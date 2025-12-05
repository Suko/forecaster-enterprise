<template>
  <div
    :class="cn(
      'relative w-full rounded-lg border p-4',
      variant === 'destructive' ? 'border-destructive/50 text-destructive dark:border-destructive' : '',
      $attrs.class
    )"
    v-bind="$attrs"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'default' | 'destructive'
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
})
</script>

