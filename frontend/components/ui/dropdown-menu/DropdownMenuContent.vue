<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { inject, computed } from 'vue'
import { cn } from '~/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
  align?: 'start' | 'end' | 'center'
  sideOffset?: number
}>()

const dropdownMenu = inject('dropdownMenu', null)
const isOpen = computed(() => dropdownMenu?.open.value || false)
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="isOpen"
      :class="cn(
        'fixed right-4 mt-2 w-56 origin-top-right rounded-md bg-background shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50',
        props.align === 'end' ? 'right-4' : props.align === 'start' ? 'left-4' : '',
        props.class
      )"
      :style="{ marginTop: `${props.sideOffset || 4}px` }"
      @click.stop
    >
      <div class="p-1">
        <slot />
      </div>
    </div>
  </Teleport>
</template>


