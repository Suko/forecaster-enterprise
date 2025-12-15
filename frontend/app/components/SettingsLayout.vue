<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Settings</h1>

    <UTabs
      :items="tabs"
      :default-value="activeTab"
      variant="link"
      @update:model-value="handleTabChange"
    >
      <template #list-trailing>
        <UButton
          to="https://ui.nuxt.com/docs/getting-started/installation/nuxt"
          external
          variant="ghost"
          icon="i-lucide-external-link"
          trailing
          class="ml-auto"
        >
          Documentation
        </UButton>
      </template>

      <template #general>
        <slot name="general">
          <GeneralSection />
        </slot>
      </template>

      <template #inventory>
        <slot name="inventory">
          <InventorySection />
        </slot>
      </template>

      <template #locations>
        <slot name="locations">
          <LocationsSection />
        </slot>
      </template>

      <template #users>
        <slot name="users">
          <UsersSection />
        </slot>
      </template>

      <template #notifications>
        <slot name="notifications">
          <div class="py-8">
            <p class="text-gray-500 dark:text-gray-400">Notifications settings coming soon...</p>
          </div>
        </slot>
      </template>

      <template #forecasting>
        <slot name="forecasting">
          <ForecastingAssumptionsSection />
        </slot>
      </template>

      <template #security>
        <slot name="security">
          <div class="py-8">
            <p class="text-gray-500 dark:text-gray-400">Security settings coming soon...</p>
          </div>
        </slot>
      </template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
import type { TabsItem } from "@nuxt/ui";

const route = useRoute();
const router = useRouter();

const tabs: TabsItem[] = [
  {
    label: "General",
    value: "general",
    slot: "general",
  },
  {
    label: "Inventory",
    value: "inventory",
    slot: "inventory",
  },
  {
    label: "Locations",
    value: "locations",
    slot: "locations",
  },
  {
    label: "Forecasting",
    value: "forecasting",
    slot: "forecasting",
  },
  {
    label: "Users",
    value: "users",
    slot: "users",
  },
  {
    label: "Notifications",
    value: "notifications",
    slot: "notifications",
  },
  {
    label: "Security",
    value: "security",
    slot: "security",
  },
];

const activeTab = computed(() => {
  if (route.path === "/settings" || route.path === "/settings/") {
    return "general";
  }
  if (route.path === "/settings/inventory") {
    return "inventory";
  }
  if (route.path === "/settings/locations") {
    return "locations";
  }
  if (route.path === "/settings/forecasting") {
    return "forecasting";
  }
  if (route.path === "/settings/users") {
    return "users";
  }
  if (route.path === "/settings/notifications") {
    return "notifications";
  }
  if (route.path === "/settings/security") {
    return "security";
  }
  return "general";
});

const handleTabChange = (value: string | number) => {
  const tabValue = String(value);
  if (tabValue === "general") {
    router.push("/settings");
  } else {
    router.push(`/settings/${tabValue}`);
  }
};
</script>
