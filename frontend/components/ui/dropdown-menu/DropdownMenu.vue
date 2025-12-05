<script setup lang="ts">
import { ref, provide } from 'vue'

const open = ref(false)

const toggle = () => {
  open.value = !open.value
}

const close = () => {
  open.value = false
}

provide('dropdownMenu', { open, toggle, close })
</script>

<template>
  <div class="relative inline-block text-left">
    <slot />
  </div>
</template>

