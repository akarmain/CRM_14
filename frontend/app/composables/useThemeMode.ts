type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'theme-mode'

function isThemeMode(value: string | null): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system'
}

function getResolvedTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode !== 'system') {
    return mode
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(mode: ThemeMode) {
  const resolvedTheme = getResolvedTheme(mode)
  document.documentElement.classList.toggle('dark', resolvedTheme === 'dark')
}

export function useThemeMode() {
  const mode = useState<ThemeMode>('theme-mode', () => 'system')
  const initialized = useState<boolean>('theme-mode-initialized', () => false)

  const setThemeMode = (value: ThemeMode) => {
    mode.value = value

    if (!import.meta.client) {
      return
    }

    window.localStorage.setItem(STORAGE_KEY, value)
    applyTheme(value)
  }

  const initThemeMode = () => {
    if (!import.meta.client || initialized.value) {
      return
    }

    const savedValue = window.localStorage.getItem(STORAGE_KEY)
    mode.value = isThemeMode(savedValue) ? savedValue : 'system'
    applyTheme(mode.value)

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', () => {
      if (mode.value === 'system') {
        applyTheme(mode.value)
      }
    })

    initialized.value = true
  }

  return {
    mode,
    setThemeMode,
    initThemeMode,
  }
}
