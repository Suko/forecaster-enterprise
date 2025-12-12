<script setup lang="ts">
import type { Supplier } from "~/types/supplier";
import type { Product, ProductListResponse } from "~/types/product";

definePageMeta({
  layout: "dashboard",
});

const route = useRoute();
const supplierId = computed(() => String(route.params.id || ""));

const { fetchSupplier, updateSupplier } = useSuppliers();
const { handleAuthError } = useAuthError();

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

const badgeColorForType = (supplierType: string) => {
  if (supplierType === "PO") return "blue";
  if (supplierType === "WO") return "purple";
  return "gray";
};

const loadSupplier = async () => {
  if (!supplierId.value) return;
  loading.value = true;
  error.value = null;
  try {
    supplier.value = await fetchSupplier(supplierId.value);
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load supplier";
  } finally {
    loading.value = false;
  }
};

const loadProducts = async () => {
  if (!supplierId.value) return;
  productsLoading.value = true;
  productsError.value = null;
  try {
    const res = await $fetch<ProductListResponse>("/api/products", {
      query: {
        page: 1,
        page_size: 50,
        supplier_id: supplierId.value,
      },
    });
    products.value = res.items || [];
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    productsError.value = err.message || "Failed to load products";
  } finally {
    productsLoading.value = false;
  }
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
  isEditing.value = true;
};

const cancelEditing = () => {
  isEditing.value = false;
  applyToExisting.value = false;
  pendingChanges.value = null;
  showApplyDialog.value = false;  // Ensure dialog is closed when canceling
};

const checkForDefaultChanges = (): { default_moq?: number; default_lead_time_days?: number } | null => {
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
    showApplyDialog.value = false;

    // Reload products to show updated values
    await loadProducts();
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to update supplier";
  } finally {
    saving.value = false;
  }
};

const confirmApplyToExisting = () => {
  showApplyDialog.value = false;
  performSave(true);
};

const skipApplyToExisting = () => {
  showApplyDialog.value = false;
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
                color="green"
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
                color="gray"
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
            <div class="text-sm mt-1 font-medium">
              {{ supplier.default_moq || 0 }} units
            </div>
            <div class="text-xs text-muted mt-1">
              Used when linking products to this supplier
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">Default Lead Time</div>
            <div class="text-sm mt-1 font-medium">
              {{ supplier.default_lead_time_days || 14 }} days
            </div>
            <div class="text-xs text-muted mt-1">
              Used when linking products to this supplier
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
            <UFormGroup
              label="Name"
              required
            >
              <UInput
                v-model="editForm.name"
                placeholder="Supplier name"
              />
            </UFormGroup>
            <UFormGroup label="Supplier Type">
              <USelectMenu
                v-model="editForm.supplier_type"
                :options="['PO', 'WO']"
              />
            </UFormGroup>
            <UFormGroup label="Contact Email">
              <UInput
                v-model="editForm.contact_email"
                type="email"
                placeholder="email@example.com"
              />
            </UFormGroup>
            <UFormGroup label="Contact Phone">
              <UInput
                v-model="editForm.contact_phone"
                placeholder="+1 234 567 8900"
              />
            </UFormGroup>
            <UFormGroup label="Default MOQ">
              <UInput
                v-model.number="editForm.default_moq"
                type="number"
                min="0"
                placeholder="0"
              />
              <template #hint>
                Used when linking products to this supplier
              </template>
            </UFormGroup>
            <UFormGroup label="Default Lead Time (Days)">
              <UInput
                v-model.number="editForm.default_lead_time_days"
                type="number"
                min="0"
                placeholder="14"
              />
              <template #hint>
                Used when linking products to this supplier
              </template>
            </UFormGroup>
            <UFormGroup
              label="Address"
              class="md:col-span-2"
            >
              <UTextarea
                v-model="editForm.address"
                placeholder="Street address, City, State, ZIP"
                :rows="3"
              />
            </UFormGroup>
            <UFormGroup
              label="Notes"
              class="md:col-span-2"
            >
              <UTextarea
                v-model="editForm.notes"
                placeholder="Additional notes..."
                :rows="3"
              />
            </UFormGroup>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Products (first 50)</h2>
            <UButton
              icon="i-lucide-refresh-cw"
              variant="ghost"
              :loading="productsLoading"
              @click="loadProducts"
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
            class="py-3 flex items-center justify-between gap-4"
          >
            <div class="min-w-0">
              <div class="font-medium truncate">{{ p.product_name }}</div>
              <div class="text-xs text-muted">
                {{ p.item_id }} · {{ p.category || "Uncategorized" }}
              </div>
            </div>
            <UButton
              size="sm"
              variant="soft"
              @click="navigateTo({ path: '/inventory', query: { item: p.item_id } })"
            >
              View
            </UButton>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Apply to Existing Products Dialog -->
    <UModal
      v-if="showApplyDialog"
      v-model="showApplyDialog"
      :prevent-close="saving"
      :ui="{ width: 'sm:max-w-md' }"
      @close="showApplyDialog = false"
    >
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Apply Default Changes to Existing Products?</h3>
        </template>

        <div class="space-y-4">
          <p class="text-sm text-muted">
            You've changed the supplier defaults. Would you like to apply these changes to existing products?
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
              {{ supplier?.default_lead_time_days || 14 }} → {{ pendingChanges.default_lead_time_days }} days
            </div>
          </div>

          <UAlert
            color="amber"
            variant="soft"
            title="Note"
            description="This will only update products that are currently using the supplier defaults. Products with explicit overrides will remain unchanged."
          />
        </div>

        <template #footer>
          <div class="flex items-center justify-end gap-2">
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
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>
