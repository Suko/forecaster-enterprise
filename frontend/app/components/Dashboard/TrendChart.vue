<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">{{ title }}</h3>
        <UButton
          v-if="showResetZoom"
          icon="i-lucide-zoom-out"
          variant="ghost"
          size="xs"
          @click="resetZoom"
        >
          Reset Zoom
        </UButton>
      </div>
    </template>
    <div class="p-4">
      <ClientOnly>
        <Line
          v-if="chartData"
          :data="chartData"
          :options="chartOptions"
          ref="chartRef"
        />
        <div v-else class="flex items-center justify-center h-64 text-gray-400">
          No data available
        </div>
      </ClientOnly>
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import type { ChartData, ChartOptions } from 'chart.js'

interface Props {
  title: string
  data: Array<{ date: string; value: number }>
  label?: string
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Value',
  color: 'rgb(59, 130, 246)',
})

const chartRef = ref<InstanceType<typeof Line>>()

const chartData = computed<ChartData<'line'>>(() => {
  if (!props.data || props.data.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: props.data.map((d) => d.date),
    datasets: [
      {
        label: props.label,
        data: props.data.map((d) => d.value),
        borderColor: props.color,
        backgroundColor: props.color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        tension: 0.4,
        fill: true,
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
    },
    zoom: {
      zoom: {
        wheel: {
          enabled: true,
          speed: 0.1,
        },
        pinch: {
          enabled: true,
        },
        mode: 'x',
        drag: {
          enabled: true,
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderColor: 'rgba(59, 130, 246, 0.3)',
          borderWidth: 1,
        },
      },
      pan: {
        enabled: true,
        mode: 'x',
        modifierKey: 'ctrl',
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'day',
        displayFormats: {
          day: 'MMM dd',
        },
      },
      title: {
        display: true,
        text: 'Date',
      },
    },
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: props.label,
      },
    },
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false,
  },
}))

const showResetZoom = ref(false)

const resetZoom = () => {
  if (chartRef.value?.chart) {
    chartRef.value.chart.resetZoom()
    showResetZoom.value = false
  }
}

// Watch for zoom changes
onMounted(() => {
  if (chartRef.value?.chart) {
    chartRef.value.chart.canvas.addEventListener('wheel', () => {
      showResetZoom.value = true
    })
  }
})
</script>
