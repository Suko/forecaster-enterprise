<template>
  <SettingsLayout>
    <template #inventory>
      <InventorySection />
    </template>
  </SettingsLayout>
</template>

<script setup lang="ts">
definePageMeta({
  layout: "dashboard",
});
</script>

