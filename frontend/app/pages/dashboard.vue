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

        <DashboardKpiCard
          label="Understocked"
          :value="dashboardData.metrics.understocked_count || 0"
          icon="i-lucide-alert-triangle"
          bg-color="bg-red-100 dark:bg-red-900"
          icon-color="text-red-500"
          value-color="text-red-600 dark:text-red-400"
        />

        <DashboardKpiCard
          label="Overstocked"
          :value="dashboardData.metrics.overstocked_count || 0"
          icon="i-lucide-trending-up"
          bg-color="bg-green-100 dark:bg-green-900"
          icon-color="text-green-500"
          value-color="text-green-600 dark:text-green-400"
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
                      toRiskPercent(item.stockout_risk) > 70
                        ? 'error'
                        : toRiskPercent(item.stockout_risk) > 40
                          ? 'warning'
                          : 'info'
                    "
                    variant="soft"
                  >
                    {{ toRiskPercent(item.stockout_risk).toFixed(1) }}% risk
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

      <!-- Trend Charts (Placeholder for future implementation) -->
      <!-- <div class="grid grid-cols-1 gap-6">
        <DashboardTrendChart
          title="Inventory Value Trend"
          :data="trendData"
          label="Inventory Value (€)"
        />
      </div> -->
    </div>
  </div>
</template>

<script setup lang="ts">
 import type { DashboardResponse } from "~/types/dashboard";
 import { getErrorText } from "~/utils/error";

definePageMeta({
  layout: "dashboard",
});

const { fetch } = useUserSession();
const dashboardData = ref<DashboardResponse | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const formatCurrency = (value: number): string => {
  return Math.round(value).toLocaleString("de-DE", {
    maximumFractionDigits: 0,
  });
};

const toRiskPercent = (risk: unknown): number => {
  const value = Number(risk);
  if (!Number.isFinite(value)) return 0;
  return value * 100;
};

const { handleAuthError } = useAuthError();

const loadDashboard = async () => {
  loading.value = true;
  error.value = null;

  try {
    const data = await $fetch<DashboardResponse>("/api/dashboard");
    dashboardData.value = data;
  } catch (err: unknown) {
    // Handle 401 errors - redirect to login
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) {
      // Redirect is handled, just return
      return;
    }
    error.value = getErrorText(err, "Failed to load dashboard data");
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
