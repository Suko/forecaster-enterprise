<script setup lang="ts">
 import type { Supplier } from "~/types/supplier";
 import type { Product, ProductListResponse } from "~/types/product";
 import type { ProductSupplierCondition } from "~/types/inventory";
 import { getErrorText } from "~/utils/error";

definePageMeta({
  layout: "dashboard",
});

const route = useRoute();
const supplierId = computed(() => String(route.params.id || ""));

const { fetchSupplier, updateSupplier } = useSuppliers();
const { getProductSuppliers, addProductSupplier, updateProductSupplier } = useProductSuppliers();
const { handleAuthError } = useAuthError();
const toast = useToast();

const loading = ref(false);
const error = ref<string | null>(null);
const supplier = ref<Supplier | null>(null);

const isEditing = ref(false);
const editForm = ref({
  name: "",
  contact_email: "",
  contact_phone: "",
  address: "",
  supplier_type: "PO",
  default_moq: 0,
  default_lead_time_days: 14,
  notes: "",
});
const saving = ref(false);
const showApplyDialog = ref(false);
const applyToExisting = ref(false);
const pendingChanges = ref<{ default_moq?: number; default_lead_time_days?: number } | null>(null);

const productsLoading = ref(false);
const productsError = ref<string | null>(null);
const products = ref<Product[]>([]);
const productsTotal = ref(0);
const productsPage = ref(1);
const productsPageSize = ref(50);
const productsTotalPages = ref(0);
const productConditions = ref<Map<string, ProductSupplierCondition>>(new Map());
const editingProductId = ref<string | null>(null);
const editingProductForm = ref<{
  moq: number;
  lead_time_days: number;
  is_primary?: boolean;
} | null>(null);
const savingProduct = ref(false);

const loadSupplier = async () => {
  if (!supplierId.value) return;
  loading.value = true;
  error.value = null;
  try {
    supplier.value = await fetchSupplier(supplierId.value);
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = getErrorText(err, "Failed to load supplier");
  } finally {
    loading.value = false;
  }
};

const loadProducts = async (page: number = productsPage.value) => {
  if (!supplierId.value) return;
  productsLoading.value = true;
  productsError.value = null;
  try {
    const res = await $fetch<ProductListResponse>("/api/products", {
      query: {
        page,
        page_size: productsPageSize.value,
        supplier_id: supplierId.value,
      },
    });
    products.value = res.items || [];
    productsTotal.value = res.total || 0;
    productsPage.value = res.page || 1;
    productsPageSize.value = res.page_size || 50;
    productsTotalPages.value = res.total_pages || 0;

    // Load product-supplier conditions for each product
    await loadProductConditions();
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    productsError.value = getErrorText(err, "Failed to load products");
  } finally {
    productsLoading.value = false;
  }
};

const goToPage = (page: number) => {
  if (page >= 1 && page <= productsTotalPages.value && page !== productsPage.value) {
    loadProducts(page);
  }
};

const getVisiblePages = (): number[] => {
  const current = productsPage.value;
  const total = productsTotalPages.value;
  const pages: number[] = [];

  if (total <= 7) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // Show first page, pages around current, and last page
    pages.push(1);

    if (current > 3) {
      pages.push(-1); // Ellipsis marker
    }

    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);

    for (let i = start; i <= end; i++) {
      if (!pages.includes(i)) {
        pages.push(i);
      }
    }

    if (current < total - 2) {
      pages.push(-1); // Ellipsis marker
    }

    if (!pages.includes(total)) {
      pages.push(total);
    }
  }

  return pages;
};

const loadProductConditions = async () => {
  if (!supplierId.value) return;

  const conditionsMap = new Map<string, ProductSupplierCondition>();

  for (const product of products.value) {
    try {
      const conditions = await getProductSuppliers(product.item_id);
      // Find condition for this supplier
      const condition = conditions.find((c) => c.supplier_id === supplierId.value);
      if (condition) {
        conditionsMap.set(product.item_id, condition);
      }
    } catch {
      // Silently fail for individual products - errors logged on server side
    }
  }

  productConditions.value = conditionsMap;
};

const getProductCondition = (itemId: string): ProductSupplierCondition | null => {
  return productConditions.value.get(itemId) || null;
};

const isUsingSupplierDefault = (itemId: string, field: "moq" | "lead_time_days"): boolean => {
  if (!supplier.value) return false;
  const condition = getProductCondition(itemId);
  if (!condition) return true; // No condition means using default

  if (field === "moq") {
    return condition.moq === (supplier.value.default_moq || 0);
  } else {
    return condition.lead_time_days === (supplier.value.default_lead_time_days || 14);
  }
};

const startEditingProduct = (product: Product) => {
  const condition = getProductCondition(product.item_id);
  editingProductId.value = product.item_id;
  editingProductForm.value = {
    moq: condition?.moq ?? (supplier.value?.default_moq || 0),
    lead_time_days: condition?.lead_time_days ?? (supplier.value?.default_lead_time_days || 14),
    is_primary: condition?.is_primary ?? false,
  };
};

const cancelEditingProduct = () => {
  editingProductId.value = null;
  editingProductForm.value = null;
};

const saveProductCondition = async (product: Product) => {
  if (!editingProductForm.value || !supplierId.value || savingProduct.value) return;

  savingProduct.value = true;
  try {
    const condition = getProductCondition(product.item_id);
    let updated: ProductSupplierCondition;

    // If condition doesn't exist, create it; otherwise update it
    if (!condition) {
      updated = await addProductSupplier(product.item_id, {
        supplier_id: supplierId.value,
        moq: editingProductForm.value.moq,
        lead_time_days: editingProductForm.value.lead_time_days,
        is_primary: editingProductForm.value.is_primary ?? false,
      });
    } else {
      updated = await updateProductSupplier(product.item_id, supplierId.value, {
        moq: editingProductForm.value.moq,
        lead_time_days: editingProductForm.value.lead_time_days,
        is_primary: editingProductForm.value.is_primary,
      });
    }

    // Update local state
    productConditions.value.set(product.item_id, updated);

    toast.add({
      title: "Updated",
      description: `MOQ and lead time ${condition ? "updated" : "set"} for ${product.product_name}`,
      color: "success",
    });

    editingProductId.value = null;
    editingProductForm.value = null;
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;

    toast.add({
      title: "Save failed",
      description: getErrorText(err, "Failed to save product condition"),
      color: "error",
    });
  } finally {
    savingProduct.value = false;
  }
};

const resetToDefault = async (product: Product) => {
  if (!supplierId.value || !supplier.value || savingProduct.value) return;

  savingProduct.value = true;
  try {
    const condition = getProductCondition(product.item_id);

    // If no condition exists, nothing to reset
    if (!condition) {
      toast.add({
        title: "Already using defaults",
        description: `${product.product_name} is already using supplier defaults`,
        color: "info",
      });
      savingProduct.value = false;
      return;
    }

    // Update condition to match supplier defaults
    const updated = await updateProductSupplier(product.item_id, supplierId.value, {
      moq: supplier.value.default_moq || 0,
      lead_time_days: supplier.value.default_lead_time_days || 14,
    });

    // Update local state
    productConditions.value.set(product.item_id, updated);

    toast.add({
      title: "Reset to default",
      description: `${product.product_name} now uses supplier defaults`,
      color: "success",
    });
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;

    toast.add({
      title: "Reset failed",
      description: getErrorText(err, "Failed to reset to default"),
      color: "error",
    });
  } finally {
    savingProduct.value = false;
  }
};

const hasCustomValues = (itemId: string): boolean => {
  if (!supplier.value) return false;
  return (
    !isUsingSupplierDefault(itemId, "moq") || !isUsingSupplierDefault(itemId, "lead_time_days")
  );
};

const startEditing = () => {
  if (!supplier.value) return;
  editForm.value = {
    name: supplier.value.name || "",
    contact_email: supplier.value.contact_email || "",
    contact_phone: supplier.value.contact_phone || "",
    address: supplier.value.address || "",
    supplier_type: supplier.value.supplier_type || "PO",
    default_moq: supplier.value.default_moq || 0,
    default_lead_time_days: supplier.value.default_lead_time_days || 14,
    notes: supplier.value.notes || "",
  };
  // Reset modal state when starting to edit
  showApplyDialog.value = false;
  pendingChanges.value = null;
  isEditing.value = true;
};

const cancelEditing = () => {
  isEditing.value = false;
  applyToExisting.value = false;
  pendingChanges.value = null;
  showApplyDialog.value = false; // Ensure dialog is closed when canceling
  saving.value = false; // Reset saving state
};

const checkForDefaultChanges = (): {
  default_moq?: number;
  default_lead_time_days?: number;
} | null => {
  if (!supplier.value) return null;
  const changes: { default_moq?: number; default_lead_time_days?: number } = {};
  if (editForm.value.default_moq !== (supplier.value.default_moq || 0)) {
    changes.default_moq = editForm.value.default_moq;
  }
  if (editForm.value.default_lead_time_days !== (supplier.value.default_lead_time_days || 14)) {
    changes.default_lead_time_days = editForm.value.default_lead_time_days;
  }
  return Object.keys(changes).length > 0 ? changes : null;
};

const saveSupplier = async () => {
  if (!supplier.value || saving.value) return;

  // Check if defaults changed
  const defaultChanges = checkForDefaultChanges();
  if (defaultChanges) {
    pendingChanges.value = defaultChanges;
    showApplyDialog.value = true;
    return;
  }

  // No default changes, save directly
  await performSave(false);
};

const performSave = async (applyToExistingProducts: boolean) => {
  if (!supplier.value || saving.value) return;

  // Close modal first before setting saving to true
  showApplyDialog.value = false;

  saving.value = true;
  error.value = null;

  try {
    const updated = await updateSupplier(supplier.value.id, {
      name: editForm.value.name,
      contact_email: editForm.value.contact_email || undefined,
      contact_phone: editForm.value.contact_phone || undefined,
      address: editForm.value.address || undefined,
      supplier_type: editForm.value.supplier_type,
      default_moq: editForm.value.default_moq,
      default_lead_time_days: editForm.value.default_lead_time_days,
      notes: editForm.value.notes || undefined,
      apply_to_existing: applyToExistingProducts,
    });

    supplier.value = updated;
    isEditing.value = false;
    applyToExisting.value = false;
    pendingChanges.value = null;

    // Reload products to show updated values
    await loadProducts();

    // Reload product conditions in case they were affected
    await loadProductConditions();
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = getErrorText(err, "Failed to update supplier");
  } finally {
    saving.value = false;
  }
};

const badgeColorForType = (supplierType: string) => {
  if (supplierType === "PO") return "info";
  if (supplierType === "WO") return "primary";
  return "neutral";
};

const confirmApplyToExisting = () => {
  performSave(true);
};

const skipApplyToExisting = () => {
  performSave(false);
};

onMounted(async () => {
  // Reset dialog state on mount
  showApplyDialog.value = false;
  pendingChanges.value = null;
  isEditing.value = false;

  await loadSupplier();
  await loadProducts();
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div>
      <h1 class="text-3xl font-bold">Purchase Orders</h1>
      <p
        v-if="supplier"
        class="text-sm text-muted"
      >
        {{ supplier.name }}
      </p>
    </div>

    <PurchaseOrdersSectionTabs />

    <div class="flex items-center justify-end gap-2">
      <UButton
        icon="i-lucide-arrow-left"
        variant="ghost"
        @click="navigateTo('/purchase-orders/suppliers')"
      >
        Back
      </UButton>
      <UButton
        icon="i-lucide-refresh-cw"
        variant="ghost"
        :loading="loading"
        @click="loadSupplier"
      >
        Refresh
      </UButton>
    </div>

    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary"
      />
    </div>

    <UAlert
      v-else-if="error"
      color="error"
      variant="soft"
      title="Error loading supplier"
      :description="error"
    />

    <div
      v-else-if="supplier"
      class="space-y-4"
    >
      <UCard>
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-semibold">{{ supplier.name }}</h2>
              <UBadge
                :color="badgeColorForType(supplier.supplier_type)"
                variant="soft"
              >
                {{ supplier.supplier_type }}
              </UBadge>
              <UBadge
                v-if="supplier.is_synced"
                color="success"
                variant="soft"
                >Synced</UBadge
              >
            </div>
            <div class="flex items-center gap-2">
              <UButton
                v-if="!isEditing"
                icon="i-lucide-edit"
                variant="soft"
                @click="startEditing"
              >
                Edit
              </UButton>
              <UButton
                v-if="isEditing"
                icon="i-lucide-x"
                variant="soft"
                color="neutral"
                @click="cancelEditing"
              >
                Cancel
              </UButton>
              <UButton
                v-if="isEditing"
                icon="i-lucide-check"
                variant="soft"
                color="primary"
                :loading="saving"
                @click="saveSupplier"
              >
                Save
              </UButton>
              <UButton
                icon="i-lucide-receipt"
                variant="soft"
                @click="
                  navigateTo({ path: '/purchase-orders', query: { supplier_id: supplier.id } })
                "
              >
                Orders
              </UButton>
              <UButton
                icon="i-lucide-package"
                variant="soft"
                @click="navigateTo({ path: '/inventory', query: { supplier_id: supplier.id } })"
              >
                Inventory
              </UButton>
            </div>
          </div>
        </template>

        <div
          v-if="!isEditing"
          class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div>
            <div class="text-xs text-muted">Contact</div>
            <div class="text-sm mt-1">
              <div>{{ supplier.contact_email || "No email" }}</div>
              <div v-if="supplier.contact_phone">{{ supplier.contact_phone }}</div>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">External ID</div>
            <div class="text-sm mt-1">{{ supplier.external_id || "—" }}</div>
          </div>
          <div>
            <div class="text-xs text-muted">Default MOQ</div>
            <div class="text-sm mt-1 font-medium">{{ supplier.default_moq || 0 }} units</div>
            <div class="text-xs text-muted mt-1">Used when linking products to this supplier</div>
            <div
              v-if="
                supplier.effective_moq_avg !== undefined &&
                supplier.effective_moq_avg !== supplier.default_moq
              "
              class="text-xs text-primary mt-1"
            >
              Effective avg: {{ supplier.effective_moq_avg }} units
            </div>
            <div
              v-if="supplier.custom_moq_count && supplier.custom_moq_count > 0"
              class="text-xs text-blue-600 mt-1"
            >
              {{ supplier.custom_moq_count }} product{{
                supplier.custom_moq_count !== 1 ? "s" : ""
              }}
              with custom MOQ
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">Default Lead Time</div>
            <div class="text-sm mt-1 font-medium">
              {{ supplier.default_lead_time_days || 14 }} days
            </div>
            <div class="text-xs text-muted mt-1">Used when linking products to this supplier</div>
            <div
              v-if="
                supplier.effective_lead_time_avg !== undefined &&
                supplier.effective_lead_time_avg !== supplier.default_lead_time_days
              "
              class="text-xs text-primary mt-1"
            >
              Effective avg: {{ supplier.effective_lead_time_avg }} days
            </div>
            <div
              v-if="supplier.custom_lead_time_count && supplier.custom_lead_time_count > 0"
              class="text-xs text-blue-600 mt-1"
            >
              {{ supplier.custom_lead_time_count }} product{{
                supplier.custom_lead_time_count !== 1 ? "s" : ""
              }}
              with custom lead time
            </div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Address</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ supplier.address || "—" }}</div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Notes</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ supplier.notes || "—" }}</div>
          </div>
        </div>

        <div
          v-else
          class="p-4 space-y-4"
        >
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UFormField
              label="Name"
              name="name"
              required
            >
              <UInput
                v-model="editForm.name"
                placeholder="Supplier name"
              />
            </UFormField>
            <UFormField
              label="Supplier Type"
              name="supplier_type"
            >
              <USelectMenu
                v-model="editForm.supplier_type"
                :options="['PO', 'WO']"
              />
            </UFormField>
            <UFormField
              label="Contact Email"
              name="contact_email"
            >
              <UInput
                v-model="editForm.contact_email"
                type="email"
                placeholder="email@example.com"
              />
            </UFormField>
            <UFormField
              label="Contact Phone"
              name="contact_phone"
            >
              <UInput
                v-model="editForm.contact_phone"
                placeholder="+1 234 567 8900"
              />
            </UFormField>
            <UFormField
              label="Default MOQ"
              name="default_moq"
            >
              <UInput
                v-model.number="editForm.default_moq"
                type="number"
                min="0"
                placeholder="0"
              />
              <template #hint> Used when linking products to this supplier </template>
            </UFormField>
            <UFormField
              label="Default Lead Time (Days)"
              name="default_lead_time_days"
            >
              <UInput
                v-model.number="editForm.default_lead_time_days"
                type="number"
                min="0"
                placeholder="14"
              />
              <template #hint> Used when linking products to this supplier </template>
            </UFormField>
            <UFormField
              label="Address"
              name="address"
              class="md:col-span-2"
            >
              <UTextarea
                v-model="editForm.address"
                placeholder="Street address, City, State, ZIP"
                :rows="3"
              />
            </UFormField>
            <UFormField
              label="Notes"
              name="notes"
              class="md:col-span-2"
            >
              <UTextarea
                v-model="editForm.notes"
                placeholder="Additional notes..."
                :rows="3"
              />
            </UFormField>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">
              Products
              <span
                v-if="productsTotal > 0"
                class="text-sm font-normal text-muted"
              >
                ({{ productsTotal }} total)
              </span>
            </h2>
            <UButton
              icon="i-lucide-refresh-cw"
              variant="ghost"
              :loading="productsLoading"
              @click="() => loadProducts()"
            >
              Refresh
            </UButton>
          </div>
        </template>

        <div
          v-if="productsLoading"
          class="p-6 flex items-center justify-center"
        >
          <UIcon
            name="i-lucide-loader-2"
            class="w-6 h-6 animate-spin text-primary"
          />
        </div>
        <UAlert
          v-else-if="productsError"
          color="error"
          variant="soft"
          title="Error loading products"
          :description="productsError"
        />
        <div
          v-else-if="products.length === 0"
          class="p-6 text-center text-muted"
        >
          No products linked.
        </div>
        <div
          v-else
          class="divide-y"
        >
          <div
            v-for="p in products"
            :key="p.item_id"
            class="py-3 space-y-2"
          >
            <div class="flex items-center justify-between gap-4">
              <div class="min-w-0 flex-1">
                <div class="font-medium truncate">{{ p.product_name }}</div>
                <div class="text-xs text-muted">
                  {{ p.item_id }} · {{ p.category || "Uncategorized" }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <UButton
                  v-if="editingProductId !== p.item_id && hasCustomValues(p.item_id)"
                  size="sm"
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-rotate-ccw"
                  :disabled="savingProduct"
                  @click="resetToDefault(p)"
                >
                  Reset to Default
                </UButton>
                <UButton
                  v-if="editingProductId !== p.item_id"
                  size="sm"
                  variant="soft"
                  icon="i-lucide-edit"
                  @click="startEditingProduct(p)"
                >
                  {{ getProductCondition(p.item_id) ? "Edit MOQ" : "Set MOQ" }}
                </UButton>
                <UButton
                  size="sm"
                  variant="soft"
                  @click="navigateTo({ path: '/inventory', query: { item: p.item_id } })"
                >
                  View
                </UButton>
              </div>
            </div>

            <!-- Display MOQ and Lead Time -->
            <div
              v-if="editingProductId !== p.item_id"
              class="flex items-center gap-4 text-sm"
            >
              <div class="flex items-center gap-2">
                <span class="text-muted">MOQ:</span>
                <span
                  class="font-medium"
                  :class="isUsingSupplierDefault(p.item_id, 'moq') ? 'text-muted' : 'text-primary'"
                >
                  {{ getProductCondition(p.item_id)?.moq ?? (supplier?.default_moq || 0) }}
                </span>
                <UBadge
                  v-if="!isUsingSupplierDefault(p.item_id, 'moq')"
                  color="info"
                  variant="soft"
                  size="xs"
                >
                  Custom
                </UBadge>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-muted">Lead Time:</span>
                <span
                  class="font-medium"
                  :class="
                    isUsingSupplierDefault(p.item_id, 'lead_time_days')
                      ? 'text-muted'
                      : 'text-primary'
                  "
                >
                  {{
                    getProductCondition(p.item_id)?.lead_time_days ??
                    (supplier?.default_lead_time_days || 14)
                  }}
                  days
                </span>
                <UBadge
                  v-if="!isUsingSupplierDefault(p.item_id, 'lead_time_days')"
                  color="info"
                  variant="soft"
                  size="xs"
                >
                  Custom
                </UBadge>
              </div>
              <div
                v-if="getProductCondition(p.item_id)?.is_primary"
                class="flex items-center gap-2"
              >
                <UBadge
                  color="success"
                  variant="soft"
                  size="xs"
                >
                  Primary Supplier
                </UBadge>
              </div>
            </div>

            <!-- Edit Form -->
            <div
              v-else
              class="p-3 bg-muted rounded-lg space-y-3"
            >
              <div class="grid grid-cols-2 gap-3">
                <UFormField
                  label="MOQ"
                  name="moq"
                >
                  <UInput
                    v-model.number="editingProductForm!.moq"
                    type="number"
                    min="0"
                    size="sm"
                  />
                  <template #hint> Supplier default: {{ supplier?.default_moq || 0 }} </template>
                </UFormField>
                <UFormField
                  label="Lead Time (Days)"
                  name="lead_time_days"
                >
                  <UInput
                    v-model.number="editingProductForm!.lead_time_days"
                    type="number"
                    min="0"
                    size="sm"
                  />
                  <template #hint>
                    Supplier default: {{ supplier?.default_lead_time_days || 14 }}
                  </template>
                </UFormField>
              </div>
              <UFormField
                label="Primary Supplier"
                name="is_primary"
              >
                <UCheckbox
                  v-model="editingProductForm!.is_primary"
                  label="Set as primary supplier for this product"
                />
                <template #hint>
                  Primary supplier is used for MOQ/lead time calculations. Only one supplier can be
                  primary per product.
                </template>
              </UFormField>
              <div class="flex items-center justify-between">
                <UButton
                  v-if="hasCustomValues(p.item_id)"
                  size="sm"
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-rotate-ccw"
                  :disabled="savingProduct"
                  @click="resetToDefault(p)"
                >
                  Reset to Default
                </UButton>
                <div v-else></div>
                <div class="flex items-center gap-2">
                  <UButton
                    size="sm"
                    variant="ghost"
                    :disabled="savingProduct"
                    @click="cancelEditingProduct"
                  >
                    Cancel
                  </UButton>
                  <UButton
                    size="sm"
                    color="primary"
                    :loading="savingProduct"
                    @click="saveProductCondition(p)"
                  >
                    Save
                  </UButton>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div
          v-if="productsTotalPages > 1"
          class="mt-4 pt-4 border-t flex items-center justify-between"
        >
          <div class="text-sm text-muted">
            Showing {{ (productsPage - 1) * productsPageSize + 1 }} to
            {{ Math.min(productsPage * productsPageSize, productsTotal) }} of
            {{ productsTotal }} products
          </div>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-chevron-left"
              variant="ghost"
              size="sm"
              :disabled="productsPage <= 1 || productsLoading"
              @click="goToPage(productsPage - 1)"
            >
              Previous
            </UButton>
            <div class="flex items-center gap-1">
              <template
                v-for="page in getVisiblePages()"
                :key="page"
              >
                <span
                  v-if="page === -1"
                  class="px-2 text-sm text-muted"
                >
                  ...
                </span>
                <UButton
                  v-else
                  :variant="page === productsPage ? 'solid' : 'ghost'"
                  size="sm"
                  :disabled="productsLoading"
                  @click="goToPage(page)"
                >
                  {{ page }}
                </UButton>
              </template>
            </div>
            <UButton
              icon="i-lucide-chevron-right"
              icon-position="right"
              variant="ghost"
              size="sm"
              :disabled="productsPage >= productsTotalPages || productsLoading"
              @click="goToPage(productsPage + 1)"
            >
              Next
            </UButton>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Apply to Existing Products Dialog -->
    <UModal
      v-model:open="showApplyDialog"
      :dismissible="!saving"
      title="Apply Default Changes to Existing Products?"
      :ui="{ footer: 'justify-end' }"
    >
      <template #body>
        <div class="space-y-4">
          <p class="text-sm text-muted">
            You've changed the supplier defaults. Would you like to apply these changes to existing
            products?
          </p>

          <div
            v-if="pendingChanges"
            class="p-3 bg-muted rounded-lg space-y-2"
          >
            <div
              v-if="pendingChanges.default_moq !== undefined"
              class="text-sm"
            >
              <span class="font-medium">MOQ:</span>
              {{ supplier?.default_moq || 0 }} → {{ pendingChanges.default_moq }}
            </div>
            <div
              v-if="pendingChanges.default_lead_time_days !== undefined"
              class="text-sm"
            >
              <span class="font-medium">Lead Time:</span>
              {{ supplier?.default_lead_time_days || 14 }} →
              {{ pendingChanges.default_lead_time_days }} days
            </div>
          </div>

          <UAlert
            color="warning"
            variant="soft"
            title="Note"
            description="This will only update products that are currently using the supplier defaults. Products with explicit overrides will remain unchanged."
          />
        </div>
      </template>

      <template #footer>
        <UButton
          variant="ghost"
          :disabled="saving"
          @click="skipApplyToExisting"
        >
          Skip
        </UButton>
        <UButton
          color="primary"
          :loading="saving"
          @click="confirmApplyToExisting"
        >
          Apply to Existing Products
        </UButton>
      </template>
    </UModal>
  </div>
</template>
