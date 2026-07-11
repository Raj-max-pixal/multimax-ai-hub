import { useState } from 'react'
import { Moon, Sun, Bell } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export default function Settings() {
  const { theme, toggleTheme } = useTheme()
  const [notifications, setNotifications] = useState(true)

  const settingsSections = [
    {
      title: 'Appearance',
      items: [
        {
          label: 'Dark Mode',
          description: 'Use dark theme',
          icon: theme === 'dark' ? Moon : Sun,
          type: 'toggle',
          value: theme === 'dark',
          onChange: toggleTheme
        }
      ]
    },
    {
      title: 'Notifications',
      items: [
        {
          label: 'Enable Notifications',
          description: 'Receive alerts and updates',
          icon: Bell,
          type: 'toggle',
          value: notifications,
          onChange: () => setNotifications(!notifications)
        }
      ]
    }
  ]

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-2">
          Settings
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Manage your preferences and account settings
        </p>
      </div>

      <div className="space-y-8">
        {settingsSections.map((section) => (
          <div
            key={section.title}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">
              {section.title}
            </h2>
            <div className="space-y-4">
              {section.items.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center">
                      <item.icon className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 dark:text-slate-100">
                        {item.label}
                      </p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  {item.type === 'toggle' && (
                    <button
                      onClick={item.onChange}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        item.value
                          ? 'bg-gradient-to-r from-green-500 to-green-600'
                          : 'bg-slate-300 dark:bg-slate-700'
                      }`}
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full transition-transform ${
                          item.value ? 'translate-x-6' : 'translate-x-0.5'
                        }`}
                      />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
