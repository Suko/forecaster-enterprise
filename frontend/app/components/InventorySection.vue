<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Inventory Settings</h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Configure inventory thresholds, safety buffers, and stock management rules.
      </p>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Safety & Thresholds</h3>
      </template>

      <div class="space-y-4">
        <UFormField
          label="Safety Buffer (Days)"
          name="safety_buffer_days"
        >
          <UInput
            v-model.number="formState.safety_buffer_days"
            type="number"
            min="0"
            placeholder="7"
          />
          <template #hint>
            Extra days added to lead time to account for delays and demand variability. Used as
            default for all products unless overridden.
          </template>
        </UFormField>

        <UFormField
          label="Understocked Threshold (Days)"
          name="understocked_threshold"
        >
          <UInput
            v-model.number="formState.understocked_threshold"
            type="number"
            min="0"
            placeholder="14"
          />
          <template #hint>
            Products with DIR (Days of Inventory Remaining) below this threshold are considered
            understocked.
          </template>
        </UFormField>

        <UFormField
          label="Overstocked Threshold (Days)"
          name="overstocked_threshold"
        >
          <UInput
            v-model.number="formState.overstocked_threshold"
            type="number"
            min="0"
            placeholder="90"
          />
          <template #hint>
            Products with DIR above this threshold are considered overstocked.
          </template>
        </UFormField>

        <UFormField
          label="Dead Stock Threshold (Days)"
          name="dead_stock_days"
        >
          <UInput
            v-model.number="formState.dead_stock_days"
            type="number"
            min="0"
            placeholder="90"
          />
          <template #hint>
            Products with no sales for this many days are considered dead stock.
          </template>
        </UFormField>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <UButton
            :loading="saving"
            @click="saveSettings"
          >
            Save Changes
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { logger } from "~~/server/utils/logger";

const { fetchSettings, updateSettings } = useSettings();
const { handleAuthError } = useAuthError();

const formState = reactive({
  safety_buffer_days: 7,
  understocked_threshold: 14,
  overstocked_threshold: 90,
  dead_stock_days: 90,
});

const saving = ref(false);
const loading = ref(false);

const loadSettings = async () => {
  loading.value = true;
  try {
    const settings = await fetchSettings();
    formState.safety_buffer_days = settings.safety_buffer_days;
    formState.understocked_threshold = settings.understocked_threshold;
    formState.overstocked_threshold = settings.overstocked_threshold;
    formState.dead_stock_days = settings.dead_stock_days;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      logger.error("Failed to load settings", { error: err });
    }
  } finally {
    loading.value = false;
  }
};

const saveSettings = async () => {
  if (saving.value) return;

  saving.value = true;
  const toast = useToast();
  try {
    await updateSettings({
      safety_buffer_days: formState.safety_buffer_days,
      understocked_threshold: formState.understocked_threshold,
      overstocked_threshold: formState.overstocked_threshold,
      dead_stock_days: formState.dead_stock_days,
    });
    toast.add({
      title: "Settings saved",
      description: "Inventory settings have been updated successfully.",
    });
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      toast.add({
        title: "Error",
        description: err.message || "Failed to save settings",
        color: "red",
      });
    }
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadSettings();
});
</script>
