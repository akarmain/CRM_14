<script setup lang="ts">
import type { Component } from 'vue'
import {
  BriefcaseBusiness,
  ShieldUser,
  LineChart,
  Crown
} from 'lucide-vue-next'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'

type Role = 'manager_1' | 'manager_2' | 'analyst' | 'lead'

type RoleItem = {
  value: Role
  label: string
  path: string
  logo: Component
}

const router = useRouter()

const roles: RoleItem[] = [
  { value: 'manager_1', label: 'Менеджер 1', path: '/demo/manager-1', logo: BriefcaseBusiness },
  { value: 'manager_2', label: 'Менеджер 2', path: '/demo/manager-2', logo: BriefcaseBusiness },
  { value: 'analyst', label: 'Аналитик', path: '/demo/analyst', logo: LineChart },
  { value: 'lead', label: 'Руководитель', path: '/demo/lead', logo: Crown }
]

function openRoleDemo(path: string) {
  router.push(path)
}
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="outline">Открыть DEMO</Button>
    </DropdownMenuTrigger>

    <DropdownMenuContent class="w-64">
      <DropdownMenuLabel>Выберите роль</DropdownMenuLabel>
      <DropdownMenuSeparator />

      <DropdownMenuGroup>
        <DropdownMenuItem
          v-for="role in roles"
          :key="role.value"
          @click="openRoleDemo(role.path)"
        >
          <span class="flex items-center gap-2">
            <component :is="role.logo" class="size-4" />
            <span>{{ role.label }}</span>
          </span>
        </DropdownMenuItem>
      </DropdownMenuGroup>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
