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

    <!-- Recommendations List -->
    <UCard
      v-else
      class="overflow-hidden"
    >
      <div class="divide-y divide-gray-200 dark:divide-gray-800">
        <div
          v-for="rec in filteredRecommendations"
          :key="`${rec.item_id}-${rec.type}`"
          class="p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-start justify-between gap-6">
            <!-- Left: Type, Product -->
            <div class="flex items-start gap-4 flex-1 min-w-0">
              <UBadge
                :color="getTypeColor(rec.type)"
                variant="soft"
                size="sm"
                class="mt-0.5 flex-shrink-0"
              >
                {{ getTypeLabel(rec.type) }}
              </UBadge>
              
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">
                  {{ rec.product_name }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  {{ rec.item_id }}
                </div>
              </div>
            </div>
            
            <!-- Center: Revenue at Risk (prominent) -->
            <div
              v-if="getRevenueAtRisk(rec)"
              class="flex-shrink-0"
            >
              <UBadge
                color="red"
                variant="soft"
                size="md"
                class="font-semibold"
              >
                <UIcon
                  name="i-lucide-alert-circle"
                  class="w-4 h-4 mr-1"
                />
                €{{ getRevenueAtRisk(rec)?.toLocaleString() }} at risk
              </UBadge>
            </div>
            
            <!-- Right: Qty, Supplier, Actions -->
            <div class="flex items-center gap-4 flex-shrink-0">
              <div class="text-right">
                <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {{ rec.suggested_quantity }} units
                </div>
                <div
                  v-if="rec.supplier_name"
                  class="text-xs text-gray-500 dark:text-gray-400 mt-0.5"
                >
                  {{ rec.supplier_name }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <UButton
                  icon="i-lucide-shopping-cart"
                  color="primary"
                  size="sm"
                  @click="handleAddToCart(rec)"
                >
                  Add to Cart
                </UButton>
                <UButton
                  icon="i-lucide-eye"
                  variant="ghost"
                  size="sm"
                  @click="handleViewDetails(rec)"
                >
                  Details
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

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

    <!-- Recommendation Details Modal -->
    <UModal
      v-model:open="showDetailsModal"
      :ui="{ width: 'sm:max-w-3xl' }"
    >
      <template #content>
        <UCard
          v-if="selectedRecommendation"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-semibold">{{ selectedRecommendation.product_name }}</h3>
              <div class="flex items-center gap-2">
                <UBadge
                  :color="getTypeColor(selectedRecommendation.type)"
                  variant="soft"
                >
                  {{ getTypeLabel(selectedRecommendation.type) }}
                </UBadge>
                <UBadge
                  v-if="selectedRecommendation.priority === 'high'"
                  color="red"
                  variant="soft"
                >
                  High Priority
                </UBadge>
              </div>
            </div>
          </template>

          <div class="space-y-6">
            <!-- Product Info -->
            <div>
              <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Product ID</h4>
              <p class="text-gray-900 dark:text-gray-100">{{ selectedRecommendation.item_id }}</p>
            </div>

            <!-- Reason -->
            <div>
              <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Reason</h4>
              <p class="text-gray-900 dark:text-gray-100">{{ selectedRecommendation.reason }}</p>
            </div>

            <!-- Urgency Details -->
            <div
              v-if="selectedRecommendation.urgencyDetails"
              class="grid grid-cols-2 md:grid-cols-4 gap-4"
            >
              <div
                v-if="selectedRecommendation.urgencyDetails.dir !== undefined"
                class="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Days Until Stockout</div>
                <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {{ selectedRecommendation.urgencyDetails.dir.toFixed(1) }} days
                </div>
              </div>
              <div
                v-if="selectedRecommendation.urgencyDetails.leadTime"
                class="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Lead Time</div>
                <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {{ selectedRecommendation.urgencyDetails.leadTime }} days
                </div>
              </div>
              <div
                v-if="selectedRecommendation.urgencyDetails.velocity"
                class="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Sales Velocity</div>
                <div class="text-lg font-semibold text-gray-900 dark:text-gray-100 capitalize">
                  {{ selectedRecommendation.urgencyDetails.velocity }}
                </div>
              </div>
              <div
                v-if="selectedRecommendation.urgencyDetails.riskScore"
                class="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg"
              >
                <div class="text-xs text-red-600 dark:text-red-400 mb-1">Risk Score</div>
                <div class="text-lg font-semibold text-red-700 dark:text-red-300">
                  {{ selectedRecommendation.urgencyDetails.riskScore.toFixed(0) }}%
                </div>
              </div>
            </div>

            <!-- Revenue Impact -->
            <div
              v-if="getRevenueAtRisk(selectedRecommendation)"
              class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
              <div class="flex items-center gap-2 mb-2">
                <UIcon
                  name="i-lucide-alert-circle"
                  class="w-5 h-5 text-red-600 dark:text-red-400"
                />
                <h4 class="font-semibold text-red-900 dark:text-red-100">Revenue at Risk</h4>
              </div>
              <p class="text-lg font-bold text-red-700 dark:text-red-300">
                €{{ getRevenueAtRisk(selectedRecommendation)?.toLocaleString() }}
              </p>
              <p class="text-sm text-red-600 dark:text-red-400 mt-1">
                Estimated revenue at risk over the next 14 days
              </p>
            </div>

            <!-- Action Details -->
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div class="text-xs text-blue-600 dark:text-blue-400 mb-1">Suggested Quantity</div>
                <div class="text-2xl font-bold text-blue-900 dark:text-blue-100">
                  {{ selectedRecommendation.suggested_quantity }}
                </div>
                <div class="text-sm text-blue-700 dark:text-blue-300 mt-1">units</div>
              </div>
              <div
                v-if="selectedRecommendation.supplier_name"
                class="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">Supplier</div>
                <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {{ selectedRecommendation.supplier_name }}
                </div>
              </div>
            </div>
          </div>

          <template #footer>
            <div class="flex items-center justify-end gap-2">
              <UButton
                variant="ghost"
                @click="showDetailsModal = false"
              >
                Close
              </UButton>
              <UButton
                icon="i-lucide-shopping-cart"
                color="primary"
                @click="handleAddToCartFromModal"
              >
                Add to Cart
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
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
const showDetailsModal = ref(false);
const selectedRecommendation = ref<DemoRecommendation | null>(null);

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
const handleViewDetails = (rec: DemoRecommendation) => {
  selectedRecommendation.value = rec;
  showDetailsModal.value = true;
};

// Handle add to cart from modal
const handleAddToCartFromModal = async () => {
  if (selectedRecommendation.value) {
    await handleAddToCart(selectedRecommendation.value);
    showDetailsModal.value = false;
  }
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
