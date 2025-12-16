<template>
  <div class="space-y-6">
    <div class="flex justify-between items-start">
      <div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Locations</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Manage warehouse and store locations.
        </p>
      </div>
      <UButton
        icon="i-lucide-plus"
        @click="openCreateModal"
      >
        Add Location
      </UButton>
    </div>

    <UInput
      v-model="searchQuery"
      icon="i-lucide-search"
      placeholder="Search locations"
      class="w-full"
    />

    <div class="space-y-1">
      <div
        v-for="location in filteredLocations"
        :key="location.id"
        class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <div class="flex-1 min-w-0">
            <div class="font-medium text-gray-900 dark:text-white">
              {{ location.name }}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">
              <span v-if="location.city || location.country">
                {{ [location.city, location.country].filter(Boolean).join(", ") }}
              </span>
              <span v-else-if="location.address">{{ location.address }}</span>
              <span
                v-else
                class="text-gray-400"
                >No address</span
              >
            </div>
            <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              ID: {{ location.location_id }}
              <span
                v-if="location.is_synced"
                class="ml-2 text-blue-500"
                >(Synced)</span
              >
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <UDropdownMenu :items="getLocationActions(location)">
            <UButton
              icon="i-lucide-more-vertical"
              color="gray"
              variant="ghost"
              size="sm"
            />
          </UDropdownMenu>
        </div>
      </div>

      <div
        v-if="loading"
        class="flex justify-center py-8"
      >
        <UIcon
          name="i-lucide-loader-2"
          class="size-6 animate-spin text-gray-400"
        />
      </div>

      <div
        v-if="!loading && filteredLocations.length === 0"
        class="text-center py-12"
      >
        <p class="text-gray-500 dark:text-gray-400">
          {{ searchQuery ? "No locations found" : "No locations yet" }}
        </p>
      </div>
    </div>

    <UModal
      v-model:open="showModal"
      :ui="{ width: 'sm:max-w-md' }"
    >
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">
              {{ editingLocation ? "Edit Location" : "Add Location" }}
            </h3>
          </template>

          <UForm
            ref="formRef"
            :state="formState"
            @submit="handleSubmit"
          >
            <UFormField
              label="Location ID"
              name="location_id"
              :disabled="editingLocation !== null"
            >
              <UInput
                v-model="formState.location_id"
                placeholder="e.g., WAREHOUSE_01"
                :disabled="editingLocation !== null"
              />
              <template #hint>
                Unique identifier for this location (cannot be changed after creation)
              </template>
            </UFormField>

            <UFormField
              label="Name"
              name="name"
            >
              <UInput
                v-model="formState.name"
                placeholder="e.g., Main Warehouse"
              />
            </UFormField>

            <UFormField
              label="Address"
              name="address"
            >
              <UInput
                v-model="formState.address"
                placeholder="Street address"
              />
            </UFormField>

            <div class="grid grid-cols-2 gap-4">
              <UFormField
                label="City"
                name="city"
              >
                <UInput
                  v-model="formState.city"
                  placeholder="City"
                />
              </UFormField>

              <UFormField
                label="Country"
                name="country"
              >
                <UInput
                  v-model="formState.country"
                  placeholder="Country"
                />
              </UFormField>
            </div>
          </UForm>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                variant="ghost"
                @click="cancelEditing"
              >
                Cancel
              </UButton>
              <UButton
                :loading="saving"
                @click="handleSubmit"
              >
                {{ editingLocation ? "Save" : "Create" }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <UModal
      v-model:open="showDeleteModal"
      :ui="{ width: 'sm:max-w-md' }"
    >
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">Delete Location</h3>
          </template>

          <p class="text-gray-600 dark:text-gray-400">
            Are you sure you want to delete "{{ locationToDelete?.name }}"? This action cannot be
            undone.
            <span
              v-if="locationToDelete?.is_synced"
              class="block mt-2 text-sm text-red-600 dark:text-red-400"
            >
              Note: Synced locations cannot be deleted from the app.
            </span>
          </p>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                variant="ghost"
                @click="showDeleteModal = false"
              >
                Cancel
              </UButton>
              <UButton
                color="red"
                :loading="deleting"
                @click="confirmDelete"
              >
                Delete
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useLocations } from "~/composables/useLocations";
import { useAuthError } from "~/composables/useAuthError";
import type { Location, LocationCreate, LocationUpdate } from "~/types/location";
import { logger } from "~~/server/utils/logger";

const toast = useToast();

const { fetchLocations, createLocation, updateLocation, deleteLocation } = useLocations();
const { handleAuthError } = useAuthError();

const locations = ref<Location[]>([]);
const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const searchQuery = ref("");
const showModal = ref(false);
const showDeleteModal = ref(false);
const editingLocation = ref<Location | null>(null);
const locationToDelete = ref<Location | null>(null);
const formRef = ref<any>(null);

const formState = ref<LocationCreate>({
  location_id: "",
  name: "",
  address: null,
  city: null,
  country: null,
});

const filteredLocations = computed(() => {
  if (!searchQuery.value) return locations.value;
  const query = searchQuery.value.toLowerCase();
  return locations.value.filter(
    (loc) =>
      loc.name.toLowerCase().includes(query) ||
      loc.location_id.toLowerCase().includes(query) ||
      loc.city?.toLowerCase().includes(query) ||
      loc.country?.toLowerCase().includes(query)
  );
});

const getLocationActions = (location: Location) => {
  const actions = [];
  if (!location.is_synced) {
    actions.push({
      label: "Edit",
      icon: "i-lucide-pencil",
      click: () => openEditModal(location),
    });
    actions.push({
      label: "Delete",
      icon: "i-lucide-trash-2",
      click: () => openDeleteModal(location),
    });
  } else {
    actions.push({
      label: "View",
      icon: "i-lucide-eye",
      click: () => openEditModal(location),
    });
  }
  return actions;
};

const loadLocations = async () => {
  loading.value = true;
  try {
    const result = await fetchLocations({ pageSize: 1000 });
    locations.value = result.items;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      logger.error("Failed to load locations", { error: err });
    }
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  editingLocation.value = null;
  formState.value = {
    location_id: "",
    name: "",
    address: null,
    city: null,
    country: null,
  };
  showModal.value = true;
};

const openEditModal = (location: Location) => {
  editingLocation.value = location;
  formState.value = {
    location_id: location.location_id,
    name: location.name,
    address: location.address || null,
    city: location.city || null,
    country: location.country || null,
  };
  showModal.value = true;
};

const openDeleteModal = (location: Location) => {
  locationToDelete.value = location;
  showDeleteModal.value = true;
};

const cancelEditing = () => {
  showModal.value = false;
  editingLocation.value = null;
  formState.value = {
    location_id: "",
    name: "",
    address: null,
    city: null,
    country: null,
  };
};

const handleSubmit = async () => {
  if (!formState.value.name || !formState.value.location_id) {
    toast.add({
      title: "Validation Error",
      description: "Location ID and Name are required",
      color: "red",
    });
    return;
  }

  saving.value = true;

  try {
    if (editingLocation.value) {
      const updateData: LocationUpdate = {
        name: formState.value.name,
        address: formState.value.address || null,
        city: formState.value.city || null,
        country: formState.value.country || null,
      };
      await updateLocation(editingLocation.value.id, updateData);
      toast.add({
        title: "Location updated",
        description: "Location has been updated successfully.",
      });
    } else {
      const createData: LocationCreate = {
        location_id: formState.value.location_id,
        name: formState.value.name,
        address: formState.value.address || null,
        city: formState.value.city || null,
        country: formState.value.country || null,
      };
      await createLocation(createData);
      toast.add({
        title: "Location created",
        description: "Location has been created successfully.",
      });
    }
    await loadLocations();
    cancelEditing();
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      toast.add({
        title: "Error",
        description: err.data?.detail || err.message || "Failed to save location",
        color: "red",
      });
    }
  } finally {
    saving.value = false;
  }
};

const confirmDelete = async () => {
  if (!locationToDelete.value) return;

  deleting.value = true;

  try {
    await deleteLocation(locationToDelete.value.id);
    toast.add({
      title: "Location deleted",
      description: "Location has been deleted successfully.",
    });
    await loadLocations();
    showDeleteModal.value = false;
    locationToDelete.value = null;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      toast.add({
        title: "Error",
        description: err.data?.detail || err.message || "Failed to delete location",
        color: "red",
      });
    }
  } finally {
    deleting.value = false;
  }
};

onMounted(() => {
  loadLocations();
});
</script>
