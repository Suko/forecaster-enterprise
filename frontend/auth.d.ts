declare module '#auth-utils' {
  interface User {
    id: string
    email: string
    name: string | null
    role: 'admin' | 'user'
    is_active: boolean
    created_at: string
    updated_at: string
  }

  interface UserSession {
    user: User
    loggedInAt: Date
  }

  interface SecureSessionData {
    // Add any secure data here if needed
  }
}

export {}

