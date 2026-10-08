const API_BASE = "http://34.67.89.177:8000";

export async function searchCities(query) {
    const response = await fetch(
        `${API_BASE}/api/cities?q=${encodeURIComponent(query)}`
    );

    if (!response.ok) {
        throw new Error("Search failed");
    }

    return response.json();
}

export async function getCity(city, state) {
    const response = await fetch(
        `${API_BASE}/api/city/${encodeURIComponent(city)}/${encodeURIComponent(state)}`
    );

    if (!response.ok) {
        throw new Error("City not found");
    }

    return response.json();
}

export async function getBoundary(geoid) {
    const response = await fetch(
        `${API_BASE}/api/boundary/${encodeURIComponent(geoid)}`
    );

    if (!response.ok) {
        throw new Error("Boundary not found");
    }

    return response.json();
}

export async function getWeather(geoid) {
    const response = await fetch(
        `${API_BASE}/api/weather/${encodeURIComponent(geoid)}`
    );

    if (!response.ok) {
        throw new Error("Weather data not found");
    }

    return response.json();
}