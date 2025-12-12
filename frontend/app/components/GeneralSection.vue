<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">General</h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Manage your account settings and preferences.
      </p>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Account Information</h3>
      </template>

      <div class="space-y-4">
        <UFormField label="Company Name" name="companyName">
          <UInput
            v-model="formState.companyName"
            placeholder="Enter company name"
          />
        </UFormField>

        <UFormField label="Timezone" name="timezone">
          <USelect
            v-model="formState.timezone"
            :options="timezoneOptions"
            placeholder="Select timezone"
          />
        </UFormField>

        <UFormField label="Language" name="language">
          <USelect
            v-model="formState.language"
            :options="languageOptions"
            placeholder="Select language"
          />
        </UFormField>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <UButton>
            Save Changes
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const formState = reactive({
  companyName: "",
  timezone: "UTC",
  language: "en"
});

const timezoneOptions = [
  { label: "UTC", value: "UTC" },
  { label: "America/New_York", value: "America/New_York" },
  { label: "America/Los_Angeles", value: "America/Los_Angeles" },
  { label: "Europe/London", value: "Europe/London" },
  { label: "Europe/Paris", value: "Europe/Paris" },
  { label: "Asia/Tokyo", value: "Asia/Tokyo" }
];

const languageOptions = [
  { label: "English", value: "en" },
  { label: "Spanish", value: "es" },
  { label: "French", value: "fr" },
  { label: "German", value: "de" }
];
</script>

