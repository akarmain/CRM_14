export default defineNuxtPlugin(() => {
  const { initThemeMode } = useThemeMode()
  initThemeMode()
})
