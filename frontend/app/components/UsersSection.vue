<template>
  <div class="space-y-6">
    <div class="flex justify-between items-start">
      <div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Users</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Invite new users by email address.
        </p>
      </div>
      <UButton
        icon="i-lucide-user-plus"
        @click="openCreateModal"
      >
        Invite people
      </UButton>
    </div>

    <UInput
      v-model="searchQuery"
      icon="i-lucide-search"
      placeholder="Search users"
      class="w-full"
    />

    <div class="space-y-1">
      <div
        v-for="user in filteredUsers"
        :key="user.id"
        class="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <div class="flex-1 min-w-0">
            <div class="font-medium text-gray-900 dark:text-white">
              {{ user.name || user.email }}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 truncate">
              {{ getUsername(user) }}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <UBadge
            :color="user.role === 'admin' ? 'primary' : 'neutral'"
            variant="soft"
            size="sm"
          >
            {{ user.role }}
          </UBadge>
          <UDropdownMenu :items="getUserActions(user)">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              size="sm"
            />
          </UDropdownMenu>
        </div>
      </div>

      <div
        v-if="loading"
        class="flex justify-center py-8"
      >
        <UIcon
          name="i-lucide-loader-2"
          class="size-6 animate-spin text-gray-400"
        />
      </div>

      <div
        v-if="!loading && filteredUsers.length === 0"
        class="text-center py-12"
      >
        <p class="text-gray-500 dark:text-gray-400">
          {{ searchQuery ? "No users found" : "No users yet" }}
        </p>
      </div>
    </div>

    <UModal
      v-model:open="showModal"
      :ui="{ content: 'sm:max-w-md' }"
    >
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">
              {{ editingUser ? "Edit User" : "Add User" }}
            </h3>
          </template>

          <UForm
            ref="formRef"
            :schema="schema.value"
            :state="formState"
            @submit="handleSubmit"
          >
            <UFormField
              label="Email"
              name="email"
              required
            >
              <UInput
                v-model="formState.email"
                type="email"
                :disabled="!!editingUser"
              />
            </UFormField>

            <UFormField
              v-if="!editingUser"
              label="Password"
              name="password"
              required
            >
              <UInput
                v-model="formState.password"
                type="password"
              />
            </UFormField>

            <UFormField
              label="Name"
              name="name"
            >
              <UInput v-model="formState.name" />
            </UFormField>

            <UFormField
              label="Role"
              name="role"
              required
            >
              <USelect
                v-model="formState.role"
                :items="roleOptions"
                value-key="value"
              />
            </UFormField>

            <UFormField
              label="Status"
              name="is_active"
            >
              <USwitch
                v-model="formState.is_active"
                label="Active"
              />
            </UFormField>
          </UForm>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                @click="closeModal"
              >
                Cancel
              </UButton>
              <UButton
                :loading="submitting"
                @click="submitForm"
              >
                {{ editingUser ? "Update" : "Create" }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <UModal
      v-model:open="showDeleteModal"
      :ui="{ content: 'sm:max-w-md' }"
    >
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold text-red-600">Delete User</h3>
          </template>

          <p class="text-gray-600 mb-4">
            Are you sure you want to delete <strong>{{ userToDelete?.email }}</strong
            >? This action cannot be undone.
          </p>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="gray"
                variant="ghost"
                @click="showDeleteModal = false"
              >
                Cancel
              </UButton>
              <UButton
                color="error"
                :loading="deleting"
                @click="handleDelete"
              >
                Delete
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import * as z from "zod";
import type { FormSubmitEvent } from "#ui/types";

const { apiCall } = useApi();

interface User {
  id: string;
  email: string;
  name: string | null;
  role: string;
  is_active: boolean;
}

const users = ref<User[]>([]);
const loading = ref(false);
const submitting = ref(false);
const deleting = ref(false);
const showModal = ref(false);
const showDeleteModal = ref(false);
const editingUser = ref<User | null>(null);
const userToDelete = ref<User | null>(null);
const formRef = ref<HTMLFormElement | null>(null);

const roleOptions = [
  { label: "Admin", value: "admin" },
  { label: "User", value: "user" },
];

const formState = reactive({
  email: "",
  password: "",
  name: "",
  role: "user",
  is_active: true,
});

const schema = computed(() => {
  const baseSchema = {
    email: z.string().email("Invalid email address"),
    name: z.string().optional(),
    role: z.enum(["admin", "user"]),
    is_active: z.boolean(),
  };

  if (editingUser.value) {
    return z.object(baseSchema);
  } else {
    return z.object({
      ...baseSchema,
      password: z
        .string()
        .min(8, "Password must be at least 8 characters")
        .max(128, "Password must be no more than 128 characters"),
    });
  }
});

const searchQuery = ref("");

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value;
  const query = searchQuery.value.toLowerCase();
  return users.value.filter(
    (user) =>
      user.email.toLowerCase().includes(query) ||
      (user.name && user.name.toLowerCase().includes(query))
  );
});

const getUsername = (user: User) => {
  if (user.email) {
    return user.email.split("@")[0];
  }
  return user.email;
};

const getUserActions = (user: User) => [
  [
    {
      label: "Edit",
      icon: "i-lucide-edit",
      onSelect: () => openEditModal(user),
    },
  ],
  [
    {
      label: "Delete",
      icon: "i-lucide-trash-2",
      onSelect: () => confirmDelete(user),
    },
  ],
];

const fetchUsers = async () => {
  loading.value = true;
  try {
    users.value = await apiCall<User[]>("/users");
  } catch (error: any) {
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  editingUser.value = null;
  formState.email = "";
  formState.password = "";
  formState.name = "";
  formState.role = "user";
  formState.is_active = true;
  showModal.value = true;
};

const openEditModal = (user: User) => {
  editingUser.value = user;
  formState.email = user.email;
  formState.password = "";
  formState.name = user.name || "";
  formState.role = user.role;
  formState.is_active = user.is_active;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingUser.value = null;
};

const submitForm = async () => {
  // Create a synthetic submit event and call handleSubmit directly
  const syntheticEvent = {
    data: formState,
    preventDefault: () => {},
  } as FormSubmitEvent<any>;
  await handleSubmit(syntheticEvent);
};

const handleSubmit = async (event: FormSubmitEvent<any>) => {
  submitting.value = true;
  try {
    if (editingUser.value) {
      await apiCall(`/users/${editingUser.value.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: formState.name,
          role: formState.role,
          is_active: formState.is_active,
        }),
      });
    } else {
      await apiCall("/users", {
        method: "POST",
        body: JSON.stringify({
          email: formState.email,
          password: formState.password,
          name: formState.name,
          role: formState.role,
        }),
      });
    }
    await fetchUsers();
    closeModal();
  } catch (error: any) {
  } finally {
    submitting.value = false;
  }
};

const confirmDelete = (user: User) => {
  userToDelete.value = user;
  showDeleteModal.value = true;
};

const handleDelete = async () => {
  if (!userToDelete.value) return;

  deleting.value = true;
  try {
    await apiCall(`/users/${userToDelete.value.id}`, {
      method: "DELETE",
    });
    await fetchUsers();
    showDeleteModal.value = false;
    userToDelete.value = null;
  } catch (error: any) {
  } finally {
    deleting.value = false;
  }
};

onMounted(() => {
  // Reset modal states on mount
  showModal.value = false;
  showDeleteModal.value = false;
  editingUser.value = null;
  userToDelete.value = null;

  fetchUsers();
});
</script>
