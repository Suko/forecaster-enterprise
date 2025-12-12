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
          <USelectMenu
            :model-value="user.role"
            :items="roleOptions"
            value-key="value"
            size="sm"
            variant="ghost"
            @update:model-value="(value) => updateRole(user, typeof value === 'string' ? value : value?.value || value)"
          >
            <template #default>
              <span class="text-sm lowercase">{{ user.role }}</span>
            </template>
          </USelectMenu>
          <UDropdownMenu :items="getUserActions(user)">
            <UButton
              icon="i-lucide-more-vertical"
              color="gray"
              variant="ghost"
              size="sm"
            />
          </UDropdownMenu>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-lucide-loader-2" class="size-6 animate-spin text-gray-400" />
      </div>

      <div v-if="!loading && filteredUsers.length === 0" class="text-center py-12">
        <p class="text-gray-500 dark:text-gray-400">
          {{ searchQuery ? 'No users found' : 'No users yet' }}
        </p>
      </div>
    </div>

    <UModal v-model="showModal" :ui="{ width: 'sm:max-w-md' }">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">
            {{ editingUser ? 'Edit User' : 'Add User' }}
          </h3>
        </template>

        <UForm
          :schema="schema.value"
          :state="formState"
          @submit="handleSubmit"
        >
          <UFormField label="Email" name="email" required>
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

          <UFormField label="Name" name="name">
            <UInput v-model="formState.name" />
          </UFormField>

          <UFormField label="Role" name="role" required>
            <USelect
              v-model="formState.role"
              :options="roleOptions"
            />
          </UFormField>

          <UFormField label="Status" name="is_active">
            <USwitch
              v-model="formState.is_active"
              label="Active"
            />
          </UFormField>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="gray"
                variant="ghost"
                @click="closeModal"
              >
                Cancel
              </UButton>
              <UButton
                type="submit"
                :loading="submitting"
              >
                {{ editingUser ? 'Update' : 'Create' }}
              </UButton>
            </div>
          </template>
        </UForm>
      </UCard>
    </UModal>

    <UModal v-model="showDeleteModal" :ui="{ width: 'sm:max-w-md' }">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-red-600">Delete User</h3>
        </template>

        <p class="text-gray-600 mb-4">
          Are you sure you want to delete <strong>{{ userToDelete?.email }}</strong>? This action cannot be undone.
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
              color="red"
              :loading="deleting"
              @click="handleDelete"
            >
              Delete
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import * as z from "zod";
import type { FormSubmitEvent } from "#ui/types";

const { apiCall } = useApi();

interface User {
  id: string
  email: string
  name: string | null
  role: string
  is_active: boolean
}

const users = ref<User[]>([]);
const loading = ref(false);
const submitting = ref(false);
const deleting = ref(false);
const showModal = ref(false);
const showDeleteModal = ref(false);
const editingUser = ref<User | null>(null);
const userToDelete = ref<User | null>(null);

const roleOptions = [
  { label: "Admin", value: "admin" },
  { label: "User", value: "user" }
];

const formState = reactive({
  email: "",
  password: "",
  name: "",
  role: "user",
  is_active: true
});

const schema = computed(() => {
  const baseSchema = {
    email: z.string().email("Invalid email address"),
    name: z.string().optional(),
    role: z.enum(["admin", "user"]),
    is_active: z.boolean()
  };
  
  if (editingUser.value) {
    return z.object(baseSchema);
  } else {
    return z.object({
      ...baseSchema,
      password: z.string()
        .min(8, "Password must be at least 8 characters")
        .max(128, "Password must be no more than 128 characters")
    });
  }
});

const searchQuery = ref("");

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value;
  const query = searchQuery.value.toLowerCase();
  return users.value.filter(user => 
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
  [{
    label: "Edit",
    icon: "i-lucide-edit",
    click: () => openEditModal(user)
  }],
  [{
    label: "Delete",
    icon: "i-lucide-trash-2",
    click: () => confirmDelete(user)
  }]
];

const updateRole = async (user: User, newRole: string) => {
  try {
    await apiCall(`/users/${user.id}`, {
      method: "PATCH",
      body: JSON.stringify({ role: newRole })
    });
    await fetchUsers();
  } catch (error: any) {
    console.error("Failed to update role:", error);
  }
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    users.value = await apiCall<User[]>("/users");
  } catch (error: any) {
    console.error("Failed to fetch users:", error);
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

const handleSubmit = async (event: FormSubmitEvent<any>) => {
  submitting.value = true;
  try {
    if (editingUser.value) {
      await apiCall(`/users/${editingUser.value.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: formState.name,
          role: formState.role,
          is_active: formState.is_active
        })
      });
    } else {
      await apiCall("/users", {
        method: "POST",
        body: JSON.stringify({
          email: formState.email,
          password: formState.password,
          name: formState.name,
          role: formState.role
        })
      });
    }
    await fetchUsers();
    closeModal();
  } catch (error: any) {
    console.error("Failed to save user:", error);
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
      method: "DELETE"
    });
    await fetchUsers();
    showDeleteModal.value = false;
    userToDelete.value = null;
  } catch (error: any) {
    console.error("Failed to delete user:", error);
  } finally {
    deleting.value = false;
  }
};

onMounted(() => {
  fetchUsers();
});
</script>








