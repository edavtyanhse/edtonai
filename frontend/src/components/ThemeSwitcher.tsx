import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components'

export default function ThemeSwitcher() {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const isDark = mounted && resolvedTheme === 'dark'

  const toggle = () => {
    setTheme(isDark ? 'light' : 'dark')
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggle}
      className="w-9 px-0"
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      <span className="relative inline-flex h-4 w-4 items-center justify-center">
        <Sun
          className={`absolute h-4 w-4 transition-all duration-300 ${
            mounted && !isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'
          }`}
        />
        <Moon
          className={`absolute h-4 w-4 transition-all duration-300 ${
            isDark ? 'rotate-0 scale-100 opacity-100' : 'rotate-90 scale-0 opacity-0'
          }`}
        />
      </span>
    </Button>
  )
}
