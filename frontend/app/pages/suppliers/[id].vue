<script setup lang="ts">
definePageMeta({
  layout: "dashboard",
});

const route = useRoute();
const id = computed(() => String(route.params.id || ""));

await navigateTo(`/purchase-orders/suppliers/${encodeURIComponent(id.value)}`, { replace: true });
</script>

<template>
  <div class="p-6">
    <p class="text-sm text-muted">Redirecting...</p>
  </div>
</template>
