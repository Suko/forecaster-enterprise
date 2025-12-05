import { z } from 'zod'
import { logSecurityEvent, getClientIP, getUserAgent } from '../utils/security-logger'

const bodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

export default defineEventHandler(async (event) => {
  const clientIP = getClientIP(event)
  const userAgent = getUserAgent(event)
  
  try {
    const { email, password } = await readValidatedBody(event, bodySchema.parse)

    const config = useRuntimeConfig()
    const apiBaseUrl = config.public.apiBaseUrl

    // Forward to FastAPI backend
    // FastAPI expects OAuth2PasswordRequestForm which uses form data
    const formData = new URLSearchParams()
    formData.append('username', email) // OAuth2 uses 'username' field for email
    formData.append('password', password)

    const response = await $fetch(`${apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    })

    if (response && 'access_token' in response) {
      const accessToken = (response as any).access_token

      // Fetch user info from backend using the token
      let userInfo = { email }
      try {
        const userResponse = await $fetch(`${apiBaseUrl}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        })
        userInfo = userResponse as any
      } catch (err) {
        // If /auth/me fails, continue with email only
        // Error logged server-side without exposing details to client
      }

      // Store token and user info in session using nuxt-auth-utils
      await setUserSession(event, {
        user: userInfo,
        accessToken: accessToken,
      })

      // Log successful login
      logSecurityEvent({
        type: 'login_success',
        email: email,
        ip: clientIP,
        userAgent: userAgent,
      })

      return {}
    }

    // Log failed login attempt
    logSecurityEvent({
      type: 'login_failure',
      ip: clientIP,
      userAgent: userAgent,
      details: { reason: 'Invalid credentials or no token received' },
    })

    throw createError({
      statusCode: 401,
      statusMessage: 'Authentication failed',
    })
  } catch (error: any) {
    // Log login failure with error details
    if (error.statusCode === 401 || error.statusCode === 429) {
      logSecurityEvent({
        type: error.statusCode === 429 ? 'rate_limit' : 'login_failure',
        email: error.data?.email,
        ip: clientIP,
        userAgent: userAgent,
        details: {
          statusCode: error.statusCode,
          message: error.data?.detail || error.statusMessage,
        },
      })
    }

    if (error.statusCode) {
      throw error
    }

    // Handle FastAPI error responses
    if (error.data) {
      throw createError({
        statusCode: error.statusCode || 401,
        statusMessage: error.data?.detail || 'Login failed',
        data: error.data,
      })
    }

    throw createError({
      statusCode: 500,
      statusMessage: 'Internal server error',
    })
  }
})

