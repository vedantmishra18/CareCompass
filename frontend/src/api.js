export async function request(path, { token, method = "GET", body } = {}) {
  const response = await fetch(path, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  const data =
    response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(
      typeof data?.detail === "string"
        ? data.detail
        : "The request could not be completed. Please retry.",
    );
    error.status = response.status;
    throw error;
  }
  return data;
}
