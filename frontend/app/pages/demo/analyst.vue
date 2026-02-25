<script setup lang="ts">
import { LineChart } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-xl rounded-2xl border p-8">
      <div class="mb-4 flex items-center gap-3">
        <LineChart class="size-8" />
        <h1 class="text-2xl font-semibold">DEMO: Аналитик</h1>
      </div>
      <p class="text-muted-foreground">Отдельная демо-страница роли "Аналитик".</p>
      <NuxtLink to="/" class="mt-6 inline-flex h-10 items-center justify-center rounded-md border px-4 text-sm font-medium">Назад</NuxtLink>
    </div>
  </div>
</template>
