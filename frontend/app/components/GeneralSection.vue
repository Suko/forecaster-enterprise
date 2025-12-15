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
        <UFormField
          label="Company Name"
          name="companyName"
        >
          <UInput
            v-model="formState.companyName"
            placeholder="Enter company name"
          />
        </UFormField>

        <UFormField
          label="Timezone"
          name="timezone"
        >
          <USelect
            v-model="formState.timezone"
            :options="timezoneOptions"
            placeholder="Select timezone"
          />
        </UFormField>

        <UFormField
          label="Language"
          name="language"
        >
          <USelect
            v-model="formState.language"
            :options="languageOptions"
            placeholder="Select language"
          />
        </UFormField>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <UButton> Save Changes </UButton>
        </div>
      </template>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Appearance</h3>
      </template>

      <div class="space-y-4">
        <UFormField
          label="Theme"
          name="theme"
          description="Choose your preferred color scheme"
        >
          <div class="flex gap-2">
            <UButton
              variant="outline"
              :color="themePreference === 'light' ? 'primary' : 'neutral'"
              @click="handleThemeChange('light')"
            >
              <UIcon
                name="i-lucide-sun"
                class="size-4 mr-2"
              />
              Light
            </UButton>
            <UButton
              variant="outline"
              :color="themePreference === 'dark' ? 'primary' : 'neutral'"
              @click="handleThemeChange('dark')"
            >
              <UIcon
                name="i-lucide-moon"
                class="size-4 mr-2"
              />
              Dark
            </UButton>
            <UButton
              variant="outline"
              :color="themePreference === 'system' ? 'primary' : 'neutral'"
              @click="handleThemeChange('system')"
            >
              <UIcon
                name="i-lucide-monitor"
                class="size-4 mr-2"
              />
              System
            </UButton>
          </div>
        </UFormField>

        <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <UIcon
            :name="themeIcon"
            class="size-4"
          />
          <span>Current theme: {{ currentThemeLabel }}</span>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
// Color mode (dark/light theme)
const colorMode = useColorMode();

const formState = reactive({
  companyName: "",
  timezone: "UTC",
  language: "en",
});

const timezoneOptions = [
  { label: "UTC", value: "UTC" },
  { label: "America/New_York", value: "America/New_York" },
  { label: "America/Los_Angeles", value: "America/Los_Angeles" },
  { label: "Europe/London", value: "Europe/London" },
  { label: "Europe/Paris", value: "Europe/Paris" },
  { label: "Asia/Tokyo", value: "Asia/Tokyo" },
];

const languageOptions = [
  { label: "English", value: "en" },
  { label: "Spanish", value: "es" },
  { label: "French", value: "fr" },
  { label: "German", value: "de" },
];

// Theme options
const themeOptions = [
  { label: "Light", value: "light" },
  { label: "Dark", value: "dark" },
  { label: "System", value: "system" },
];

// Theme preference (syncs with colorMode)
const themePreference = ref(colorMode.preference);

// Watch for changes from colorMode (external changes)
watch(
  () => colorMode.preference,
  (newValue) => {
    themePreference.value = newValue;
  },
  { immediate: true }
);

const handleThemeChange = (value: string) => {
  colorMode.preference = value;
  themePreference.value = value;
};

const currentThemeLabel = computed(() => {
  if (colorMode.preference === "system") {
    return `System (${colorMode.value === "dark" ? "Dark" : "Light"})`;
  }
  return colorMode.value === "dark" ? "Dark" : "Light";
});

const themeIcon = computed(() => {
  return colorMode.value === "dark" ? "i-lucide-moon" : "i-lucide-sun";
});
</script>
