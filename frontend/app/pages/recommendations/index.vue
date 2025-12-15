<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Action Items</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Prioritized recommendations to optimize your inventory
        </p>
      </div>
      <div class="flex items-center gap-2">
        <UButton
          icon="i-lucide-refresh-cw"
          variant="ghost"
          :loading="loading"
          @click="loadRecommendations"
        >
          Refresh
        </UButton>
      </div>
    </div>

    <!-- Quick Action Filters -->
    <div class="flex items-center gap-2 flex-wrap">
      <UButton
        :variant="activeFilter === 'all' ? 'solid' : 'outline'"
        :color="activeFilter === 'all' ? 'primary' : 'gray'"
        :class="activeFilter === 'all' ? 'ring-2 ring-primary-500 ring-offset-2' : ''"
        @click="applyFilter('all')"
      >
        All
        <UBadge
          :label="filterCounts.all.toString()"
          :color="activeFilter === 'all' ? 'white' : 'gray'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
      <UButton
        :variant="activeFilter === 'urgent' ? 'solid' : 'outline'"
        :color="activeFilter === 'urgent' ? 'red' : 'gray'"
        :class="activeFilter === 'urgent' ? 'ring-2 ring-red-500 ring-offset-2' : ''"
        icon="i-lucide-alert-triangle"
        @click="applyFilter('urgent')"
      >
        Urgent
        <UBadge
          :label="filterCounts.urgent.toString()"
          :color="activeFilter === 'urgent' ? 'white' : 'red'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
      <UButton
        :variant="activeFilter === 'reorder' ? 'solid' : 'outline'"
        :color="activeFilter === 'reorder' ? 'blue' : 'gray'"
        :class="activeFilter === 'reorder' ? 'ring-2 ring-blue-500 ring-offset-2' : ''"
        icon="i-lucide-shopping-cart"
        @click="applyFilter('reorder')"
      >
        Reorder
        <UBadge
          :label="filterCounts.reorder.toString()"
          :color="activeFilter === 'reorder' ? 'white' : 'blue'"
          variant="solid"
          class="ml-2"
        />
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
      color="warning"
      variant="soft"
      title="Error loading recommendations"
      :description="error"
    />

    <!-- Action Cards -->
    <div
      v-else
      class="grid grid-cols-1 lg:grid-cols-2 gap-4"
    >
      <UCard
        v-for="rec in filteredRecommendations"
        :key="`${rec.item_id}-${rec.type}`"
        :class="getCardClass(rec)"
        class="hover:shadow-lg transition-shadow cursor-pointer"
        @click="handleViewDetails(rec)"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 space-y-2">
            <!-- Header with Type and Priority -->
            <div class="flex items-center gap-2">
              <UBadge
                :color="getTypeColor(rec.type)"
                variant="soft"
                size="sm"
              >
                {{ getTypeLabel(rec.type) }}
              </UBadge>
              <UBadge
                v-if="rec.priority === 'high'"
                color="red"
                variant="soft"
                size="sm"
              >
                High Priority
              </UBadge>
            </div>

            <!-- Product Info -->
            <div>
              <h3 class="font-semibold text-lg">{{ rec.product_name }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ rec.item_id }}</p>
            </div>

            <!-- Reason with urgency details -->
            <div class="space-y-1">
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ rec.reason }}
              </p>
              <div
                v-if="rec.urgencyDetails"
                class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2 flex-wrap"
              >
                <span
                  v-if="rec.urgencyDetails.dir !== undefined"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-calendar"
                    class="w-3 h-3"
                  />
                  DIR: {{ rec.urgencyDetails.dir.toFixed(1) }}d
                </span>
                <span
                  v-if="rec.urgencyDetails.leadTime"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-clock"
                    class="w-3 h-3"
                  />
                  Lead: {{ rec.urgencyDetails.leadTime }}d
                </span>
                <span
                  v-if="rec.urgencyDetails.velocity"
                  class="flex items-center gap-1"
                >
                  <UIcon
                    name="i-lucide-trending-up"
                    class="w-3 h-3"
                  />
                  Velocity: {{ rec.urgencyDetails.velocity }}
                </span>
              </div>
            </div>

            <!-- Revenue Impact -->
            <div
              v-if="getRevenueAtRisk(rec)"
              class="flex items-center gap-2 text-sm font-medium text-red-700 dark:text-red-300"
            >
              <UIcon
                name="i-lucide-alert-circle"
                class="w-4 h-4"
              />
              <span>Est. revenue at risk (next 14 days): €{{ getRevenueAtRisk(rec)?.toLocaleString() }}</span>
            </div>

            <!-- Action Details -->
            <div class="flex items-center gap-4 text-sm">
              <div
                v-if="rec.suggested_quantity"
                class="flex items-center gap-1"
              >
                <UIcon
                  name="i-lucide-package"
                  class="w-4 h-4 text-gray-400"
                />
                <span class="font-medium">Order {{ rec.suggested_quantity }} units</span>
              </div>
              <div
                v-if="rec.supplier_name"
                class="flex items-center gap-1 text-gray-500"
              >
                <UIcon
                  name="i-lucide-truck"
                  class="w-4 h-4"
                />
                <span>{{ rec.supplier_name }}</span>
              </div>
            </div>
          </div>

          <!-- Action Button -->
          <div class="flex flex-col items-end gap-2">
            <UButton
              icon="i-lucide-shopping-cart"
              color="primary"
              size="sm"
              @click.stop="handleAddToCart(rec)"
            >
              Add to Cart
            </UButton>
            <UButton
              icon="i-lucide-eye"
              variant="ghost"
              size="xs"
              @click.stop="handleViewDetails(rec)"
            >
              View Details
            </UButton>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Empty State -->
    <div
      v-if="!loading && !error && filteredRecommendations.length === 0"
      class="text-center py-12"
    >
      <UIcon
        name="i-lucide-check-circle"
        class="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4"
      />
      <p class="text-lg font-medium text-gray-500 dark:text-gray-400">
        No recommendations found
      </p>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
        All inventory levels are optimal
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Recommendation } from "~/types/recommendation";

definePageMeta({
  layout: "dashboard",
});

const { fetchRecommendations, addToCart } = useRecommendations();
const { handleAuthError } = useAuthError();

// Extended recommendation interface for demo
interface DemoRecommendation extends Recommendation {
  urgencyDetails?: {
    dir?: number;
    leadTime?: number;
    velocity?: string;
    riskScore?: number;
  };
}

const rowData = ref<DemoRecommendation[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const activeFilter = ref<'all' | 'urgent' | 'reorder'>('all');

// Filter counts
const filterCounts = computed(() => {
  const all = rowData.value.length;
  const urgent = rowData.value.filter(r => r.type === 'URGENT').length;
  const reorder = rowData.value.filter(r => r.type === 'REORDER').length;
  
  return { all, urgent, reorder };
});

// Filtered recommendations
const filteredRecommendations = computed(() => {
  if (activeFilter.value === 'all') return rowData.value;
  if (activeFilter.value === 'urgent') return rowData.value.filter(r => r.type === 'URGENT');
  if (activeFilter.value === 'reorder') return rowData.value.filter(r => r.type === 'REORDER');
  return rowData.value;
});

// Apply filter
const applyFilter = (filter: 'all' | 'urgent' | 'reorder') => {
  activeFilter.value = filter;
};

// Get type label
const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    URGENT: 'Urgent',
    REORDER: 'Reorder',
    REDUCE_ORDER: 'Reduce Order',
    DEAD_STOCK: 'Dead Stock',
    PROMOTE: 'Promote',
  };
  return labels[type] || type;
};

// Calculate revenue at risk for a recommendation
const getRevenueAtRisk = (rec: DemoRecommendation): number | null => {
  if (rec.type !== 'URGENT' && rec.type !== 'REORDER') return null;
  
  // Demo calculation: estimate based on urgency details
  const dir = rec.urgencyDetails?.dir || 14;
  const riskScore = rec.urgencyDetails?.riskScore || 70;
  
  // Simple estimate: assume average unit price and sales velocity
  // For demo: use rough estimates
  const avgUnitPrice = 25; // Demo constant
  const avgDailySales = dir < 7 ? 20 : dir < 14 ? 15 : 10; // Higher sales for urgent items
  const riskFactor = (riskScore || 70) / 100;
  
  // Revenue at risk = avg_daily_sales * unit_price * 14 days * risk_factor
  const revenueAtRisk = avgDailySales * avgUnitPrice * 14 * riskFactor;
  
  return Math.round(revenueAtRisk);
};

// Get type color
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    URGENT: 'red',
    REORDER: 'blue',
    REDUCE_ORDER: 'orange',
    DEAD_STOCK: 'gray',
    PROMOTE: 'green',
  };
  return colors[type] || 'gray';
};

// Get card class based on type
const getCardClass = (rec: Recommendation) => {
  if (rec.type === 'URGENT') {
    return 'border-l-4 border-red-500';
  }
  if (rec.type === 'REORDER') {
    return 'border-l-4 border-blue-500';
  }
  return '';
};

// Handle add to cart
const handleAddToCart = async (rec: Recommendation) => {
  const toast = useToast();
  try {
    // DEMO MODE: Simulate add to cart
    // await addToCart(rec.item_id, rec.supplier_id, rec.suggested_quantity);
    
    await new Promise(resolve => setTimeout(resolve, 300));
    
    toast.add({
      title: "Added to cart",
      description: `${rec.product_name} added to order planning cart`,
      color: "success",
      icon: "i-lucide-check-circle",
    });
    
    // Refresh cart count
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('cart-updated'));
    }
  } catch (err: any) {
    toast.add({
      title: "Error",
      description: "Failed to add item to cart",
      color: "error",
      icon: "i-lucide-alert-circle",
    });
  }
};

// Handle view details
const handleViewDetails = (rec: Recommendation) => {
  navigateTo(`/inventory?item=${rec.item_id}`);
};

// Demo recommendations data (hardcoded for demo branch)
const getDemoRecommendations = (): DemoRecommendation[] => {
  const recommendations: DemoRecommendation[] = [];
  
  // Urgent recommendations (stockout risk)
  for (let i = 1; i <= 12; i++) {
    const itemId = `M5_HOUSEHOLD_1_${String(i + 300).padStart(3, '0')}`;
    const stockoutRisk = Math.random() * 0.25 + 0.7; // 70-95% risk
    const dir = Math.random() * 5 + 1; // 1-6 days
    const suggestedQty = Math.floor(Math.random() * 100 + 50);
    const leadTime = 14;
    const velocity = Math.random() > 0.5 ? 'high' : 'medium';
    
    recommendations.push({
      type: 'URGENT',
      priority: 'high',
      item_id: itemId,
      product_name: `Product ${itemId}`,
      reason: `Stockout risk ${(stockoutRisk * 100).toFixed(1)}% - Only ${dir.toFixed(1)} days remaining`,
      suggested_quantity: suggestedQty,
      supplier_id: `SUPPLIER_${i % 3 + 1}`,
      supplier_name: `Supplier ${i % 3 + 1}`,
      urgencyDetails: {
        dir: dir,
        leadTime: leadTime,
        velocity: velocity,
        riskScore: stockoutRisk * 100,
      },
    });
  }
  
  // Reorder recommendations
  for (let i = 1; i <= 20; i++) {
    const itemId = `M5_HOBBIES_1_${String(i + 200).padStart(3, '0')}`;
    const dir = Math.random() * 20 + 10; // 10-30 days
    const leadTime = 14;
    const buffer = 7;
    const suggestedQty = Math.floor(Math.random() * 80 + 30);
    const velocity = Math.random() > 0.6 ? 'high' : Math.random() > 0.3 ? 'medium' : 'low';
    
    recommendations.push({
      type: 'REORDER',
      priority: i < 8 ? 'high' : 'medium',
      item_id: itemId,
      product_name: `Product ${itemId}`,
      reason: `DIR ${dir.toFixed(1)} days < lead time + buffer (${leadTime + buffer} days)`,
      suggested_quantity: suggestedQty,
      supplier_id: `SUPPLIER_${i % 3 + 1}`,
      supplier_name: `Supplier ${i % 3 + 1}`,
      urgencyDetails: {
        dir: dir,
        leadTime: leadTime,
        velocity: velocity,
      },
    });
  }
  
  return recommendations;
};

const loadRecommendations = async () => {
  // Prevent concurrent calls
  if (loading.value) {
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // DEMO MODE: Use hardcoded data instead of API call
    // const recommendations = await fetchRecommendations({
    //   recommendation_type: selectedType.value || undefined,
    // });
    
    rowData.value = getDemoRecommendations();
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));
  } catch (err: any) {
    // Fallback to demo data
    rowData.value = getDemoRecommendations();
    console.warn("Using demo data due to error:", err);
  } finally {
    loading.value = false;
  }
};

// Load data on mount
onMounted(() => {
  loadRecommendations();
});
</script>
