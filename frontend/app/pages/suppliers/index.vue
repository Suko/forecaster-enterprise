<script setup lang="ts">
definePageMeta({
  layout: "dashboard",
});

await navigateTo("/purchase-orders/suppliers", { replace: true });
</script>

<template>
  <div class="p-6">
    <p class="text-sm text-muted">Redirecting...</p>
  </div>
</template>
