<template>
  <div class="min-h-screen bg-background">
    <DashboardSidebar />
    <div 
      class="dashboard-main min-h-screen" 
      :style="`margin-left: ${sidebarLeftOffset}px; transition: margin-left 0.3s ease;`"
    >
      <DashboardNavbar />
      <main class="container mx-auto px-6 py-6 max-w-7xl">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const sidebarLeftOffset = ref(280) // Default sidebar width

onMounted(() => {
  // Initialize theme if needed
  // This can be expanded later for theme management
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

