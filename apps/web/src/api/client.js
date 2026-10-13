import { config } from '../core/config.js';
export async function request(method, path, { body, signal } = {}) {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  if (signal?.aborted) cancel();
  signal?.addEventListener('abort', cancel, { once: true });
  const timer = setTimeout(() => controller.abort('timeout'), config.requestTimeoutMs);
  try {
    const response = await fetch(`${config.apiBaseUrl.replace(/\/$/, '')}${path}`, {
      method, headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined, signal: controller.signal
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      const details = Array.isArray(data?.detail) ? data.detail.map(d => d.msg).join('; ') : typeof data?.detail === 'string' ? data.detail : '';
      throw new Error(`La API respondió con estado ${response.status}.${details ? ' ' + details : ' Revisa la conexión del backend con el grafo.'}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    if (controller.signal.reason === 'timeout') throw new Error('La consulta superó el tiempo de espera. Intenta nuevamente.');
    if (error instanceof TypeError) throw new Error('No fue posible conectar con la API. Verifica que FastAPI esté activo en el puerto 8001.');
    throw error;
  } finally { clearTimeout(timer); signal?.removeEventListener('abort', cancel); }
}
