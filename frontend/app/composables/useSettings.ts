export interface ClientSettings {
  client_id: string;
  safety_buffer_days: number;
  understocked_threshold: number;
  overstocked_threshold: number;
  dead_stock_days: number;
  recommendation_rules?: Record<string, any>;
}

export interface ClientSettingsUpdate {
  safety_buffer_days?: number;
  understocked_threshold?: number;
  overstocked_threshold?: number;
  dead_stock_days?: number;
}

export const useSettings = () => {
  const { isDemoMode } = useDemoMode();

  const fetchSettings = async (): Promise<ClientSettings> => {
    // In demo mode, return default settings
    if (isDemoMode.value) {
      return {
        client_id: "demo-client",
        safety_buffer_days: 7,
        understocked_threshold: 14,
        overstocked_threshold: 90,
        dead_stock_days: 365,
      };
    }
    return await $fetch<ClientSettings>("/api/settings");
  };

  const updateSettings = async (data: ClientSettingsUpdate): Promise<ClientSettings> => {
    // In demo mode, just return updated settings (no persistence)
    if (isDemoMode.value) {
      const current = await fetchSettings();
      return { ...current, ...data };
    }
    return await $fetch<ClientSettings>("/api/settings", {
      method: "PUT",
      body: data,
    });
  };

  return {
    fetchSettings,
    updateSettings,
  };
};

