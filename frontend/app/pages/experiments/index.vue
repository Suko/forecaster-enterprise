<script setup lang="ts">
definePageMeta({
  layout: "dashboard",
});

// Redirect to testbed by default
await navigateTo("/experiments/testbed", { replace: true });
</script>

<template>
  <div class="p-6">
    <p class="text-sm text-muted">Redirecting...</p>
  </div>
</template>

