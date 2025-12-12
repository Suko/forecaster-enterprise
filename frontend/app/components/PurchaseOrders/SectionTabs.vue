<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";

const route = useRoute();

const isSupplierRoute = computed(() => route.path.startsWith("/purchase-orders/suppliers"));
const isDraftRoute = computed(() => route.path === "/purchase-orders/draft");
const isOrdersRoute = computed(() => route.path === "/purchase-orders" || route.path.startsWith("/purchase-orders/"));

const items = computed<NavigationMenuItem[]>(() => [
  {
    label: "Draft (Cart)",
    icon: "i-lucide-shopping-cart",
    to: "/purchase-orders/draft",
    active: isDraftRoute.value,
  },
  {
    label: "Orders",
    icon: "i-lucide-receipt",
    to: "/purchase-orders",
    active: isOrdersRoute.value && !isSupplierRoute.value && !isDraftRoute.value,
  },
  {
    label: "Suppliers",
    icon: "i-lucide-truck",
    to: "/purchase-orders/suppliers",
    active: isSupplierRoute.value,
  },
]);
</script>

<template>
  <UNavigationMenu :items="items" class="mb-4" />
</template>

