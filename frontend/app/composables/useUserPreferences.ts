export interface UserPreferences {
  inventoryColumns?: {
    [field: string]: boolean; // true = visible, false = hidden
  };
  [key: string]: any; // Allow other preferences
}

export const useUserPreferences = () => {
  const preferences = ref<UserPreferences>({});
  const loading = ref(false);

  const fetchPreferences = async (): Promise<UserPreferences> => {
    loading.value = true;
    try {
      const response = await $fetch<{ preferences: UserPreferences }>("/api/auth/me/preferences");
      preferences.value = response.preferences || {};
      return preferences.value;
    } catch (error: any) {
      return {};
    } finally {
      loading.value = false;
    }
  };

  const updatePreferences = async (newPreferences: UserPreferences): Promise<void> => {
    loading.value = true;
    try {
      const response = await $fetch<{ preferences: UserPreferences }>("/api/auth/me/preferences", {
        method: "PUT",
        body: { preferences: newPreferences },
      });
      preferences.value = response.preferences || {};
    } catch (error: any) {
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const getInventoryColumnVisibility = (): { [field: string]: boolean } => {
    return preferences.value.inventoryColumns || {};
  };

  const setInventoryColumnVisibility = async (columnVisibility: {
    [field: string]: boolean;
  }): Promise<void> => {
    const newPreferences = {
      ...preferences.value,
      inventoryColumns: columnVisibility,
    };
    await updatePreferences(newPreferences);
  };

  return {
    preferences,
    loading,
    fetchPreferences,
    updatePreferences,
    getInventoryColumnVisibility,
    setInventoryColumnVisibility,
  };
};
