<template>
  <div class="flex min-h-screen flex-col">
    <main class="flex-1">
      <NuxtPage />
    </main>
    <footer class="border-t">
      <div class="mx-auto flex h-16 max-w-6xl items-center justify-end px-4">
        <ThemeModeSwitcher />
      </div>
    </footer>
  </div>
</template>
