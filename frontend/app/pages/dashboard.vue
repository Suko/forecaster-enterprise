<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold mb-6 text-gray-900">
      Dashboard
    </h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <UCard>
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
            <div class="h-3 w-3 rounded-full bg-blue-500"></div>
          </div>
          <div>
            <p class="text-sm text-gray-500">Total Inventory</p>
            <p class="text-2xl font-bold text-blue-600">€0</p>
          </div>
        </div>
      </UCard>
      
      <UCard>
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
            <div class="h-3 w-3 rounded-full bg-primary-500"></div>
          </div>
          <div>
            <p class="text-sm text-gray-500">Total SKUs</p>
            <p class="text-2xl font-bold text-primary-600">0</p>
          </div>
        </div>
      </UCard>
      
      <UCard>
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
            <div class="h-3 w-3 rounded-full bg-red-500"></div>
          </div>
          <div>
            <p class="text-sm text-gray-500">Understocked</p>
            <p class="text-2xl font-bold text-red-600">0</p>
          </div>
        </div>
      </UCard>
      
      <UCard>
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
            <div class="h-3 w-3 rounded-full bg-green-500"></div>
          </div>
          <div>
            <p class="text-sm text-gray-500">Overstocked</p>
            <p class="text-2xl font-bold text-green-600">0</p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user, fetch } = useUserSession()

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

// Fetch latest user info on mount
onMounted(async () => {
  try {
    await fetch()
    // Optionally refresh user info from backend
    // await $fetch('/api/me')
  } catch (error) {
    // Error handled silently - user session will be validated on next request
  }
})
</script>
