import * as maplibregl from "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs";
import { getBoundary } from "./api.js";

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

                map.setLayoutProperty(
                    layer.id,
                    "visibility",
                    "none"
                );

            }

            if (
                layer.type === "line" &&
                (
                    layer.id.includes("road") ||
                    layer.id.includes("street") ||
                    layer.id.includes("highway") ||
                    layer.id.includes("transport")
                )
            ) {

                map.setLayoutProperty(
                    layer.id,
                    "visibility",
                    "none"
                );

            }

        });

    });


    return map;
}


export async function showCityOnMap(city) {

    const latitude = Number(city.latitude);
    const longitude = Number(city.longitude);

    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {
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


    // =========================
    // GET CITY BOUNDARY
    // =========================

    const boundary =
        await getBoundary(city.place_GEOID);

    const geojson =
        JSON.parse(boundary.geojson);


    // =========================
    // DRAW / UPDATE BOUNDARY
    // =========================

    if (map.getSource("city-boundary")) {

        map
            .getSource("city-boundary")
            .setData(geojson);

    } else {

        map.addSource("city-boundary", {
            type: "geojson",
            data: geojson
        });


        map.addLayer({
            id: "city-boundary-fill",
            type: "fill",
            source: "city-boundary",

            paint: {
                "fill-color": "#3388ff",
                "fill-opacity": 0.12
            }
        });


        map.addLayer({
            id: "city-boundary-outline",
            type: "line",
            source: "city-boundary",

            paint: {
                "line-color": "#3388ff",
                "line-width": 3,
                "line-opacity": 0.9
            }
        });

    }


    // =========================
    // FIT CITY TO AVAILABLE MAP
    // =========================

    const bounds =
        getGeoJsonBounds(geojson);


    if (bounds) {

        const panel =
            document.getElementById("city-panel");

        const panelWidth =
            panel
                ? panel.getBoundingClientRect().width
                : 760;


        map.fitBounds(
            bounds,
            {
                padding: {
                    top: 70,
                    bottom: 70,
                    left: 70,
                    right: panelWidth + 70
                },

                maxZoom: 11.5,

                duration: 1000
            }
        );

    }


    map.once("moveend", () => {

        marker.togglePopup();

    });

}


function getGeoJsonBounds(geojson) {

    const bounds =
        new maplibregl.LngLatBounds();


    function walkCoordinates(value) {

        if (!Array.isArray(value)) {
            return;
        }


        // A coordinate pair: [longitude, latitude]
        if (
            value.length >= 2 &&
            typeof value[0] === "number" &&
            typeof value[1] === "number"
        ) {

            bounds.extend([
                value[0],
                value[1]
            ]);

            return;
        }


        value.forEach(
            walkCoordinates
        );

    }


    if (geojson.type === "Feature") {

        walkCoordinates(
            geojson.geometry.coordinates
        );

    } else if (
        geojson.type === "FeatureCollection"
    ) {

        geojson.features.forEach(feature => {

            walkCoordinates(
                feature.geometry.coordinates
            );

        });

    } else if (geojson.coordinates) {

        walkCoordinates(
            geojson.coordinates
        );

    }


    return bounds.isEmpty()
        ? null
        : bounds;
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}