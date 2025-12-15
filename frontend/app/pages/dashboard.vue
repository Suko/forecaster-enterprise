<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">Dashboard</h1>
      <UButton
        icon="i-lucide-refresh-cw"
        variant="ghost"
        :loading="loading"
        @click="loadDashboard"
      >
        Refresh
      </UButton>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary"
      />
    </div>

    <!-- Error State -->
    <UAlert
      v-else-if="error"
      color="error"
      variant="soft"
      title="Error loading dashboard"
      :description="error"
    />

    <!-- Dashboard Content -->
    <div
      v-else-if="dashboardData"
      class="space-y-6"
    >
      <!-- Money Impact Banner -->
      <UCard class="bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-800">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <UIcon
                name="i-lucide-lock"
                class="w-6 h-6 text-orange-600 dark:text-orange-400"
              />
            </div>
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Cash Tied Up in Overstock</p>
              <p class="text-2xl font-bold text-orange-700 dark:text-orange-300">
                €{{ moneyImpact.cashTiedUp.toLocaleString() }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {{ dashboardData.metrics.overstocked_count }} SKUs overstocked
              </p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="p-3 bg-red-100 dark:bg-red-900 rounded-lg">
              <UIcon
                name="i-lucide-alert-circle"
                class="w-6 h-6 text-red-600 dark:text-red-400"
              />
            </div>
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Revenue at Risk (Next 14 Days)</p>
              <p class="text-2xl font-bold text-red-700 dark:text-red-300">
                €{{ moneyImpact.revenueAtRisk.toLocaleString() }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                Based on stockout risk and sales velocity
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardKpiCard
          label="Total Inventory Value"
          :value="`€${formatCurrency(
            parseFloat(dashboardData.metrics.total_inventory_value || '0')
          )}`"
          icon="i-lucide-euro"
          bg-color="bg-blue-100 dark:bg-blue-900"
          icon-color="text-blue-500"
          value-color="text-blue-600 dark:text-blue-400"
        />

        <DashboardKpiCard
          label="Total SKUs"
          :value="dashboardData.metrics.total_skus || 0"
          icon="i-lucide-package"
          bg-color="bg-primary-100 dark:bg-primary-900"
          icon-color="text-primary-500"
          value-color="text-primary-600 dark:text-primary-400"
        />

        <NuxtLink
          to="/recommendations?filter=urgent"
          class="block no-underline"
        >
          <DashboardKpiCard
            label="Understocked"
            :value="dashboardData.metrics.understocked_count || 0"
            icon="i-lucide-alert-triangle"
            bg-color="bg-red-100 dark:bg-red-900"
            icon-color="text-red-500"
            value-color="text-red-600 dark:text-red-400"
            class="cursor-pointer hover:opacity-80 transition-opacity"
          />
        </NuxtLink>

        <NuxtLink
          to="/inventory?status=overstocked"
          class="block no-underline"
        >
          <DashboardKpiCard
            label="Overstocked"
            :value="dashboardData.metrics.overstocked_count || 0"
            icon="i-lucide-trending-up"
            bg-color="bg-green-100 dark:bg-green-900"
            icon-color="text-green-500"
            value-color="text-green-600 dark:text-green-400"
            class="cursor-pointer hover:opacity-80 transition-opacity"
          />
        </NuxtLink>
      </div>

      <!-- Summary Sentence -->
      <UCard class="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <p class="text-sm text-gray-700 dark:text-gray-300">
          <span class="font-semibold">Reordering top {{ Math.min(5, dashboardData.metrics.understocked_count || 0) }} items</span>
          <span> reduces revenue risk by ~{{ Math.round((Math.min(5, dashboardData.metrics.understocked_count || 0) / Math.max(1, dashboardData.metrics.understocked_count || 1)) * 35) }}%.</span>
        </p>
      </UCard>

      <!-- Trend Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardTrendChart
          title="Inventory Value Trend (Last 90 Days)"
          :data="demoTrendData"
          label="Inventory Value (€)"
          color="rgb(59, 130, 246)"
          :subtitle="`<span class='inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 font-semibold text-xs'><span>↓</span><span>${inventoryReductionPercent}% reduction</span></span> <span class='text-gray-600 dark:text-gray-400'>• Reduced by <span class='font-semibold text-gray-900 dark:text-gray-100'>€${inventoryReductionAmount.toLocaleString()}</span> over 90 days</span>`"
        />
        <DashboardTrendChart
          title="Sales Velocity Trend (Last 90 Days)"
          :data="demoSalesTrendData"
          label="Units Sold"
          color="rgb(16, 185, 129)"
        />
      </div>

      <!-- Charts Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Top Understocked Products -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">Top 5 Understocked Products</h3>
          </template>
          <div class="p-4">
            <div
              v-if="dashboardData.top_understocked.length === 0"
              class="text-center text-gray-400 py-8"
            >
              No understocked items
            </div>
            <div
              v-else
              class="space-y-2"
            >
              <div
                v-for="item in dashboardData.top_understocked"
                :key="item.item_id"
                class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                @click="navigateTo(`/inventory?item=${item.item_id}`)"
              >
                <div class="flex-1">
                  <p class="font-medium">{{ item.product_name }}</p>
                  <p class="text-sm text-gray-500">{{ item.item_id }}</p>
                </div>
                <div class="text-right">
                  <UBadge
                    :color="
                      (Number(item.stockout_risk) || 0) > 70
                        ? 'error'
                        : (Number(item.stockout_risk) || 0) > 40
                          ? 'warning'
                          : 'info'
                    "
                    variant="soft"
                  >
                    {{ (Number(item.stockout_risk) || 0).toFixed(1) }}% risk
                  </UBadge>
                  <p class="text-xs text-gray-400 mt-1">
                    {{ (Number(item.dir) || 0).toFixed(1) }} days
                  </p>
                </div>
              </div>
            </div>
          </div>
        </UCard>

        <!-- Top Overstocked Products -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">Top 5 Overstocked Products</h3>
          </template>
          <div class="p-4">
            <div
              v-if="dashboardData.top_overstocked.length === 0"
              class="text-center text-gray-400 py-8"
            >
              No overstocked items
            </div>
            <div
              v-else
              class="space-y-2"
            >
              <div
                v-for="item in dashboardData.top_overstocked"
                :key="item.item_id"
                class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                @click="navigateTo(`/inventory?item=${item.item_id}`)"
              >
                <div class="flex-1">
                  <p class="font-medium">{{ item.product_name }}</p>
                  <p class="text-sm text-gray-500">{{ item.item_id }}</p>
                </div>
                <div class="text-right">
                  <p class="text-sm font-medium">{{ (Number(item.dir) || 0).toFixed(1) }} days</p>
                  <p class="text-xs text-gray-400">Overstocked</p>
                </div>
              </div>
            </div>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DashboardResponse } from "~/types/dashboard";

definePageMeta({
  layout: "dashboard",
});

const { user, fetch } = useUserSession();
const dashboardData = ref<DashboardResponse | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const formatCurrency = (value: number): string => {
  return Math.round(value).toLocaleString("de-DE", {
    maximumFractionDigits: 0,
  });
};

// Demo trend data (hardcoded for demo)
// Shows inventory reduction over time - demonstrating system effectiveness
// Values match the KPI card (current total inventory value)
const currentTotalInventory = 2900000; // Current total inventory (~2.9M, matches KPI)
const reductionPercent = 29; // 29% reduction over 90 days
const startInventoryValue = 4100000; // Starting value 90 days ago (~4.1M)
const endInventoryValue = currentTotalInventory; // Current value (~2.9M)

const inventoryReductionAmount = computed(() => {
  return startInventoryValue - endInventoryValue;
});

const inventoryReductionPercent = computed(() => {
  return reductionPercent; // Fixed at 29% for demo
});

// Money impact calculations (demo mode)
const moneyImpact = computed(() => {
  // Cash tied up in overstock
  const overstockedValue = parseFloat(dashboardData.value?.metrics.overstocked_value || '1200000');
  const cashTiedUp = overstockedValue;
  
  // Revenue at risk (next 14 days) - simplified calculation
  // Based on understocked items with high risk
  const understockedValue = parseFloat(dashboardData.value?.metrics.understocked_value || '450000');
  const understockedCount = dashboardData.value?.metrics.understocked_count || 23;
  
  // Estimate: average unit cost * average daily sales * 14 days * risk factor
  // Simplified: use understocked value as base, apply risk multiplier
  const avgUnitCost = understockedValue / (understockedCount * 100); // Rough estimate
  const avgDailySales = 15; // Demo constant
  const riskMultiplier = 0.75; // Average risk for understocked items
  const revenueAtRisk = Math.round(avgUnitCost * avgDailySales * 14 * riskMultiplier * understockedCount);
  
  return {
    cashTiedUp: Math.round(cashTiedUp),
    revenueAtRisk: revenueAtRisk,
  };
});

const demoTrendData = computed(() => {
  const data = [];
  const today = new Date();
  
  // Monthly data points (3 months = ~90 days)
  // Each month shows a step reduction, making it clear actions were taken
  const months = [
    { daysAgo: 90, value: startInventoryValue }, // 3 months ago - starting point
    { daysAgo: 60, value: startInventoryValue - (startInventoryValue - endInventoryValue) * 0.4 }, // 2 months ago - first reduction
    { daysAgo: 30, value: startInventoryValue - (startInventoryValue - endInventoryValue) * 0.7 }, // 1 month ago - second reduction
    { daysAgo: 0, value: endInventoryValue }, // Current - final value
  ];
  
  // Generate data points for each month
  months.forEach((month, index) => {
    const date = new Date(today);
    date.setDate(date.getDate() - month.daysAgo);
    
    // Add the month-end data point
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(month.value),
    });
    
    // If not the last month, add a mid-month point to show the transition
    if (index < months.length - 1) {
      const midDate = new Date(today);
      midDate.setDate(midDate.getDate() - (month.daysAgo + (month.daysAgo - months[index + 1].daysAgo) / 2));
      
      // Mid-month value (slightly higher, showing gradual decline within month)
      const midValue = month.value - (month.value - months[index + 1].value) * 0.3;
      data.push({
        date: midDate.toISOString().split('T')[0],
        value: Math.round(midValue),
      });
    }
  });
  
  // Sort by date
  data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  return data;
});

const demoSalesTrendData = computed(() => {
  const data = [];
  const today = new Date();
  
  // Monthly data points showing sales velocity trend
  // Sales velocity should show improvement (more units sold) as inventory is optimized
  const months = [
    { daysAgo: 90, value: 850 }, // 3 months ago - lower sales (inefficient inventory)
    { daysAgo: 60, value: 1050 }, // 2 months ago - improving sales
    { daysAgo: 30, value: 1250 }, // 1 month ago - better sales
    { daysAgo: 0, value: 1400 }, // Current - optimized sales velocity
  ];
  
  // Generate data points for each month
  months.forEach((month, index) => {
    const date = new Date(today);
    date.setDate(date.getDate() - month.daysAgo);
    
    // Add the month-end data point
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(month.value),
    });
    
    // If not the last month, add a mid-month point to show the transition
    if (index < months.length - 1) {
      const midDate = new Date(today);
      midDate.setDate(midDate.getDate() - (month.daysAgo + (month.daysAgo - months[index + 1].daysAgo) / 2));
      
      // Mid-month value (showing gradual improvement)
      const midValue = month.value + (months[index + 1].value - month.value) * 0.4;
      data.push({
        date: midDate.toISOString().split('T')[0],
        value: Math.round(midValue),
      });
    }
  });
  
  // Sort by date
  data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  return data;
});

const { handleAuthError } = useAuthError();

// Demo dashboard data (hardcoded for demo branch)
// Inventory value matches the current chart value (2.9M)
const getDemoDashboardData = (): DashboardResponse => {
  return {
    metrics: {
      total_inventory_value: "2900000", // 2.9M - matches chart end value
      total_skus: 200,
      understocked_count: 23,
      overstocked_count: 95,
      understocked_value: "450000",
      overstocked_value: "1200000",
    },
    top_understocked: [
      { item_id: "M5_HOUSEHOLD_1_334", product_name: "Product M5_HOUSEHOLD_1_334", dir: 1.3, stockout_risk: 0.944 },
      { item_id: "M5_HOBBIES_1_387", product_name: "Product M5_HOBBIES_1_387", dir: 2.3, stockout_risk: 0.894 },
      { item_id: "M5_HOBBIES_1_404", product_name: "Product M5_HOBBIES_1_404", dir: 2.8, stockout_risk: 0.889 },
      { item_id: "M5_HOBBIES_1_209", product_name: "Product M5_HOBBIES_1_209", dir: 2.1, stockout_risk: 0.884 },
      { item_id: "M5_HOUSEHOLD_1_370", product_name: "Product M5_HOUSEHOLD_1_370", dir: 2.7, stockout_risk: 0.857 },
    ],
    top_overstocked: [
      { item_id: "M5_HOUSEHOLD_1_082", product_name: "Product M5_HOUSEHOLD_1_082", dir: 368.7 },
      { item_id: "M5_HOUSEHOLD_1_086", product_name: "Product M5_HOUSEHOLD_1_086", dir: 351.1 },
      { item_id: "M5_HOUSEHOLD_1_048", product_name: "Product M5_HOUSEHOLD_1_048", dir: 251.5 },
      { item_id: "M5_HOUSEHOLD_1_027", product_name: "Product M5_HOUSEHOLD_1_027", dir: 236.3 },
      { item_id: "M5_HOUSEHOLD_1_439", product_name: "Product M5_HOUSEHOLD_1_439", dir: 194.1 },
    ],
  };
};

const loadDashboard = async () => {
  loading.value = true;
  error.value = null;

  try {
    // DEMO MODE: Use hardcoded data instead of API call
    // const data = await $fetch<DashboardResponse>("/api/dashboard");
    dashboardData.value = getDemoDashboardData();
    
    // Simulate network delay for demo
    await new Promise(resolve => setTimeout(resolve, 300));
  } catch (err: any) {
    // Fallback to demo data on error
    dashboardData.value = getDemoDashboardData();
    console.warn("Using demo data due to error:", err);
  } finally {
    loading.value = false;
  }
};

// Load dashboard on mount
onMounted(async () => {
  await fetch();
  await loadDashboard();
});
</script>
