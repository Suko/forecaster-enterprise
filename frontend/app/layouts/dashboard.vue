<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const { user } = useUserSession()
const route = useRoute()

const mainMenuItems = computed<NavigationMenuItem[]>(() => [
  {
    label: 'Dashboard',
    icon: 'i-lucide-layout-dashboard',
    to: '/dashboard',
    active: route.path === '/dashboard'
  },
  {
    label: 'Inventory',
    icon: 'i-lucide-package',
    to: '/inventory',
    active: route.path.startsWith('/inventory')
  },
  {
    label: 'Recommendations',
    icon: 'i-lucide-lightbulb',
    to: '/recommendations',
    active: route.path.startsWith('/recommendations')
  }
])

const settingsItem = ref<NavigationMenuItem>({
  label: 'Settings',
  icon: 'i-lucide-settings',
  active: false,
  defaultOpen: false,
  children: [
    {
      label: 'Users',
      icon: 'i-lucide-users',
      to: '/settings/users',
      active: false
    }
  ]
})

watch(() => route.path, (path) => {
  settingsItem.value.active = path.startsWith('/settings')
  settingsItem.value.defaultOpen = path.startsWith('/settings')
  if (settingsItem.value.children) {
    settingsItem.value.children[0].active = path === '/settings/users'
  }
}, { immediate: true })

const otherMenuItems = computed<NavigationMenuItem[]>(() => [settingsItem.value])

const { clear: clearSession } = useUserSession()

const handleLogout = async () => {
  await clearSession()
  await navigateTo('/login')
}
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible resizable>
      <template #header="{ collapsed }">
        <div v-if="!collapsed" class="flex items-center gap-2">
          <h1 class="text-xl font-bold text-primary">Forecast Enterprise</h1>
        </div>
        <UIcon v-else name="i-lucide-layout-dashboard" class="size-5 text-primary mx-auto" />
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :collapsed="collapsed"
          :items="[mainMenuItems, otherMenuItems]"
          orientation="vertical"
          type="multiple"
        />
      </template>

      <template #footer="{ collapsed }">
        <UButton
          :avatar="{
            src: undefined
          }"
          :label="collapsed ? undefined : (user?.email || 'User')"
          color="neutral"
          variant="ghost"
          class="w-full"
          :block="collapsed"
          @click="handleLogout"
        >
          <template #trailing>
            <UIcon name="i-lucide-log-out" class="size-4" />
          </template>
        </UButton>
      </template>
    </UDashboardSidebar>

    <UDashboardPanel>
      <template #header>
        <UDashboardNavbar title="Dashboard">
          <template #trailing>
            <span class="text-sm text-muted">{{ user?.email || 'Guest' }}</span>
          </template>
        </UDashboardNavbar>
      </template>

      <template #body>
        <slot />
      </template>
    </UDashboardPanel>
  </UDashboardGroup>
</template>
