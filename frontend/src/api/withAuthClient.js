import { createApiClient } from "./client";

// React hook to get an API client
export const useApi = () => {
  return createApiClient();
};
