<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center space-y-4">
      <h1 class="text-4xl font-bold">Forecaster Enterprise</h1>
      <p class="text-muted-foreground">Welcome to the dashboard</p>
      <div v-if="loggedIn" class="space-y-2">
        <p>Logged in as: {{ user?.email }}</p>
        <Button @click="handleLogout">Logout</Button>
      </div>
      <div v-else>
        <NuxtLink to="/login">
          <Button>Login</Button>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user, loggedIn, clear } = useUserSession()

const handleLogout = async () => {
  await clear()
  await navigateTo('/login')
}
</script>

