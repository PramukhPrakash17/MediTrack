// Direct base URL (no proxy or .env)
const BASE_URL = "http://localhost:8080";

export const createApiClient = (getToken) => {
  const request = async (
    path,
    { headers = {}, auth = true, ...options } = {}
  ) => {
    const finalHeaders = new Headers({
      ...headers,
    });

    // Only set Content-Type to application/json if not FormData
    if (!(options.body instanceof FormData)) {
      finalHeaders.set("Content-Type", "application/json");
    }

    const token = getToken?.();
    if (auth && token) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${BASE_URL}${path}`, {
      headers: finalHeaders,
      ...options,
    });

    // Try to parse JSON; fall back to text
    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const message =
        typeof data === "string" ? data : data?.message || "Request failed";
      throw new Error(message);
    }

    return data;
  };

  return {
    post: (path, body, options) => {
      // Don't stringify FormData
      const requestBody = body instanceof FormData ? body : JSON.stringify(body);
      return request(path, {
        method: "POST",
        body: requestBody,
        ...options,
      });
    },
    get: (path, options) => request(path, { method: "GET", ...options }),
  };
};
