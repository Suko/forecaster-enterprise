<template>
  <div class="space-y-6">
    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Forecasting Assumptions</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          System parameters and assumptions used for inventory forecasting
        </p>
      </template>

      <div class="space-y-6">
        <!-- Service Level -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Service Level Target</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Target fill rate for inventory planning
            </p>
          </div>
          <UBadge
            color="primary"
            variant="soft"
          >
            95%
          </UBadge>
        </div>

        <!-- Safety Stock Method -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Safety Stock Method</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              How safety stock is calculated
            </p>
          </div>
          <UBadge
            color="blue"
            variant="soft"
          >
            Days-Based
          </UBadge>
        </div>

        <!-- Default Safety Buffer -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Default Safety Buffer</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Default days of safety stock coverage
            </p>
          </div>
          <span class="font-semibold">7 days</span>
        </div>

        <!-- Lead Time Source -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Lead Time Source</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Where lead times are sourced from
            </p>
          </div>
          <UBadge
            color="green"
            variant="soft"
          >
            Supplier Default
          </UBadge>
        </div>

        <!-- Forecast Horizon -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Forecast Horizon</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              How far ahead forecasts are generated
            </p>
          </div>
          <span class="font-semibold">90 days</span>
        </div>

        <!-- Review Period -->
        <div class="flex items-center justify-between py-3 border-b">
          <div>
            <p class="font-medium">Review Period</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Standard review cycle for reorder decisions
            </p>
          </div>
          <span class="font-semibold">7 days</span>
        </div>

        <!-- Seasonality -->
        <div class="flex items-center justify-between py-3">
          <div>
            <p class="font-medium">Seasonality Adjustment</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Whether seasonal patterns are considered
            </p>
          </div>
          <UBadge
            color="purple"
            variant="soft"
          >
            Enabled
          </UBadge>
        </div>
      </div>
    </UCard>

    <!-- Risk Thresholds -->
    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Risk Thresholds</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Thresholds used to classify inventory status
        </p>
      </template>

      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <p class="text-sm font-medium text-red-700 dark:text-red-300">Understocked</p>
            <p class="text-xs text-red-600 dark:text-red-400 mt-1">DIR &lt; 14 days</p>
            <p class="text-xs text-red-500 dark:text-red-500 mt-1">or Risk &gt; 70%</p>
          </div>
          <div class="p-4 bg-gray-50 dark:bg-gray-900/20 rounded-lg border border-gray-200 dark:border-gray-800">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Normal</p>
            <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">14 ≤ DIR ≤ 90 days</p>
            <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">Risk &lt; 70%</p>
          </div>
          <div class="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <p class="text-sm font-medium text-green-700 dark:text-green-300">Overstocked</p>
            <p class="text-xs text-green-600 dark:text-green-400 mt-1">DIR &gt; 90 days</p>
            <p class="text-xs text-green-500 dark:text-green-500 mt-1">Excess inventory</p>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Note -->
    <UAlert
      color="info"
      variant="soft"
      title="Demo Mode"
      description="These are demo assumptions. In production, these values are configurable per client."
    />
  </div>
</template>

<script setup lang="ts">
// Read-only settings preview for demo
</script>

