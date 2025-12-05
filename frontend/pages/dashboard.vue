<template>
  <div>
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
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'dashboard',
})

const { user } = useUserSession()
</script>

