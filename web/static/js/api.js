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

export async function getHousing(city, state) {
    const response = await fetch(
        `${API_BASE}/api/housing/${encodeURIComponent(city)}/${encodeURIComponent(state)}`
    );

    if (!response.ok) {
        throw new Error("Housing data not found");
    }

    return response.json();
}

export async function getPOIs(
    scopeType,
    scopeId,
    category,
    options = {}
) {
    const params = new URLSearchParams();

    if (category) {
        params.set("category", category);
    }

    if (options.search) {
        params.set("search", options.search);
    }

    if (options.startsWith) {
        params.set("starts_with", options.startsWith);
    }

    if (options.limit !== undefined) {
        params.set("limit", options.limit);
    }

    if (options.offset !== undefined) {
        params.set("offset", options.offset);
    }

    const response = await fetch(
        `${API_BASE}/api/pois/${encodeURIComponent(scopeType)}/${encodeURIComponent(scopeId)}?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error("POI data not found");
    }

    return response.json();
}

export async function getNeighborhoodBoundaries(city, state) {
    const response = await fetch(
        `${API_BASE}/api/neighborhood-boundaries/${encodeURIComponent(city)}/${encodeURIComponent(state)}`
    );

    if (!response.ok) {
        throw new Error("Failed to load neighborhood boundaries");
    }

    return response.json();
}