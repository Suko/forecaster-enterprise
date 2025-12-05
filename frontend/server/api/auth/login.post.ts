export default defineEventHandler(async (event) => {
  // setUserSession is auto-imported by nuxt-auth-utils
  const body = await readBody(event)
  const config = useRuntimeConfig()

  try {
    // Call FastAPI backend
    const response = await $fetch(`${config.apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: body.email, // FastAPI expects 'username' field
        password: body.password,
      }).toString(),
    })

    if (response.access_token) {
      // Get user info from backend
      const userResponse = await $fetch(`${config.apiBaseUrl}/auth/me`, {
        headers: {
          Authorization: `Bearer ${response.access_token}`,
        },
      })

      // Set user session in Nuxt
      await setUserSession(event, {
        user: userResponse,
        loggedInAt: new Date(),
      })

      return {
        success: true,
        user: userResponse,
      }
    }

    return {
      success: false,
      error: 'No access token received',
    }
  } catch (error: any) {
    const status = error.status || error.statusCode || 500
    const message = error.data?.detail || error.message || 'Login failed'

    if (status === 401 || status === 403) {
      return {
        success: false,
        error: 'Invalid email or password',
      }
    }

    return {
      success: false,
      error: message,
    }
  }
})

