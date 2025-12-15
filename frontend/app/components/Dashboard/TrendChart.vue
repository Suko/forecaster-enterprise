<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <h3 class="text-lg font-semibold">{{ title }}</h3>
          <p
            v-if="subtitle"
            class="text-sm text-gray-500 dark:text-gray-400 mt-1"
            v-html="subtitle"
          />
        </div>
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
        <div
          v-else
          class="flex items-center justify-center h-64 text-gray-400"
        >
          No data available
        </div>
      </ClientOnly>
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { Line } from "vue-chartjs";
import type { ChartData, ChartOptions } from "chart.js";

interface Props {
  title: string;
  data: Array<{ date: string; value: number }>;
  label?: string;
  color?: string;
  forecastData?: Array<{ date: string; value: number; lower?: number; upper?: number }>;
  showForecast?: boolean;
  subtitle?: string;
}

const props = withDefaults(defineProps<Props>(), {
  label: "Value",
  color: "rgb(59, 130, 246)",
  showForecast: false,
});

const chartRef = ref<InstanceType<typeof Line>>();

const chartData = computed<ChartData<"line">>(() => {
  if (!props.data || props.data.length === 0) {
    return {
      labels: [],
      datasets: [],
    };
  }

  const allDates = [...props.data.map((d) => d.date)];
  if (props.forecastData) {
    props.forecastData.forEach((d) => {
      if (!allDates.includes(d.date)) {
        allDates.push(d.date);
      }
    });
  }
  allDates.sort();

  const datasets: any[] = [
    {
      label: props.label,
      data: props.data.map((d) => ({ x: d.date, y: d.value })),
      borderColor: props.color,
      backgroundColor: props.color.replace("rgb", "rgba").replace(")", ", 0.1)"),
      tension: 0.4,
      fill: true,
      pointRadius: 2,
    },
  ];

  // Add forecast data if available
  if (props.showForecast && props.forecastData && props.forecastData.length > 0) {
    // Confidence interval (shaded area)
    if (props.forecastData[0].lower !== undefined && props.forecastData[0].upper !== undefined) {
      datasets.push({
        label: "Confidence Interval",
        data: props.forecastData.map((d) => ({ x: d.date, y: d.upper })),
        borderColor: "transparent",
        backgroundColor: props.color.replace("rgb", "rgba").replace(")", ", 0.2)"),
        fill: "+1",
        tension: 0.4,
        pointRadius: 0,
      });
      
      datasets.push({
        label: "",
        data: props.forecastData.map((d) => ({ x: d.date, y: d.lower })),
        borderColor: "transparent",
        backgroundColor: props.color.replace("rgb", "rgba").replace(")", ", 0.2)"),
        fill: false,
        tension: 0.4,
        pointRadius: 0,
      });
    }

    // Forecast line (dashed)
    datasets.push({
      label: "Forecast",
      data: props.forecastData.map((d) => ({ x: d.date, y: d.value })),
      borderColor: props.color.replace("rgb", "rgba").replace(")", ", 0.8)"),
      backgroundColor: "transparent",
      borderDash: [5, 5],
      tension: 0.4,
      pointRadius: 2,
    });
  }

  return {
    labels: allDates,
    datasets,
  };
});

const chartOptions = computed<ChartOptions<"line">>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: "top",
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
        mode: "x",
        drag: {
          enabled: true,
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          borderColor: "rgba(59, 130, 246, 0.3)",
          borderWidth: 1,
        },
      },
      pan: {
        enabled: true,
        mode: "x",
        modifierKey: "ctrl",
      },
    },
  },
  scales: {
    x: {
      type: "category",
      title: {
        display: true,
        text: "Date",
      },
      ticks: {
        maxRotation: 45,
        minRotation: 45,
        callback: function(value: any, index: number) {
          // Show every 10th label to avoid crowding
          if (index % 10 === 0 || index === this.chart.data.labels.length - 1) {
            const label = this.chart.data.labels[index] as string;
            return label ? new Date(label).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
          }
          return '';
        },
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
    mode: "nearest",
    axis: "x",
    intersect: false,
  },
}));

const showResetZoom = ref(false);

const resetZoom = () => {
  if (chartRef.value?.chart) {
    chartRef.value.chart.resetZoom();
    showResetZoom.value = false;
  }
};

// Watch for zoom changes
onMounted(() => {
  if (chartRef.value?.chart) {
    chartRef.value.chart.canvas.addEventListener("wheel", () => {
      showResetZoom.value = true;
    });
  }
});
</script>
