import { escapeHtml } from "./utils.js";

let map;
let marker = null;

export function setupMap() {
    map = L.map("map", {
        minZoom: 3,
        maxZoom: 12
    }).setView([39.8283, -98.5795], 4);

    L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        {
            attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
        }
    ).addTo(map);

    map.setMaxBounds([
        [24.396308, -124.848974],
        [49.384358, -66.885444]
    ]);

    return map;
}

export function showCityOnMap(city) {
    const latitude = Number(city.latitude);
    const longitude = Number(city.longitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        return;
    }

    if (marker) {
        map.removeLayer(marker);
    }

    marker = L.marker([latitude, longitude])
        .addTo(map)
        .bindPopup(`
            <strong>${escapeHtml(city.city)}</strong><br>
            ${escapeHtml(city.state)}
        `);

    map.flyTo([latitude, longitude], 10, {
        duration: 1.2
    });

    map.once("moveend", () => marker.openPopup());
}