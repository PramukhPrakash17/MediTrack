import { createApiClient } from "./client";
import { useAuth } from "../auth/AuthContext";

// React hook to get an API client that automatically adds the JWT to requests
export const useApi = () => {
  const { token } = useAuth();
  return createApiClient(() => token);
};
