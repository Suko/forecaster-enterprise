<script setup lang="ts">
import { inject } from 'vue'

const props = defineProps<{
  asChild?: boolean
}>()

const dropdownMenu = inject('dropdownMenu', null)

const handleClick = () => {
  if (dropdownMenu) {
    dropdownMenu.toggle()
  }
}
</script>

<template>
  <div @click="handleClick">
    <slot />
  </div>
</template>


