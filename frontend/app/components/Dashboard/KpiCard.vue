<template>
  <UCard :class="['hover:scale-105 transition-transform duration-200', $attrs.class]">
    <div class="flex items-center gap-3">
      <div :class="`h-12 w-12 rounded-lg ${bgColor} flex items-center justify-center transition-all duration-300 hover:scale-110`">
        <UIcon
          :name="icon"
          :class="`w-6 h-6 ${iconColor}`"
        />
      </div>
      <div class="flex-1">
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ label }}</p>
        <p :class="`text-2xl font-bold ${valueColor} transition-all duration-500`">
          <span :key="displayValue" class="inline-block animate-count-up">{{ displayValue }}</span>
        </p>
        <p
          v-if="subtitle"
          class="text-xs text-gray-400 mt-1"
        >
          {{ subtitle }}
        </p>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
interface Props {
  label: string;
  value: string | number | undefined;
  icon: string;
  bgColor?: string;
  iconColor?: string;
  valueColor?: string;
  subtitle?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  bgColor: "bg-blue-100 dark:bg-blue-900",
  iconColor: "text-blue-500",
  valueColor: "text-blue-600 dark:text-blue-400",
});

const formattedValue = computed(() => {
  if (props.value === undefined || props.value === null) {
    return "0";
  }
  if (typeof props.value === "number") {
    return props.value.toLocaleString();
  }
  if (typeof props.value === "string" && props.value.startsWith("€")) {
    return props.value;
  }
  return props.value;
});

// Animated count-up value
const displayValue = ref("0");
const targetValue = computed(() => formattedValue.value);

onMounted(() => {
  // Animate from 0 to target value
  const startValue = 0;
  const endValue = typeof props.value === "number" ? props.value : parseFloat(targetValue.value.replace(/[€,]/g, "")) || 0;
  const duration = 1500; // 1.5 seconds
  const startTime = Date.now();
  
  const animate = () => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function (ease-out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = startValue + (endValue - startValue) * easeOut;
    
    if (typeof props.value === "number") {
      displayValue.value = Math.floor(current).toLocaleString();
    } else if (typeof props.value === "string" && props.value.startsWith("€")) {
      const numValue = parseFloat(props.value.replace(/[€,]/g, "")) || 0;
      displayValue.value = `€${Math.floor(numValue * easeOut).toLocaleString()}`;
    } else {
      displayValue.value = targetValue.value;
    }
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      displayValue.value = targetValue.value;
    }
  };
  
  animate();
});

watch(targetValue, () => {
  // Reset and re-animate when value changes
  displayValue.value = "0";
  const startValue = 0;
  const endValue = typeof props.value === "number" ? props.value : parseFloat(targetValue.value.replace(/[€,]/g, "")) || 0;
  const duration = 1000;
  const startTime = Date.now();
  
  const animate = () => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = startValue + (endValue - startValue) * easeOut;
    
    if (typeof props.value === "number") {
      displayValue.value = Math.floor(current).toLocaleString();
    } else if (typeof props.value === "string" && props.value.startsWith("€")) {
      const numValue = parseFloat(targetValue.value.replace(/[€,]/g, "")) || 0;
      displayValue.value = `€${Math.floor(numValue * easeOut).toLocaleString()}`;
    } else {
      displayValue.value = targetValue.value;
    }
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      displayValue.value = targetValue.value;
    }
  };
  
  animate();
});
</script>

<style scoped>
@keyframes count-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-count-up {
  animation: count-up 0.5s ease-out;
}
</style>
