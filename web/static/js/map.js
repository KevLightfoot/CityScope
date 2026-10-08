import * as maplibregl from "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs";

let map;
let marker = null;

export function setupMap() {
    const css = document.createElement("link");

    css.rel = "stylesheet";
    css.href =
        "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.css";

    document.head.appendChild(css);

    map = new maplibregl.Map({
        container: "map",
        style: "https://tiles.openfreemap.org/styles/liberty",
        center: [-98.5795, 39.8283],
        zoom: 4,
        minZoom: 3,
        maxZoom: 12,
        maxBounds: [
            [-124.848974, 24.396308],
            [-66.885444, 49.384358]
        ]
    });

    map.on("styledata", () => {
        const layers = map.getStyle().layers || [];

        layers.forEach(layer => {
            if (layer.type === "symbol") {
                map.setLayoutProperty(layer.id, "visibility", "none");
            }
        });
    });

    return map;
}

export function showCityOnMap(city) {
    const latitude = Number(city.latitude);
    const longitude = Number(city.longitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        return;
    }

    if (marker) {
        marker.remove();
    }

    const popup = new maplibregl.Popup({
        offset: 25
    }).setHTML(`
        <strong>${escapeHtml(city.city)}</strong><br>
        ${escapeHtml(city.state)}
    `);

    marker = new maplibregl.Marker()
        .setLngLat([longitude, latitude])
        .setPopup(popup)
        .addTo(map);

    map.flyTo({
        center: [longitude, latitude],
        zoom: 10,
        duration: 1200
    });

    map.once("moveend", () => {
        marker.togglePopup();
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}