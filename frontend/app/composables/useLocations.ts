import type { Location, LocationCreate, LocationUpdate } from "~/types/location";

export const useLocations = () => {
  const { isDemoMode } = useDemoMode();

  const fetchLocations = async (params?: {
    search?: string;
    page?: number;
    pageSize?: number;
  }): Promise<{
    items: Location[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }> => {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append("search", params.search);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.pageSize) queryParams.append("page_size", params.pageSize.toString());

    // In demo mode, return empty list (locations not in demo data)
    if (isDemoMode.value) {
      return {
        items: [],
        total: 0,
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        total_pages: 0,
      };
    }

    const url = `/api/locations${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    return await $fetch(url);
  };

  const fetchLocation = async (id: string): Promise<Location> => {
    // In demo mode, return mock location
    if (isDemoMode.value) {
      throw createError({
        statusCode: 404,
        statusMessage: "Location not found in demo mode",
      });
    }
    return await $fetch(`/api/locations/${encodeURIComponent(id)}`);
  };

  const createLocation = async (data: LocationCreate): Promise<Location> => {
    // In demo mode, return mock location (no persistence)
    if (isDemoMode.value) {
      return {
        id: `demo-${Date.now()}`,
        ...data,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Location;
    }
    return await $fetch("/api/locations", {
      method: "POST",
      body: data,
    });
  };

  const updateLocation = async (
    id: string,
    data: LocationUpdate
  ): Promise<Location> => {
    // In demo mode, return updated mock location (no persistence)
    if (isDemoMode.value) {
      return {
        id,
        ...data,
        updated_at: new Date().toISOString(),
      } as Location;
    }
    return await $fetch(`/api/locations/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: data,
    });
  };

  const deleteLocation = async (id: string): Promise<void> => {
    // In demo mode, just return (no persistence)
    if (isDemoMode.value) {
      return;
    }
    return await $fetch(`/api/locations/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  };

  return {
    fetchLocations,
    fetchLocation,
    createLocation,
    updateLocation,
    deleteLocation,
  };
};

