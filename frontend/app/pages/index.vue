<script setup lang="ts">
import { onMounted, ref, computed } from "vue"

const avatarUrl = ref("")

const tg = computed(() => {
  if (process.server) return null
  return window.Telegram?.WebApp ?? null
})

function onMainClick() {
  if (!tg.value) return

  tg.value.showPopup({
    title: "Аватар",
    message: "Вставь ссылку на изображение.\nПоле ввода откроется после OK.",
    buttons: [{ type: "ok", text: "ОК" }],
  })

  // после закрытия popup просто показываем input
  setTimeout(() => {
    const el = document.getElementById("avatar-input")
    el?.focus()
  }, 300)
}

onMounted(() => {
  tg.value?.ready()
  tg.value?.expand()

  if (tg.value) {
    tg.value.MainButton.setText("Указать аватар")
    tg.value.MainButton.show()
    tg.value.MainButton.onClick(onMainClick)
  }
})
</script>

<template>
  <div class="p-4 space-y-2">
    <input
      id="avatar-input"
      v-model="avatarUrl"
      type="url"
      placeholder="https://example.com/avatar.jpg"
      class="w-full px-3 py-2 rounded border"
    />

    <p class="text-xs opacity-70">
      Ссылка на аватар:
      <br />
      {{ avatarUrl || "не указана" }}
    </p>
  </div>
</template>
