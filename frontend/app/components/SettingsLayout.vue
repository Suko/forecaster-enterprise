<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Settings</h1>
    
    <UTabs
      :items="tabs"
      :default-value="activeTab"
      variant="link"
      @update:model-value="handleTabChange"
    >
      <template #list-trailing>
        <UButton
          to="https://ui.nuxt.com/docs/getting-started/installation/nuxt"
          external
          variant="ghost"
          icon="i-lucide-external-link"
          trailing
          class="ml-auto"
        >
          Documentation
        </UButton>
      </template>
      
      <template #general>
        <slot name="general">
          <GeneralSection />
        </slot>
      </template>
      
      <template #members>
        <slot name="members">
          <MembersSection />
        </slot>
      </template>
      
      <template #notifications>
        <slot name="notifications">
          <div class="py-8">
            <p class="text-gray-500 dark:text-gray-400">Notifications settings coming soon...</p>
          </div>
        </slot>
      </template>
      
      <template #security>
        <slot name="security">
          <div class="py-8">
            <p class="text-gray-500 dark:text-gray-400">Security settings coming soon...</p>
          </div>
        </slot>
      </template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
import type { TabsItem } from '@nuxt/ui'

const route = useRoute()
const router = useRouter()

const tabs: TabsItem[] = [
  {
    label: 'General',
    value: 'general',
    slot: 'general'
  },
  {
    label: 'Members',
    value: 'members',
    slot: 'members'
  },
  {
    label: 'Notifications',
    value: 'notifications',
    slot: 'notifications'
  },
  {
    label: 'Security',
    value: 'security',
    slot: 'security'
  }
]

const activeTab = computed(() => {
  if (route.path === '/settings' || route.path === '/settings/') {
    return 'general'
  }
  if (route.path === '/settings/members') {
    return 'members'
  }
  if (route.path === '/settings/notifications') {
    return 'notifications'
  }
  if (route.path === '/settings/security') {
    return 'security'
  }
  return 'general'
})

const handleTabChange = (value: string | number) => {
  const tabValue = String(value)
  if (tabValue === 'general') {
    router.push('/settings')
  } else {
    router.push(`/settings/${tabValue}`)
  }
}
</script>

