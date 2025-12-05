<template>
  <div class="min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-4">Dashboard</h1>
      <Card>
        <CardHeader>
          <CardTitle>Welcome, {{ user?.name || user?.email }}</CardTitle>
          <CardDescription>You are logged in as {{ user?.role }}</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <p><strong>Email:</strong> {{ user?.email }}</p>
            <p><strong>Role:</strong> {{ user?.role }}</p>
            <p><strong>Active:</strong> {{ user?.is_active ? 'Yes' : 'No' }}</p>
          </div>
          <div class="mt-4">
            <Button @click="handleLogout" variant="destructive">Logout</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
})

const { user, clear } = useUserSession()

const handleLogout = async () => {
  await clear()
  await navigateTo('/login')
}
</script>

