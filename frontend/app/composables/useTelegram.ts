// composables/useTelegram.ts
export const useTelegram = () => {
  if (process.server) return null
  return window.Telegram?.WebApp ?? null
}
