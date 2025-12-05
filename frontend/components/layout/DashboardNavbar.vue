<script setup lang="ts">
import { ref } from 'vue'
import { LogOut, User, Bell, Sun, Moon, Menu, Settings } from 'lucide-vue-next'
import { useUserSession } from '#auth-utils'

const { user, clear } = useUserSession()
const isLoggingOut = ref(false)
const isDark = ref(false) // TODO: Implement theme toggle

const toggleMode = () => {
  isDark.value = !isDark.value
  // TODO: Implement theme toggle logic
}

const handleLogout = async () => {
  if (isLoggingOut.value) {
    return
  }
  
  isLoggingOut.value = true
  
  try {
    await clear()
    await navigateTo('/login')
  } catch (error) {
    console.error('Logout failed:', error)
  } finally {
    isLoggingOut.value = false
  }
}
</script>

<template>
  <nav 
    class="flex items-center justify-between h-16 border-b px-4 bg-background border-border sticky top-0 z-10" 
  >
    <div class="w-24 hidden lg:block">
      <!-- Breadcrumb can be added here later -->
    </div>
    <Button
      variant="outline"
      class="p-[6px] w-8 h-8 transition-all duration-200 block lg:hidden"
      @click="$emit('toggle-sidebar')"
    >
      <Menu class="transition-all duration-500 text-black" />
    </Button>
    <div class="flex items-center">
      <Button variant="outline" class="border-0 p-[6px] w-8 h-8">
        <Bell />
      </Button>
      <Button variant="outline" class="border-0 p-[6px] ml-2 w-8 h-8" @click="toggleMode">
        <Sun v-if="isDark" />
        <Moon v-else />
      </Button>
      <div class="border-x-[1px] border-gray-300 h-[24px] w-[1px] mx-2"></div>
      <div class="relative">
        <DropdownMenu v-slot="{ open, toggle }">
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" class="relative h-8 w-8 rounded-full" @click="toggle">
              <Avatar class="h-8 w-8">
                <AvatarFallback>{{ (user?.name || user?.email)?.charAt(0).toUpperCase() }}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent v-if="open" class="w-56" align="end" :sideOffset="4">
          <DropdownMenuLabel class="p-0 font-normal">
            <div class="flex items-center gap-2 px-1 py-1.5 text-sm">
              <Avatar class="h-8 w-8">
                <AvatarFallback>{{ (user?.name || user?.email)?.charAt(0).toUpperCase() }}</AvatarFallback>
              </Avatar>
              <div class="grid flex-1 text-left text-sm leading-tight">
                <span class="truncate font-semibold">{{ user?.name || user?.email }}</span>
                <span class="truncate text-xs text-muted-foreground">{{ user?.email }}</span>
              </div>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <User class="mr-2 h-4 w-4" />
            <span>Account</span>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings class="mr-2 h-4 w-4" />
            <span>Settings</span>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleLogout">
            <LogOut class="mr-2 h-4 w-4" />
            <span>Log out</span>
            <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
          </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  </nav>
</template>

