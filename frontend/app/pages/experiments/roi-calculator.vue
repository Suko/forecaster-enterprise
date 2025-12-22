<template>
  <div class="p-6 space-y-6">
    <ExperimentsTabs />
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
          Forecasting ROI Explorer
        </h1>
        <p class="text-sm text-muted mt-1">
          <strong>How accurate are your sales forecasts?</strong>
          Better forecasts = less money tied up in wrong inventory.
        </p>
      </div>
    </div>

    <!-- Help Section -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold">❓ How do I find my current forecast accuracy?</h3>
          <UButton
            variant="ghost"
            size="xs"
            @click="showHelp = !showHelp"
          >
            {{ showHelp ? 'Hide' : 'Show' }}
          </UButton>
        </div>
      </template>
      <div
        v-if="showHelp"
        class="space-y-4 text-sm"
      >
        <div>
          <strong>Option 1: If you have historical forecast data</strong>
          <p class="mt-1 text-muted">
            Calculate MAPE from your past forecasts:
          </p>
          <ol class="list-decimal list-inside mt-2 space-y-1 text-muted">
            <li>Take your past forecasts and compare them to what actually happened</li>
            <li>For each forecast: <code class="bg-muted px-1 rounded">|Forecast - Actual| / Actual × 100</code></li>
            <li>Average all those percentages = your MAPE</li>
          </ol>
          <p class="mt-2 text-muted">
            <strong>Example:</strong><br>
            You forecasted 100 units, sold 80 → Error = |100-80|/80 = 25%<br>
            You forecasted 50 units, sold 60 → Error = |50-60|/60 = 17%<br>
            Average = (25% + 17%) / 2 = <strong>21% MAPE</strong>
          </p>
        </div>
        <div>
          <strong>Option 2: If you use a forecasting system</strong>
          <ul class="list-disc list-inside mt-1 text-muted">
            <li>Check your system's accuracy reports/metrics</li>
            <li>Look for "MAPE", "forecast error", or "accuracy" in dashboards</li>
            <li>Use the Test Bed to see MAPE for each model</li>
          </ul>
        </div>
        <div>
          <strong>Option 3: Estimate based on typical values</strong>
          <ul class="list-disc list-inside mt-1 text-muted">
            <li><strong>No formal forecasting (gut feeling):</strong> 40-60% error</li>
            <li><strong>Simple methods (moving average, last period):</strong> 30-50% error</li>
            <li><strong>Basic forecasting tools:</strong> 25-40% error</li>
            <li><strong>Advanced ML models:</strong> 15-30% error</li>
          </ul>
          <p class="mt-2 text-muted">
            <strong>💡 Tip:</strong> If unsure, start with 40% and adjust based on how often you have overstock/stockouts.
          </p>
        </div>
      </div>
    </UCard>

    <!-- Input Parameters -->
    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold">Input Parameters</h3>
      </template>
      <div class="space-y-6">
        <!-- Annual Revenue -->
        <UFormField label="Annual revenue (€)">
          <div class="flex items-center gap-4">
            <USlider
              v-model="revenue"
              :min="500000"
              :max="50000000"
              :step="500000"
              class="flex-1"
            />
            <span class="text-sm font-medium w-32 text-right">{{ formatNumber(revenue) }} €</span>
          </div>
        </UFormField>

        <!-- Inventory Distortion -->
        <UFormField
          label="Inventory distortion (overstock + stockouts) as % of revenue"
          hint="Industry average: 10-30%"
        >
          <div class="flex items-center gap-4">
            <USlider
              v-model="distortionPct"
              :min="10"
              :max="30"
              :step="1"
              class="flex-1"
            />
            <span class="text-sm font-medium w-16 text-right">{{ distortionPct.toFixed(0) }}%</span>
          </div>
        </UFormField>

        <!-- Current Forecast Accuracy -->
        <UFormField
          label="Current forecast accuracy: How far off are your forecasts today? (%)"
          hint="Example: 40% means if you forecast 100 units, you're typically off by 40 units."
        >
          <div class="flex items-center gap-4">
            <USlider
              v-model="baselineMape"
              :min="20"
              :max="60"
              :step="1"
              class="flex-1"
            />
            <span class="text-sm font-medium w-16 text-right">{{ baselineMape.toFixed(0) }}%</span>
          </div>
        </UFormField>

        <!-- Improved Forecast Accuracy -->
        <UFormField
          label="Improved forecast accuracy: How accurate could forecasts be? (%)"
          hint="Lower is better. Example: 25% means if you forecast 100 units, you're typically off by 25 units."
        >
          <div class="flex items-center gap-4">
            <USlider
              v-model="modelMape"
              :min="5"
              :max="50"
              :step="1"
              class="flex-1"
            />
            <span class="text-sm font-medium w-16 text-right">{{ modelMape.toFixed(0) }}%</span>
          </div>
        </UFormField>
      </div>
    </UCard>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <UCard class="border-l-4 border-l-red-500">
        <template #header>
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-red-500" />
            <h3 class="text-sm font-semibold">Current Accuracy</h3>
          </div>
        </template>
        <p class="text-2xl font-bold text-red-600">{{ baselineMape.toFixed(0) }}% off</p>
        <p class="text-xs text-muted mt-1">How far off your forecasts are today</p>
      </UCard>

      <UCard class="border-l-4 border-l-blue-500">
        <template #header>
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-blue-500" />
            <h3 class="text-sm font-semibold">Improved Accuracy</h3>
          </div>
        </template>
        <p class="text-2xl font-bold text-blue-600">{{ modelMape.toFixed(0) }}% off</p>
        <p class="text-xs text-muted mt-1">How accurate forecasts could be</p>
      </UCard>

      <UCard class="border-l-4 border-l-emerald-500">
        <template #header>
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-emerald-500" />
            <h3 class="text-sm font-semibold">Improvement</h3>
          </div>
        </template>
        <p class="text-2xl font-bold text-emerald-600">
          {{ mapeImprovement > 0 ? `${(errorReduction * 100).toFixed(0)}% better` : 'No improvement' }}
        </p>
        <p class="text-xs text-muted mt-1">
          {{ mapeImprovement > 0
            ? `Reduced error by ${mapeImprovement.toFixed(1)} percentage points`
            : 'No improvement possible'
          }}
        </p>
      </UCard>
    </div>

    <!-- Cost Comparison Chart -->
    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold">Cost Comparison</h3>
      </template>
      <div class="h-48">
        <Bar
          :data="chartData"
          :options="barChartOptions"
        />
      </div>
    </UCard>

    <!-- Savings Curve Chart -->
    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold">📈 How Forecast Accuracy Affects Savings</h3>
      </template>
      <div class="h-48">
        <Line
          :data="lineChartData"
          :options="lineChartOptions"
        />
      </div>
      <p class="text-xs text-muted mt-2">
        💡 As forecast error decreases (moving left), savings increase.
        Your selected improvement ({{ modelMape.toFixed(0) }}% error) saves {{ formatCurrency(savings) }} per year.
      </p>
    </UCard>

    <!-- What This Means -->
    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold">What This Means</h3>
      </template>
      <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <p class="font-semibold text-sm mb-2">Simple Example:</p>
        <p class="text-sm mb-2">
          Imagine you need to order inventory for next month. You forecast you'll sell <strong>100 units</strong>.
        </p>
        <ul class="text-sm space-y-1 list-disc list-inside">
          <li>
            <strong>With current accuracy ({{ baselineMape.toFixed(0) }}% error):</strong>
            You're typically off by {{ baselineMape.toFixed(0) }} units.
            You might order 100 but actually sell {{ (100 - baselineMape).toFixed(0) }}-{{ (100 + baselineMape).toFixed(0) }} units.
          </li>
          <li>
            <strong>With improved accuracy ({{ modelMape.toFixed(0) }}% error):</strong>
            You're typically off by {{ modelMape.toFixed(0) }} units.
            You might order 100 and actually sell {{ (100 - modelMape).toFixed(0) }}-{{ (100 + modelMape).toFixed(0) }} units.
          </li>
        </ul>
        <p class="text-sm mt-2">
          <strong>That's {{ mapeImprovement.toFixed(1) }} percentage points less error</strong>
          ({{ (errorReduction * 100).toFixed(0) }}% relative improvement) - meaning less overstock sitting in your warehouse
          and fewer stockouts where you lose sales.
        </p>
      </div>
    </UCard>

    <!-- Cost Summary -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <UCard>
        <template #header>
          <h3 class="text-sm font-semibold">Current Cost of Wrong Inventory</h3>
        </template>
        <p class="text-2xl font-bold">{{ formatCurrency(baselineDistortion) }}</p>
        <p class="text-xs text-muted mt-1">
          Money tied up in overstock + lost sales from stockouts
        </p>
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-sm font-semibold">Potential Annual Savings</h3>
        </template>
        <p class="text-2xl font-bold text-green-600">{{ formatCurrency(savings) }}</p>
        <p class="text-xs text-muted mt-1">
          {{ (errorReduction * 100).toFixed(0) }}% reduction - Money you could save with better forecasts
        </p>
      </UCard>
    </div>

    <!-- Savings at Different Levels -->
    <UCard>
      <template #header>
        <h3 class="text-sm font-semibold">💡 Savings at Different Accuracy Levels</h3>
      </template>
      <div class="h-48">
        <Bar
          :data="breakdownChartData"
          :options="breakdownChartOptions"
        />
      </div>
      <p class="text-xs text-muted mt-2">
        See how much more you could save by improving accuracy even further!
      </p>
    </UCard>

    <p class="text-xs text-muted">
      💡 <strong>Note:</strong> This is an estimate. Better forecasts reduce both overstock (money tied up) and stockouts (lost sales).
      Actual savings depend on your specific business.
    </p>
  </div>
</template>

<script setup lang="ts">
import { Bar, Line } from "vue-chartjs";

definePageMeta({
  layout: "dashboard",
});

// State
const revenue = ref(5_000_000);
const distortionPct = ref(20);
const baselineMape = ref(40);
const modelMape = ref(25);
const showHelp = ref(false);

// Computed values
const distortionDecimal = computed(() => distortionPct.value / 100);
const baselineDistortion = computed(() => revenue.value * distortionDecimal.value);
const mapeImprovement = computed(() => Math.max(0, baselineMape.value - modelMape.value));
const errorReduction = computed(() =>
  baselineMape.value > 0 ? mapeImprovement.value / baselineMape.value : 0
);
const savings = computed(() => baselineDistortion.value * errorReduction.value);
const modelCost = computed(() => baselineDistortion.value - savings.value);

// Format functions
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value: number) => {
  return new Intl.NumberFormat("de-DE").format(value);
};

// Chart data
const chartData = computed(() => ({
  labels: [`Current (${baselineMape.value.toFixed(0)}% error)`, `Improved (${modelMape.value.toFixed(0)}% error)`],
  datasets: [
    {
      label: "Cost (€)",
      data: [baselineDistortion.value, modelCost.value],
      backgroundColor: ["rgba(239, 68, 68, 0.7)", "rgba(34, 197, 94, 0.7)"],
      borderColor: ["rgb(239, 68, 68)", "rgb(34, 197, 94)"],
      borderWidth: 2,
    },
  ],
}));

const accuracyRange = computed(() => {
  const range: number[] = [];
  for (let i = 5; i <= Math.min(baselineMape.value + 5, 60); i += 1) {
    range.push(i);
  }
  return range;
});

const savingsCurve = computed(() => {
  return accuracyRange.value.map((acc) => {
    if (acc <= baselineMape.value) {
      const improvement = baselineMape.value - acc;
      const errorRed = improvement / baselineMape.value;
      return baselineDistortion.value * errorRed;
    }
    return 0;
  });
});

const lineChartData = computed(() => ({
  labels: accuracyRange.value.map((a) => `${a}%`),
  datasets: [
    {
      label: "Annual Savings (€)",
      data: savingsCurve.value,
      borderColor: "rgb(59, 130, 246)",
      backgroundColor: "rgba(59, 130, 246, 0.1)",
      tension: 0.4,
      fill: true,
    },
  ],
}));

const accuracyExamples = computed(() => {
  const examples = [
    { acc: Math.round(baselineMape.value), label: "Current" },
    { acc: Math.round(modelMape.value), label: "Your Target" },
    { acc: Math.max(5, Math.round(modelMape.value - 5)), label: "Even Better" },
    { acc: Math.max(5, Math.round(modelMape.value - 10)), label: "Best Case" },
  ];

  const seen = new Set<number>();
  return examples
    .filter((ex) => {
      const rounded = Math.round(ex.acc);
      if (rounded <= baselineMape.value && !seen.has(rounded)) {
        seen.add(rounded);
        return true;
      }
      return false;
    })
    .map((ex) => {
      const rounded = Math.round(ex.acc);
      const improvement = baselineMape.value - rounded;
      const errorRed = improvement / baselineMape.value;
      const savingsAtAcc = baselineDistortion.value * errorRed;
      return {
        label: `${ex.label}\n(${rounded}% error)`,
        savings: savingsAtAcc,
      };
    });
});

const breakdownChartData = computed(() => ({
  labels: accuracyExamples.value.map((ex) => ex.label),
  datasets: [
    {
      label: "Annual Savings (€)",
      data: accuracyExamples.value.map((ex) => ex.savings),
      backgroundColor: "rgba(59, 130, 246, 0.7)",
      borderColor: "rgb(59, 130, 246)",
      borderWidth: 2,
    },
  ],
}));

// Chart options
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: number) => formatCurrency(value),
      },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: { parsed: { y: number } }) => formatCurrency(context.parsed.y),
      },
    },
  },
};

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: number) => formatCurrency(value),
      },
    },
    x: {
      title: {
        display: true,
        text: "Forecast Error (%)",
      },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: { parsed: { y: number } }) => `Savings: ${formatCurrency(context.parsed.y)}`,
      },
    },
  },
};

const breakdownChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: number) => formatCurrency(value),
      },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: { parsed: { y: number } }) => formatCurrency(context.parsed.y),
      },
    },
  },
};
</script>

