import { motion } from 'framer-motion'
import { MessageSquare, FileText, Mic, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

const features = [
  {
    title: 'AI Chat',
    description: 'Chat with advanced AI models',
    icon: MessageSquare,
    path: '/chat',
    gradient: 'from-blue-500 to-blue-600',
    bgGradient: 'from-blue-500/10 to-blue-600/10'
  },
  {
    title: 'PDF Chat',
    description: 'Chat with your PDF documents',
    icon: FileText,
    path: '/pdf',
    gradient: 'from-purple-500 to-purple-600',
    bgGradient: 'from-purple-500/10 to-purple-600/10'
  },
  {
    title: 'Voice Assistant',
    description: 'Speak to AI naturally',
    icon: Mic,
    path: '/voice',
    gradient: 'from-orange-500 to-orange-600',
    bgGradient: 'from-orange-500/10 to-orange-600/10'
  }
]

export default function Dashboard() {
  return (
    <div className="max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-12"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">
              Welcome to Multimax AI
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              Your AI-powered workspace
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {features.map((feature, i) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -4 }}
          >
            <Link to={feature.path}>
              <div className="h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer">
                <div className={cn(
                  "w-14 h-14 bg-gradient-to-br rounded-xl flex items-center justify-center mb-4",
                  feature.bgGradient
                )}>
                  <feature.icon className="w-7 h-7 text-slate-700 dark:text-slate-200" />
                </div>
                <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-500 dark:text-slate-400">
                  {feature.description}
                </p>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6"
        >
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">
            Quick Start
          </h2>
          <div className="space-y-4">
            {[
              'Create an AI Chat conversation',
              'Upload a PDF document',
              'Try the voice assistant'
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-8 h-8 bg-green-500/10 text-green-600 dark:text-green-400 rounded-full flex items-center justify-center font-semibold">
                  {i + 1}
                </div>
                <p className="text-slate-600 dark:text-slate-300">{step}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20 rounded-2xl p-6"
        >
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-2">
            Tip of the Day
          </h3>
          <p className="text-slate-600 dark:text-slate-300">
            You can use Ollama models locally for completely private AI conversations!
          </p>
        </motion.div>
      </div>
    </div>
  )
}

function cn(...args: any[]) {
  return args.filter(Boolean).join(' ')
}
