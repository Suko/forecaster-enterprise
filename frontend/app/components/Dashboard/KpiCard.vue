<template>
  <UCard>
    <div class="flex items-center gap-3">
      <div :class="`h-12 w-12 rounded-lg ${bgColor} flex items-center justify-center`">
        <UIcon :name="icon" :class="`w-6 h-6 ${iconColor}`" />
      </div>
      <div class="flex-1">
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ label }}</p>
        <p :class="`text-2xl font-bold ${valueColor}`">{{ formattedValue }}</p>
        <p v-if="subtitle" class="text-xs text-gray-400 mt-1">{{ subtitle }}</p>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: string | number | undefined
  icon: string
  bgColor?: string
  iconColor?: string
  valueColor?: string
  subtitle?: string
}

const props = withDefaults(defineProps<Props>(), {
  bgColor: 'bg-blue-100 dark:bg-blue-900',
  iconColor: 'text-blue-500',
  valueColor: 'text-blue-600 dark:text-blue-400',
})

const formattedValue = computed(() => {
  if (props.value === undefined || props.value === null) {
    return '0'
  }
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  if (typeof props.value === 'string' && props.value.startsWith('€')) {
    return props.value
  }
  return props.value
})
</script>
