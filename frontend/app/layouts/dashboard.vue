<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";

const { user } = useUserSession();
const route = useRoute();

const mainMenuItems = computed<NavigationMenuItem[]>(() => [
  {
    label: "Dashboard",
    icon: "i-lucide-layout-dashboard",
    to: "/dashboard",
    active: route.path === "/dashboard",
  },
  {
    label: "Inventory",
    icon: "i-lucide-package",
    to: "/inventory",
    active: route.path.startsWith("/inventory"),
  },
  {
    label: "Recommendations",
    icon: "i-lucide-lightbulb",
    to: "/recommendations",
    active: route.path.startsWith("/recommendations"),
  },
  {
    label: "Purchase Orders",
    icon: "i-lucide-receipt",
    to: "/purchase-orders/draft",
    active: route.path.startsWith("/purchase-orders"),
  },
]);

const settingsItem = ref<NavigationMenuItem>({
  label: "Settings",
  icon: "i-lucide-settings",
  active: false,
  defaultOpen: false,
  children: [
    {
      label: "General",
      icon: "i-lucide-settings-2",
      to: "/settings",
      active: false,
    },
    {
      label: "Inventory",
      icon: "i-lucide-package",
      to: "/settings/inventory",
      active: false,
    },
    {
      label: "Locations",
      icon: "i-lucide-map-pin",
      to: "/settings/locations",
      active: false,
    },
    {
      label: "Users",
      icon: "i-lucide-users",
      to: "/settings/users",
      active: false,
    },
    {
      label: "Notifications",
      icon: "i-lucide-bell",
      to: "/settings/notifications",
      active: false,
    },
    {
      label: "Security",
      icon: "i-lucide-shield",
      to: "/settings/security",
      active: false,
    },
  ],
});

watch(
  () => route.path,
  (path) => {
    settingsItem.value.active = path.startsWith("/settings");
    settingsItem.value.defaultOpen = path.startsWith("/settings");
    if (settingsItem.value.children) {
      settingsItem.value.children.forEach((child) => {
        if (path === "/settings" || path === "/settings/") {
          child.active = child.to === "/settings";
        } else {
          child.active = path === child.to;
        }
      });
    }
  },
  { immediate: true }
);

const otherMenuItems = computed<NavigationMenuItem[]>(() => [settingsItem.value]);

const { clear: clearSession } = useUserSession();

const handleLogout = async () => {
  await clearSession();
  await navigateTo("/login");
};

const pageTitle = computed(() => {
  if (route.path.startsWith("/inventory")) return "Inventory";
  if (route.path.startsWith("/recommendations")) return "Recommendations";
  if (route.path.startsWith("/purchase-orders")) return "Purchase Orders";
  if (route.path.startsWith("/settings")) return "Settings";
  return "Dashboard";
});

// Cart badge with animated count
const cartCount = ref(0);
const { fetchCart } = useOrderPlanningCart();
const toast = useToast();

// Demo cart count (increments when items are added)
let demoCartCount = 3;

const loadCartCount = async () => {
  try {
    // DEMO MODE: Use hardcoded cart count instead of API call
    // const cart = await fetchCart();
    // const newCount = cart.items?.length || 0;
    
    // Use demo cart count (increments when items added via cart-updated event)
    cartCount.value = demoCartCount;
  } catch (err) {
    // Fallback to demo count
    cartCount.value = demoCartCount;
  }
};

// Listen for cart updates and increment count
if (typeof window !== 'undefined') {
  window.addEventListener('cart-updated', () => {
    demoCartCount = Math.min(demoCartCount + 1, 10); // Cap at 10 for demo
    loadCartCount();
  });
}

// Last data sync timestamp (demo mode)
const lastDataSync = ref<Date>(new Date());

// Format last sync time
const lastSyncText = computed(() => {
  const now = new Date();
  const diffMs = now.getTime() - lastDataSync.value.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else {
    return `${diffDays}d ago`;
  }
});

const lastSyncFormatted = computed(() => {
  return lastDataSync.value.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
});

let syncInterval: ReturnType<typeof setInterval> | null = null;

// Load cart count on mount and watch for changes
onMounted(() => {
  loadCartCount();
  // Poll for cart updates (demo mode)
  setInterval(loadCartCount, 2000);
  
  // Listen for cart update events
  if (typeof window !== 'undefined') {
    window.addEventListener('cart-updated', loadCartCount);
  }
  
  // Set initial sync time to 15 minutes ago for demo
  lastDataSync.value = new Date(Date.now() - 15 * 60000);
  
  // Update sync time every 5 minutes (simulate periodic syncs)
  syncInterval = setInterval(() => {
    lastDataSync.value = new Date();
  }, 5 * 60000); // 5 minutes
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('cart-updated', loadCartCount);
  }
  if (syncInterval) {
    clearInterval(syncInterval);
  }
});
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar
      collapsible
      resizable
    >
      <template #header="{ collapsed }">
        <div
          v-if="!collapsed"
          class="flex items-center gap-2"
        >
          <h1 class="text-xl font-bold text-primary">Forecast Enterprise</h1>
        </div>
        <UIcon
          v-else
          name="i-lucide-layout-dashboard"
          class="size-5 text-primary mx-auto"
        />
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :collapsed="collapsed"
          :items="[mainMenuItems, otherMenuItems]"
          orientation="vertical"
          type="multiple"
        />
      </template>

      <template #footer="{ collapsed }">
        <UButton
          :avatar="{
            src: undefined,
          }"
          :label="collapsed ? undefined : user?.email || 'User'"
          color="neutral"
          variant="ghost"
          class="w-full"
          :block="collapsed"
          @click="handleLogout"
        >
          <template #trailing>
            <UIcon
              name="i-lucide-log-out"
              class="size-4"
            />
          </template>
        </UButton>
      </template>
    </UDashboardSidebar>

    <UDashboardPanel>
      <template #header>
        <UDashboardNavbar :title="pageTitle">
          <template #trailing>
            <div class="flex items-center gap-4">
              <!-- Last Data Sync -->
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <UIcon
                  name="i-lucide-refresh-cw"
                  class="w-3.5 h-3.5"
                />
                <span class="hidden sm:inline">Last sync:</span>
                <UTooltip
                  :text="`Last data sync: ${lastSyncFormatted}`"
                >
                  <span class="font-medium">{{ lastSyncText }}</span>
                </UTooltip>
              </div>
              
              <UButton
                icon="i-lucide-shopping-cart"
                variant="ghost"
                color="primary"
                :to="'/purchase-orders/draft'"
                class="relative"
              >
                <template #trailing>
                  <UBadge
                    v-if="cartCount > 0"
                    :label="cartCount.toString()"
                    color="primary"
                    variant="solid"
                    class="absolute -top-1 -right-1 min-w-[20px] h-5 flex items-center justify-center animate-bounce-once"
                  />
                </template>
              </UButton>
              <span class="text-sm text-muted">{{ user?.email || "Guest" }}</span>
            </div>
          </template>
        </UDashboardNavbar>
      </template>

      <template #body>
        <slot />
      </template>
    </UDashboardPanel>
  </UDashboardGroup>
</template>
