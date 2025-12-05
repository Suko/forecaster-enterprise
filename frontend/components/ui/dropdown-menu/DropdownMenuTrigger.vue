<script setup lang="ts">
const props = defineProps<{
  asChild?: boolean
}>()
</script>

<template>
  <slot />
</template>

