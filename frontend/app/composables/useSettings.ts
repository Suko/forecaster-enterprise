export interface ClientSettings {
  client_id: string;
  safety_buffer_days: number;
  understocked_threshold: number;
  overstocked_threshold: number;
  dead_stock_days: number;
  recommendation_rules?: Record<string, unknown>;
}

export interface ClientSettingsUpdate {
  safety_buffer_days?: number;
  understocked_threshold?: number;
  overstocked_threshold?: number;
  dead_stock_days?: number;
}

export const useSettings = () => {
  const fetchSettings = async (): Promise<ClientSettings> => {
    return await $fetch<ClientSettings>("/api/settings");
  };

  const updateSettings = async (data: ClientSettingsUpdate): Promise<ClientSettings> => {
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
