import { useState } from 'react'
import { Copy, Download, Image, Sparkles } from 'lucide-react'
import { generateImage } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

type ImageItem = { id: string; prompt: string; style: string; size: string; image_url: string; note?: string }

export default function AIImage() {
  const [prompt, setPrompt] = useState('A futuristic green AI operating system dashboard, glassmorphism, elegant, high contrast')
  const [style, setStyle] = useState('illustration')
  const [size, setSize] = useState('square')
  const [loading, setLoading] = useState(false)
  const [images, setImages] = useState<ImageItem[]>(() => { try { return JSON.parse(localStorage.getItem('multimax_images') || '[]') } catch { return [] } })
  const { addToast } = useToast()

  const saveImages = (next: ImageItem[]) => { setImages(next); localStorage.setItem('multimax_images', JSON.stringify(next)) }

  const generate = async () => {
    if (!prompt.trim()) return addToast('Enter an image prompt first', 'error')
    setLoading(true)
    try {
      const data = await generateImage({ prompt, style, size })
      saveImages([{ id: Date.now().toString(), ...data }, ...images].slice(0, 30))
    } catch (e: any) {
      addToast(e.message || 'Image generation failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const download = (item: ImageItem) => {
    const a = document.createElement('a')
    a.href = item.image_url
    a.download = `multimax-image-${item.id}.svg`
    a.click()
  }

  const copyPrompt = async (text: string) => { await navigator.clipboard.writeText(text); addToast('Prompt copied', 'success') }

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Image Studio</h1><p className="text-slate-500 dark:text-slate-400">Phase 8: prompt-to-image workspace, logos, posters, thumbnails, and local gallery.</p></div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Sparkles className="w-5 h-5 text-green-500" /> Generate Image</div>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={8} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <select value={style} onChange={(e) => setStyle(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['illustration','realistic','logo','poster','thumbnail'].map(x => <option key={x}>{x}</option>)}</select>
          <select value={size} onChange={(e) => setSize(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['square','wide','portrait'].map(x => <option key={x}>{x}</option>)}</select>
          <button onClick={generate} disabled={loading} className="w-full rounded-xl bg-green-500 px-5 py-3 font-semibold text-white hover:bg-green-600 disabled:opacity-60">{loading ? 'Generating...' : 'Generate Image'}</button>
          <p className="text-xs text-slate-500">Current local mode generates beautiful SVG concept images. Later you can connect ComfyUI/Stable Diffusion for photoreal images.</p>
        </div>
        <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Gallery</h2>
          {images.length === 0 ? <div className="h-80 flex items-center justify-center text-slate-500"><div className="text-center"><Image className="w-16 h-16 mx-auto mb-3" />Generated images appear here.</div></div> : <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{images.map(item => <div key={item.id} className="rounded-2xl bg-slate-100 dark:bg-slate-800 p-3"><img src={item.image_url} alt={item.prompt} className="w-full rounded-xl border border-slate-200 dark:border-slate-700" /><p className="mt-3 text-sm text-slate-700 dark:text-slate-200 line-clamp-2">{item.prompt}</p><div className="mt-3 flex gap-2"><button onClick={() => download(item)} className="rounded-lg bg-white dark:bg-slate-900 px-3 py-2 text-slate-600 dark:text-slate-300"><Download className="w-4 h-4" /></button><button onClick={() => copyPrompt(item.prompt)} className="rounded-lg bg-white dark:bg-slate-900 px-3 py-2 text-slate-600 dark:text-slate-300"><Copy className="w-4 h-4" /></button></div></div>)}</div>}
        </div>
      </div>
    </div>
  )
}
