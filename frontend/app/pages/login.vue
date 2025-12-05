<template>
  <div class="flex flex-col items-center justify-center min-h-screen p-4">
    <UPageCard class="w-full max-w-md">
      <UAuthForm
        :schema="schema"
        :fields="fields"
        title="Admin Login"
        description="Enter your credentials to access the admin dashboard"
        icon="i-lucide-lock"
        :loading="isSubmitting"
        @submit="handleLogin"
      >
        <template #validation>
          <UAlert
            v-if="error"
            color="error"
            icon="i-lucide-alert-circle"
            :title="error"
            class="mb-4"
          />
        </template>
      </UAuthForm>
    </UPageCard>
  </div>
</template>

<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'

definePageMeta({
  layout: false,
})

const { loggedIn, fetch: refreshSession } = useUserSession()
const isSubmitting = ref(false)
const error = ref<string | null>(null)

// Redirect if already logged in
if (loggedIn.value) {
  await navigateTo('/dashboard')
}

const fields: AuthFormField[] = [
  {
    name: 'email',
    type: 'email',
    label: 'Email',
    placeholder: 'Enter your email',
    required: true,
    autocomplete: 'email'
  },
  {
    name: 'password',
    label: 'Password',
    type: 'password',
    placeholder: 'Enter your password',
    required: true,
    autocomplete: 'current-password'
  }
]

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required')
})

type Schema = z.output<typeof schema>

async function handleLogin(payload: FormSubmitEvent<Schema>) {
  if (isSubmitting.value) return
  
  error.value = null
  isSubmitting.value = true
  
  try {
    await $fetch('/api/login', {
      method: 'POST',
      body: {
        email: payload.data.email,
        password: payload.data.password,
      },
    })

    // Refresh the session on client-side and redirect to dashboard
    await refreshSession()
    await navigateTo('/dashboard')
  } catch (err: any) {
    // Extract error message from various possible error structures
    const errorMessage = 
      err.data?.detail ||           // FastAPI error detail
      err.data?.statusMessage ||   // Nuxt error statusMessage
      err.data?.message ||         // Generic error message
      err.message ||                // Error object message
      'Login failed. Please check your credentials and try again.'
    
    error.value = errorMessage
  } finally {
    isSubmitting.value = false
  }
}
</script>
