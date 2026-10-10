import React from 'react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  withText?: boolean
  className?: string
}

export default function Logo({ size = 'md', withText = true, className = '' }: LogoProps) {
  const iconSizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
    xl: 'w-20 h-20',
  }

  const textSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-3xl',
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className={`relative ${iconSizes[size]} flex-shrink-0`}>
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full drop-shadow-[0_0_12px_rgba(16,185,129,0.35)]"
        >
          <defs>
            <linearGradient id="multiGradEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#34D399" />
              <stop offset="50%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#06B6D4" />
            </linearGradient>
            <linearGradient id="multiGradCyan" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#06B6D4" />
              <stop offset="100%" stopColor="#3B82F6" />
            </linearGradient>
            <radialGradient id="multiGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background ambient container */}
          <rect width="100" height="100" rx="24" fill="#0B132B" />
          <rect width="98" height="98" x="1" y="1" rx="23" stroke="url(#multiGradEmerald)" strokeWidth="1.5" strokeOpacity="0.4" />
          <circle cx="50" cy="50" r="38" fill="url(#multiGlow)" />

          {/* Geometric AI 'M' Emblem */}
          <path
            d="M20 72 V36 L38 24 L50 32 L38 42 L20 36"
            stroke="url(#multiGradEmerald)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M80 72 V36 L62 24 L50 32 L62 42 L80 36"
            stroke="url(#multiGradCyan)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M38 42 L50 56 L62 42"
            stroke="url(#multiGradEmerald)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M50 56 V76"
            stroke="url(#multiGradCyan)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Central isometric AI core cube */}
          <polygon points="50,44 58,49 50,54 42,49" fill="#10B981" fillOpacity="0.85" />
          <polygon points="42,49 50,54 50,64 42,59" fill="#059669" fillOpacity="0.9" />
          <polygon points="58,49 50,54 50,64 58,59" fill="#06B6D4" fillOpacity="0.9" />

          {/* Glowing node dots */}
          <circle cx="20" cy="72" r="3.5" fill="#34D399" />
          <circle cx="80" cy="72" r="3.5" fill="#06B6D4" />
          <circle cx="50" cy="76" r="3" fill="#38BDF8" />
          <circle cx="38" cy="24" r="3" fill="#34D399" />
          <circle cx="62" cy="24" r="3" fill="#06B6D4" />
        </svg>
      </div>

      {withText && (
        <div className="flex flex-col">
          <div className={`font-black tracking-wider leading-none text-slate-900 dark:text-white ${textSizes[size]}`}>
            MULTIMAX
          </div>
          <span className="text-[10px] font-semibold tracking-widest text-emerald-500 uppercase mt-0.5">
            AI HUB
          </span>
        </div>
      )}
    </div>
  )
}
