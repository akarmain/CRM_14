import { onBeforeUnmount, onMounted, ref } from "vue"

type ClickHandler = () => void

type TelegramMainButton = {
  text?: string
  isVisible: boolean
  show: () => void
  hide: () => void
  setText: (text: string) => void
  onClick: (cb: ClickHandler) => void
  offClick: (cb: ClickHandler) => void
}

type TelegramSecondaryButton = TelegramMainButton

type TelegramWebApp = {
  ready: () => void
  expand: () => void
  MainButton: TelegramMainButton
  SecondaryButton?: TelegramSecondaryButton
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp }
  }
}

export function useTelegram() {
  const webApp = ref<TelegramWebApp | null>(null)

  const init = () => {
    if (typeof window === "undefined") return
    const app = window.Telegram?.WebApp
    if (!app) return
    app.ready()
    app.expand()
    webApp.value = app
  }

  const setMainButton = (text: string, onClick: ClickHandler) => {
    const btn = webApp.value?.MainButton
    if (!btn) return
    btn.setText(text)
    btn.show()
    btn.onClick(onClick)
    return () => btn.offClick(onClick)
  }

  const setSecondaryButton = (text: string, onClick: ClickHandler) => {
    const btn = webApp.value?.SecondaryButton
    if (!btn) return
    btn.setText(text)
    btn.show()
    btn.onClick(onClick)
    return () => btn.offClick(onClick)
  }

  const hideButtons = () => {
    webApp.value?.MainButton?.hide()
    webApp.value?.SecondaryButton?.hide()
  }

  onMounted(init)
  onBeforeUnmount(hideButtons)

  return {
    webApp,
    init,
    setMainButton,
    setSecondaryButton,
    hideButtons,
  }
}
