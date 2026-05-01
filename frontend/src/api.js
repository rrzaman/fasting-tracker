const BASE_URL = import.meta.env.VITE_API_URL

export async function fetchHealthData(days = 90) {
    const res = await fetch(`${BASE_URL}/health?days=${days}`)
    if (!res.ok) throw new Error(`Health API error: ${res.status}`)
    const json = await res.json()
    return json.data
}

export async function fetchFastingData(daysBack = 365, daysForward = 90) {
    const res = await fetch(`${BASE_URL}/fasting?days_back=${daysBack}&days_forward=${daysForward}`)
    if (!res.ok) throw new Error(`Fasting API error: ${res.status}`)
    const json = await res.json()
    return json.data
}

export async function fetchOverrides() {
    const res = await fetch(`${BASE_URL}/overrides`)
    if (!res.ok) throw new Error(`Overrides API error: ${res.status}`)
    const json = await res.json()
    return json.data
}

export async function createOverride(date, overrideType) {
    const res = await fetch(`${BASE_URL}/overrides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date, override_type: overrideType })
    })
    if (!res.ok) throw new Error(`Create override error: ${res.status}`)
    return res.json()
}

export async function updateOverride(date, overrideType) {
    const res = await fetch(`${BASE_URL}/overrides`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date, override_type: overrideType })
    })
    if (!res.ok) throw new Error(`Update override error: ${res.status}`)
    return res.json()
}

export async function deleteOverride(date) {
    const res = await fetch(`${BASE_URL}/overrides?date=${date}`, {
        method: "DELETE"
    })
    if (!res.ok) throw new Error(`Delete override error: ${res.status}`)
    return res.json()
}

export async function fetchSystemStatus() {
    const res = await fetch(`${BASE_URL}/status`)
    if (!res.ok) throw new Error(`Status API error: ${res.status}`)
    return res.json()
}