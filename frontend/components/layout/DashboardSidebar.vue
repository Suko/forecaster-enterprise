<script setup lang="ts">
import { ref, computed } from 'vue'
import { LayoutDashboard, Users, UserCheck, Activity, PanelLeft, MessageSquare } from 'lucide-vue-next'
import { useUserSession } from '#auth-utils'

const sidebarExpanded = ref(true)
const { user } = useUserSession()

const navigationItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    adminOnly: true
  },
  {
    title: 'Users',
    href: '/dashboard/users',
    icon: Users,
    adminOnly: true
  },
  {
    title: 'Clients',
    href: '/dashboard/clients',
    icon: UserCheck
  },
  {
    title: 'Analysis Requests',
    href: '/dashboard/analysis-requests',
    icon: Activity
  },
  {
    title: 'Messaging Center',
    href: '/dashboard/messaging-center',
    icon: MessageSquare,
    adminOnly: true
  }
]

const isAdmin = computed(() => user.value?.role === 'admin')

const handleNavigate = (path: string) => {
  navigateTo(path)
  if (typeof window !== 'undefined' && window.innerWidth < 1025) {
    toggleSidebar()
  }
}

const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value
}
</script>

<template>
  <div 
    class="flex h-full max-h-screen flex-col gap-2 border-r bg-background fixed left-0 top-0 z-40 transition-all duration-300" 
    :style="{ width: sidebarExpanded ? '280px' : '64px' }"
  >
    <div class="flex h-16 items-center border-b px-4 lg:px-6" v-if="sidebarExpanded">
      <NuxtLink to="/dashboard" class="flex items-center gap-2 font-semibold">
        <div class="h-6 w-6 bg-primary rounded-sm flex items-center justify-center">
          <span class="text-primary-foreground text-xs font-bold">F</span>
        </div>
        <span>FORECASTER</span>
      </NuxtLink>
      <Button variant="outline" size="icon" class="ml-auto h-8 w-8" @click="toggleSidebar">
        <PanelLeft class="h-4 w-4" />
        <span class="sr-only">Toggle sidebar</span>
      </Button>
    </div>
    <div class="flex h-16 items-center border-b px-2" v-else>
      <Button variant="outline" class="w-full h-10 justify-center" @click="toggleSidebar">
        <PanelLeft class="h-4 w-4" />
        <span class="sr-only">Toggle sidebar</span>
      </Button>
    </div>
    <div class="flex-1">
      <nav class="grid items-start px-2 pt-4 text-sm font-medium lg:px-4">
        <template v-for="item in navigationItems" :key="item.href">
          <NuxtLink
            v-if="!item.adminOnly || isAdmin"
            :to="item.href"
            @click.prevent="handleNavigate(item.href)"
            class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            :class="{
              'bg-muted text-primary': $route.path === item.href,
              'justify-center': !sidebarExpanded,
              'justify-start': sidebarExpanded
            }"
          >
            <component :is="item.icon" class="h-4 w-4" />
            <span v-if="sidebarExpanded">{{ item.title }}</span>
          </NuxtLink>
        </template>
      </nav>
    </div>
  </div>
</template>

