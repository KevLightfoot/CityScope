let map;
let marker = null;

export function setupMap() {
    map = L.map("map", {
        minZoom: 3,
        maxZoom: 12,
        zoomControl: true
    }).setView([39.8283, -98.5795], 4);

    map.getContainer().style.background = "#eef1f3";

    loadStateBoundaries();

    map.setMaxBounds([
        [24.396308, -124.848974],
        [49.384358, -66.885444]
    ]);

    return map;
}

async function loadStateBoundaries() {
    const url =
        "https://tigerweb.geo.census.gov/arcgis/rest/services/" +
        "TIGERweb/USLandmass/MapServer/0/query" +
        "?where=STATE%3C60" +
        "&outFields=GEOID" +
        "&returnGeometry=true" +
        "&outSR=4326" +
        "&f=geojson";

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Failed to load state boundaries");
        }

        const data = await response.json();

        L.geoJSON(data, {
            style: {
                color: "#aeb6bd",
                weight: 1,
                fillColor: "#f5f6f7",
                fillOpacity: 1
            }
        }).addTo(map);

    } catch (error) {
        console.error("State boundaries failed to load:", error);
    }
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
            <strong>${city.city}</strong><br>
            ${city.state}
        `);

    map.flyTo([latitude, longitude], 10, {
        duration: 1.2
    });

    map.once("moveend", () => marker.openPopup());
}