// Helper komunikasi dengan REST API Flask
const TOKEN_KEY = 'padi_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY))

export async function api(path, { method = 'GET', body, form } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body) headers['Content-Type'] = 'application/json'

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: form || (body ? JSON.stringify(body) : undefined),
  })
  const data = await res.json().catch(() => ({}))

  if (res.status === 401 && token) {
    setToken(null)
    window.location.href = '/login'
  }
  if (!res.ok) throw new Error(data.message || `Terjadi kesalahan (${res.status})`)
  return data
}

export const percent = (v) => `${Number(v).toFixed(2)}%`
