# Forecaster Enterprise - Frontend

A modern, enterprise-grade forecasting dashboard built with Nuxt 4 and Nuxt UI, featuring comprehensive authentication, user management, and a clean, intuitive interface.

## Overview

Forecaster Enterprise is a full-stack application for inventory forecasting and management. This frontend application provides a responsive, secure dashboard interface for managing forecasts, inventory, and team members.

**Backend**: FastAPI backend using `uv` for package management (see `/backend` directory)

### Key Features

- **Secure Authentication**: JWT-based authentication with session management using `nuxt-auth-utils`
- **User Management**: Complete user management system with role-based access control (Admin/User)
- **Modern UI**: Built with Nuxt UI components following official design patterns
- **Dashboard Layout**: Collapsible sidebar navigation with responsive design
- **Settings Management**: Comprehensive settings pages with tabs (General, Users, Notifications, Security)
- **API Integration**: Seamless integration with FastAPI backend through Nuxt server routes
- **Fast Package Management**: Uses Bun for lightning-fast dependency installation and script execution

## Tech Stack

- **Framework**: [Nuxt 4](https://nuxt.com) - Vue.js meta-framework
- **UI Library**: [Nuxt UI](https://ui.nuxt.com) - Official Nuxt UI component library
- **Authentication**: [nuxt-auth-utils](https://github.com/nuxt-modules/auth-utils) - Official Nuxt authentication utilities
- **Validation**: [Zod](https://zod.dev) - TypeScript-first schema validation
- **Icons**: [Lucide Vue Next](https://lucide.dev) - Beautiful icon library
- **Styling**: Tailwind CSS 4

## Architecture

### Authentication Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │         │  Nuxt Server │         │  FastAPI    │
│   (Client)  │────────▶│   Routes    │────────▶│   Backend   │
└─────────────┘         └──────────────┘         └─────────────┘
     Session Cookie          JWT Token              JWT Validation
```

- **Client**: Makes requests to Nuxt server routes (`/api/*`)
- **Nuxt Server Routes**: Handle authentication, forward requests to FastAPI backend
- **FastAPI Backend**: Validates JWT tokens and processes business logic
- **Session Management**: JWT tokens stored server-side, never exposed to browser JavaScript

### Project Structure

```
frontend/
├── app/
│   ├── components/          # Vue components
│   │   ├── GeneralSection.vue
│   │   ├── UsersSection.vue
│   │   └── SettingsLayout.vue
│   ├── composables/         # Vue composables
│   │   └── useApi.ts        # API client composable
│   ├── layouts/             # Layout components
│   │   ├── dashboard.vue    # Main dashboard layout with sidebar
│   │   └── default.vue
│   ├── middleware/          # Route middleware
│   │   └── auth.global.ts   # Global authentication middleware (runs on all routes)
│   └── pages/               # File-based routing
│       ├── dashboard.vue
│       ├── login.vue
│       └── settings/        # Settings pages with tabs
│           ├── index.vue    # General settings
│           ├── users.vue    # User management
│           ├── notifications.vue
│           └── security.vue
├── server/
│   ├── api/                 # Nuxt server routes (API endpoints)
│   │   ├── login.post.ts
│   │   ├── me.get.ts
│   │   └── users/           # User management endpoints
│   ├── middleware/          # Server middleware
│   │   └── security-headers.ts
│   └── utils/               # Server utilities
│       ├── api.ts           # Authenticated fetch utilities
│       └── security-logger.ts
└── nuxt.config.ts           # Nuxt configuration
```

## Authentication

The application uses `nuxt-auth-utils` following the [official Nuxt 4.x authentication guide](https://nuxt.com/docs/4.x/guide/recipes/sessions-and-authentication).

### Features

- **Secure Session Management**: JWT tokens stored server-side in encrypted session cookies
- **Automatic Token Validation**: Tokens validated on each authenticated request
- **Role-Based Access Control**: Admin-only endpoints for user management
- **Security Logging**: All authentication events logged for security monitoring

### Usage

**Protected Routes:**

Authentication is handled globally via `auth.global.ts` middleware. All pages are protected by default. No need to specify `middleware: "auth"` on individual pages.

```vue
<script setup>
definePageMeta({
  layout: "dashboard",
});
</script>
```

To opt out of authentication for a specific page (e.g., login page), set `auth: false`:

```vue
<script setup>
definePageMeta({
  layout: "default",
  auth: false,
});
</script>
```

**Accessing User Session:**

```vue
<script setup>
const { loggedIn, user, clear: clearSession } = useUserSession();

if (loggedIn.value) {
  console.log(user.value?.email);
}
</script>
```

**Making Authenticated API Calls:**

```vue
<script setup>
const { apiCall } = useApi();

const fetchData = async () => {
  const data = await apiCall("/users", { method: "GET" });
};
</script>
```

For detailed authentication documentation, see [AUTH_SETUP.md](./AUTH_SETUP.md).

## Development Setup

### Prerequisites

- Node.js 18+
- Bun (recommended), or npm/pnpm/yarn

### Installation

```bash
# Install dependencies (Bun - recommended for speed)
bun install
# or
npm install
# or
pnpm install
```

### Environment Variables

Create a `.env` file in the root directory:

```env
NUXT_SESSION_PASSWORD=your-secure-random-password-with-at-least-32-characters
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Note**: `NUXT_SESSION_PASSWORD` is automatically generated in development if not set.

### Development Server

```bash
# Start development server (Bun - recommended)
bun run dev
# or
npm run dev
```

The application will be available at `http://localhost:3000`.

### Production Build

```bash
# Build for production (Bun - recommended)
bun run build
# or
npm run build

# Preview production build locally
bun run preview
# or
npm run preview
```

## Key Pages

### Dashboard (`/dashboard`)

Main dashboard with overview metrics and navigation.

### Settings (`/settings`)

Comprehensive settings management with tabbed interface:

- **General**: Account information and preferences
- **Users**: User management with role assignment
- **Notifications**: Notification preferences (coming soon)
- **Security**: Security settings (coming soon)

### User Management

- View all users with search functionality
- Invite new users by email
- Edit user roles (Admin/User)
- Activate/deactivate users
- Delete users

## API Integration

All API calls go through Nuxt server routes (`/api/*`) which:

1. Handle authentication automatically
2. Forward requests to FastAPI backend
3. Manage JWT tokens securely
4. Handle errors gracefully

**Server Route Example:**

```typescript
// server/api/users.get.ts
export default defineEventHandler(async (event) => {
  const users = await authenticatedFetch(event, "/users");
  return users;
});
```

**Client Usage:**

```typescript
const { apiCall } = useApi();
const users = await apiCall("/users");
```

## Security Features

- **HttpOnly Cookies**: Session cookies cannot be accessed via JavaScript
- **Secure Cookies**: Cookies only sent over HTTPS in production
- **JWT Token Protection**: Tokens never exposed to client-side code
- **Automatic Token Validation**: Invalid tokens automatically clear session
- **Security Logging**: All authentication events logged
- **Security Headers**: CSP, XSS protection, and other security headers configured

## Documentation

- [AUTH_SETUP.md](./AUTH_SETUP.md) - Detailed authentication setup and usage
- [Nuxt Documentation](https://nuxt.com/docs)
- [Nuxt UI Documentation](https://ui.nuxt.com)
- [nuxt-auth-utils](https://github.com/nuxt-modules/auth-utils)

## License

Private - Enterprise Use Only
