const runtime = window.__APP_CONFIG__ || {};
export const config = { apiBaseUrl: runtime.apiBaseUrl || import.meta.env.VITE_API_BASE_URL || '/api', requestTimeoutMs: Number(runtime.requestTimeoutMs || 120000) };
