<template>
  <div
    class="min-h-screen flex items-center justify-center bg-linear-to-br from-gray-900 to-gray-800 p-5"
  >
    <UCard class="max-w-md w-full text-center">
      <template #header>
        <div class="flex flex-col items-center gap-4">
          <div
            class="w-20 h-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center"
          >
            <UIcon
              name="i-heroicons-exclamation-triangle"
              class="w-12 h-12 text-red-500"
            />
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            License Required
          </h1>
        </div>
      </template>

      <p class="text-gray-500 dark:text-gray-400 mb-6">
        The application license has expired or is invalid. Please contact your
        administrator to renew the license.
      </p>

      <UAlert
        icon="i-heroicons-information-circle"
        color="neutral"
        variant="subtle"
        title="If you believe this is an error, please check:"
        class="text-left mb-6"
      >
        <template #description>
          <ul class="list-disc list-inside mt-2 space-y-1 text-sm">
            <li>Your license key is valid and not expired</li>
            <li>Your machine ID is registered with your license</li>
            <li>Network connectivity to the license server</li>
          </ul>
        </template>
      </UAlert>

      <template #footer>
        <div class="flex flex-col items-center gap-4">
          <UButton
            :loading="checking"
            :disabled="checking"
            icon="i-heroicons-arrow-path"
            size="lg"
            @click="retry"
          >
            {{ checking ? "Checking..." : "Retry Connection" }}
          </UButton>

          <p class="text-sm text-gray-400">
            Contact support:
            <ULink
              to="mailto:support@example.com"
              class="text-primary-500 hover:text-primary-600"
            >
              support@example.com
            </ULink>
          </p>
        </div>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
// No auth required for this page
definePageMeta({
  layout: false,
  auth: false,
});

const checking = ref(false);
const config = useRuntimeConfig();

const retry = async () => {
  checking.value = true;
  try {
    await $fetch(`${config.public.apiBaseUrl}/health`, {
      timeout: 5000,
    });
    // If we get here, backend is back up - reload the page
    window.location.reload();
  } catch (error) {
    // Still down
    console.log("Backend still unavailable");
  } finally {
    checking.value = false;
  }
};
</script>
