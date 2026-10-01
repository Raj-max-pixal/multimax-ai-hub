import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import typescript from 'react-syntax-highlighter/dist/esm/languages/prism/typescript'
import tsx from 'react-syntax-highlighter/dist/esm/languages/prism/tsx'
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript'
import jsx from 'react-syntax-highlighter/dist/esm/languages/prism/jsx'
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python'
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json'
import bash from 'react-syntax-highlighter/dist/esm/languages/prism/bash'
import sql from 'react-syntax-highlighter/dist/esm/languages/prism/sql'
import css from 'react-syntax-highlighter/dist/esm/languages/prism/css'
import markup from 'react-syntax-highlighter/dist/esm/languages/prism/markup'
import yaml from 'react-syntax-highlighter/dist/esm/languages/prism/yaml'
import diff from 'react-syntax-highlighter/dist/esm/languages/prism/diff'
import { Copy } from 'lucide-react'

const languages = { typescript, tsx, javascript, jsx, python, json, bash, sql, css, markup, yaml, diff }
Object.entries(languages).forEach(([name, grammar]) => SyntaxHighlighter.registerLanguage(name, grammar))
const aliases: Record<string, string> = { ts: 'typescript', js: 'javascript', html: 'markup', xml: 'markup', sh: 'bash', shell: 'bash', yml: 'yaml' }

interface CodeBlockProps {
  language: string
  code: string
  onCopy: (code: string) => void | Promise<void>
}

export default function CodeBlock({ language, code, onCopy }: CodeBlockProps) {
  const resolvedLanguage = aliases[language.toLowerCase()] || language.toLowerCase()
  const supportsHighlighting = Object.prototype.hasOwnProperty.call(languages, resolvedLanguage)
  return (
    <div className="my-3 overflow-hidden rounded-xl border border-slate-700 bg-[#1e1e1e]">
      <div className="flex items-center justify-between border-b border-white/10 bg-slate-900 px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-300">{language}</span>
        <button
          type="button"
          onClick={() => void onCopy(code)}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-slate-300 transition hover:bg-white/10 hover:text-white"
          aria-label={`Copy ${language} code`}
        >
          <Copy className="h-3.5 w-3.5" />
          Copy
        </button>
      </div>
      {supportsHighlighting ? <SyntaxHighlighter
          style={vscDarkPlus}
          language={resolvedLanguage}
          PreTag="div"
          customStyle={{ margin: 0, padding: '1rem', background: 'transparent', overflowX: 'auto' }}
        >{code}</SyntaxHighlighter>
        : <pre className="overflow-x-auto p-4 text-sm leading-6 text-slate-100"><code>{code}</code></pre>}
    </div>
  )
}
