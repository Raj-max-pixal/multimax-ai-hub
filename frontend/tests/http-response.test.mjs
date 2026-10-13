import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

// Run the actual TypeScript module without adding a test framework or requiring
// Node's version-specific TypeScript stripping support.
const source = await readFile(new URL('../src/lib/http-response.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } });
const { readJsonResponse } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('successful JSON is read once', async () => {
  const response = new Response('{"answer":"hello"}');
  let reads = 0;
  const original = response.text.bind(response);
  response.text = () => { reads++; return original(); };
  assert.deepEqual(await readJsonResponse(response), { answer: 'hello' });
  assert.equal(reads, 1);
});

test('plain text API failure never attempts a second body read', async () => {
  await assert.rejects(readJsonResponse(new Response('Model is unavailable', { status: 503 })), /Model is unavailable/);
});

test('JSON and validation errors preserve the useful detail', async () => {
  await assert.rejects(readJsonResponse(new Response('{"detail":"Authentication required"}', { status: 401 })), /Authentication required/);
  await assert.rejects(readJsonResponse(new Response('{"detail":[{"msg":"Invalid model"}]}', { status: 422 })), /Invalid model/);
});

test('Vercel 404 and HTML gateway errors have readable messages', async () => {
  for (const [body, status] of [['The page could not be found\nNOT_FOUND', 404], ['<!doctype html><h1>Bad gateway</h1>', 502]]) {
    await assert.rejects(readJsonResponse(new Response(body, { status })), new RegExp(`API service is unavailable \\(HTTP ${status}\\)`));
  }
});

test('empty errors still include the status', async () => {
  await assert.rejects(readJsonResponse(new Response('', { status: 500 })), /status 500/);
});

test('invalid successful payloads cannot masquerade as valid results', async () => {
  for (const body of ['<html>SPA fallback</html>', '', '{invalid']) {
    await assert.rejects(readJsonResponse(new Response(body)), /invalid response/);
  }
  assert.equal(await readJsonResponse(new Response(null, { status: 204 })), null);
  assert.equal(await readJsonResponse(new Response('null')), null);
});

test('cancellation remains an AbortError', async () => {
  const response = new Response(new ReadableStream({ start(controller) {
    controller.error(new DOMException('Stopped', 'AbortError'));
  } }));
  await assert.rejects(readJsonResponse(response), { name: 'AbortError' });
});
