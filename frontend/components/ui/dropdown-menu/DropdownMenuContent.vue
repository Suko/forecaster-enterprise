<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '~/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
  align?: 'start' | 'end' | 'center'
  sideOffset?: number
}>()
</script>

<template>
  <div 
    :class="cn(
      'absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-background shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50',
      props.align === 'end' ? 'right-0' : props.align === 'start' ? 'left-0' : '',
      props.class
    )"
    :style="{ marginTop: `${props.sideOffset || 4}px` }"
  >
    <div class="p-1">
      <slot />
    </div>
  </div>
</template>

