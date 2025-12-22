<script setup lang="ts">
const route = useRoute();

const tabs = [
  {
    label: "Test Bed",
    icon: "i-lucide-flask-conical",
    to: "/experiments/testbed",
    active: route.path === "/experiments/testbed",
  },
  {
    label: "ROI Calculator",
    icon: "i-lucide-calculator",
    to: "/experiments/roi-calculator",
    active: route.path === "/experiments/roi-calculator",
  },
];
</script>

<template>
  <UNavigationMenu
    :items="tabs"
    class="mb-6"
  />
</template>

