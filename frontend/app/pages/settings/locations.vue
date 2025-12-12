<template>
  <SettingsLayout>
    <template #locations>
      <LocationsSection />
    </template>
  </SettingsLayout>
</template>

<script setup lang="ts">
import SettingsLayout from "~/components/SettingsLayout.vue";
import LocationsSection from "~/components/LocationsSection.vue";

definePageMeta({
  layout: "dashboard",
});
</script>

