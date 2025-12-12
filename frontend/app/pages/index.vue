<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <UCard class="max-w-md w-full mx-4">
      <template #header>
        <h1 class="text-2xl font-bold">Forecaster Enterprise</h1>
      </template>

      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Welcome to Forecaster Enterprise - AI-powered demand forecasting for inventory
          optimization.
        </p>

        <div class="flex gap-3">
          <UButton
            v-if="!loggedIn"
            to="/login"
            color="primary"
            size="lg"
            class="flex-1"
          >
            Sign In
          </UButton>
          <UButton
            v-else
            to="/dashboard"
            color="primary"
            size="lg"
            class="flex-1"
          >
            Go to Dashboard
          </UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false,
  auth: false,
});

const { loggedIn } = useUserSession();
</script>
