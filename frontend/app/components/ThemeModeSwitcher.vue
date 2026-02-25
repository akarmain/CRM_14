<script setup lang="ts">
import { computed } from 'vue'
import { Check, Moon, Sun, Monitor } from 'lucide-vue-next'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type ThemeMode = 'light' | 'dark' | 'system'

type ThemeOption = {
  value: ThemeMode
  label: string
}

const options: ThemeOption[] = [
  { value: 'light', label: 'Светлая' },
  { value: 'dark', label: 'Темная' },
  { value: 'system', label: 'Автоматически' },
]

const { mode, setThemeMode } = useThemeMode()

const currentLabel = computed(() => {
  return options.find(option => option.value === mode.value)?.label ?? 'Автоматически'
})

function selectTheme(value: ThemeMode) {
  setThemeMode(value)
}

function getIcon(value: ThemeMode) {
  if (value === 'light') return Sun
  if (value === 'dark') return Moon
  return Monitor
}
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="outline" size="sm">
        Тема: {{ currentLabel }}
      </Button>
    </DropdownMenuTrigger>

    <DropdownMenuContent class="w-52" align="end">
      <DropdownMenuLabel>Тема интерфейса</DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuGroup>
        <DropdownMenuItem
          v-for="option in options"
          :key="option.value"
          @click="selectTheme(option.value)"
        >
          <span class="flex w-full items-center justify-between gap-2">
            <span class="flex items-center gap-2">
              <component :is="getIcon(option.value)" class="size-4" />
              <span>{{ option.label }}</span>
            </span>
            <Check
              v-if="mode === option.value"
              class="size-4"
              aria-hidden="true"
            />
          </span>
        </DropdownMenuItem>
      </DropdownMenuGroup>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
