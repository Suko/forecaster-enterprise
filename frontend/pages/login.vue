<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <Card class="w-full max-w-sm">
      <CardHeader class="space-y-4 px-6 py-2.5">
        <CardTitle class="text-2xl text-left">Admin Login</CardTitle>
        <CardDescription class="text-left">
          Enter your credentials to access the admin dashboard
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="handleLogin" class="space-y-4">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              placeholder="Enter your email address"
              required
              autocomplete="email"
            />
          </div>
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              placeholder="Enter your password"
              required
              autocomplete="current-password"
            />
          </div>

          <Alert v-if="error" variant="destructive">
            <AlertDescription>
              {{ error }}
            </AlertDescription>
          </Alert>

          <Button
            type="submit"
            class="w-full"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Signing in...' : 'Sign in' }}
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const email = ref('')
const password = ref('')
const isSubmitting = ref(false)
const error = ref<string | null>(null)
const { fetch } = useUserSession()

// Get return URL from query parameters
const route = useRoute()
const returnUrl = computed(() => {
  const redirect = route.query.redirect as string
  if (redirect && redirect !== '/login' && redirect !== '/') {
    return redirect
  }
  return '/dashboard'
})

const handleLogin = async () => {
  if (isSubmitting.value) {
    return
  }

  error.value = null

  if (!email.value || !password.value) {
    error.value = 'Please enter both email and password'
    return
  }

  isSubmitting.value = true

  try {
    const response = await $fetch('/api/auth/login', {
      method: 'POST',
      body: {
        email: email.value,
        password: password.value,
      },
    })

    if (response.success) {
      // Fetch user session after successful login
      await fetch()
      
      // Redirect to return URL or dashboard
      await navigateTo(returnUrl.value)
    } else {
      error.value = response.error || 'Login failed'
    }
  } catch (err: any) {
    error.value = err.data?.error || err.message || 'Login failed. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

