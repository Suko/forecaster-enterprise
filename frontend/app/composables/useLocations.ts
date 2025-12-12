import type { Location, LocationCreate, LocationUpdate } from "~/types/location";

export const useLocations = () => {
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

    const url = `/api/locations${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    return await $fetch(url);
  };

  const fetchLocation = async (id: string): Promise<Location> => {
    return await $fetch(`/api/locations/${encodeURIComponent(id)}`);
  };

  const createLocation = async (data: LocationCreate): Promise<Location> => {
    return await $fetch("/api/locations", {
      method: "POST",
      body: data,
    });
  };

  const updateLocation = async (
    id: string,
    data: LocationUpdate
  ): Promise<Location> => {
    return await $fetch(`/api/locations/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: data,
    });
  };

  const deleteLocation = async (id: string): Promise<void> => {
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

