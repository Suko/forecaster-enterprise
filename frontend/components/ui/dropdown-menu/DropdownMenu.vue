<script setup lang="ts">
import { ref } from 'vue'

const open = ref(false)

const toggle = () => {
  open.value = !open.value
}

defineExpose({ open, toggle })
</script>

<template>
  <div class="relative inline-block text-left">
    <slot :open="open" :toggle="toggle" />
  </div>
</template>

