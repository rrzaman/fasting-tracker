const BASE_URL = import.meta.env.VITE_API_URL

async function authFetch(url, token, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers,
        }
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
}

export async function fetchHealthData(token, days = 365) {
    const json = await authFetch(`${BASE_URL}/health?days=${days}`, token)
    return json.data
}

export async function fetchFastingData(token, daysBack = 365, daysForward = 90) {
    const json = await authFetch(`${BASE_URL}/fasting?days_back=${daysBack}&days_forward=${daysForward}`, token)
    return json.data
}

export async function fetchOverrides(token) {
    const json = await authFetch(`${BASE_URL}/overrides`, token)
    return json.data
}

export async function createOverride(token, date, overrideType) {
    return authFetch(`${BASE_URL}/overrides`, token, {
        method: 'POST',
        body: JSON.stringify({ date, override_type: overrideType })
    })
}

export async function updateOverride(token, date, overrideType) {
    return authFetch(`${BASE_URL}/overrides`, token, {
        method: 'PUT',
        body: JSON.stringify({ date, override_type: overrideType })
    })
}

export async function deleteOverride(token, date) {
    return authFetch(`${BASE_URL}/overrides?date=${date}`, token, {
        method: 'DELETE'
    })
}

export async function fetchSystemStatus() {
    const res = await fetch(`${BASE_URL}/status`)
    if (!res.ok) throw new Error(`Status API error: ${res.status}`)
    return res.json()
}