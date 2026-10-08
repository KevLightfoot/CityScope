import * as maplibregl from "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs";
import { getBoundary } from "./api.js";

let map;
let marker = null;
let housingProperties = [];
let housingVisible = false;


export function setupMap() {

    const css = document.createElement("link");

    css.rel = "stylesheet";
    css.href =
        "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.css";

    document.head.appendChild(css);


    map = new maplibregl.Map({
        container: "map",

        style:
            "https://tiles.openfreemap.org/styles/liberty",

        center: [
            -98.5795,
            39.8283
        ],

        zoom: 4,

        minZoom: 3,
        maxZoom: 16,

        maxBounds: [
            [-124.848974, 24.396308],
            [-66.885444, 49.384358]
        ]
    });


    map.on("styledata", () => {

        const layers =
            map.getStyle().layers || [];


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

    if (!map.isStyleLoaded()) {
        await new Promise(resolve => {
            map.once("load", resolve);
        });
    }

    const latitude =
        Number(city.latitude);

    const longitude =
        Number(city.longitude);


    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {
        return;
    }


    if (marker) {
        marker.remove();
    }


    const popup =
        new maplibregl.Popup({
            offset: 25
        }).setHTML(`
            <strong>${escapeHtml(city.city)}</strong><br>
            ${escapeHtml(city.state)}
        `);


    marker =
        new maplibregl.Marker()
            .setLngLat([
                longitude,
                latitude
            ])
            .setPopup(popup)
            .addTo(map);


    const boundary =
        await getBoundary(
            city.place_GEOID
        );


    const geojson =
        JSON.parse(boundary.geojson);


    if (map.getSource("city-boundary")) {

        map
            .getSource("city-boundary")
            .setData(geojson);

    } else {

        map.addSource(
            "city-boundary",
            {
                type: "geojson",
                data: geojson
            }
        );


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
                    top: 80,
                    bottom: 80,
                    left: 80,
                    right: panelWidth + 80
                },

                maxZoom: 16,

                duration: 1200,

                essential: true
            }
        );

    }


    map.once(
        "moveend",
        () => {

            if (marker) {
                marker.togglePopup();
            }

        }
    );

}


function getGeoJsonBounds(geojson) {

    const bounds =
        new maplibregl.LngLatBounds();


    function walkCoordinates(value) {

        if (!Array.isArray(value)) {
            return;
        }


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


        for (const child of value) {

            walkCoordinates(child);

        }

    }


    if (geojson.type === "Feature") {

        if (geojson.geometry) {

            walkCoordinates(
                geojson.geometry.coordinates
            );

        }

    } else if (geojson.type === "FeatureCollection") {

        for (const feature of geojson.features) {

            if (feature.geometry) {

                walkCoordinates(
                    feature.geometry.coordinates
                );

            }

        }

    } else if (geojson.coordinates) {

        walkCoordinates(
            geojson.coordinates
        );

    }


    if (bounds.isEmpty()) {
        return null;
    }


    return bounds;
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}

export function setHousingProperties(properties) {

    housingProperties = properties || [];
    housingVisible = false;

    if (map.getLayer("housing-properties")) {
        map.setLayoutProperty(
            "housing-properties",
            "visibility",
            "none"
        );
    }

}


export function showHousingProperties() {

    if (!housingProperties.length) {
        return;
    }

    const features = housingProperties
        .map(property => {

            const lat = Number(property.lat);
            const lng = Number(property.lng);

            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lng)
            ) {
                return null;
            }

            return {
                type: "Feature",

                geometry: {
                    type: "Point",
                    coordinates: [lng, lat]
                },

                properties: property
            };

        })
        .filter(Boolean);


    const geojson = {
        type: "FeatureCollection",
        features
    };


    if (!map.getSource("housing-properties")) {

        map.addSource(
            "housing-properties",
            {
                type: "geojson",
                data: geojson
            }
        );

        map.addLayer({
            id: "housing-properties",
            type: "circle",
            source: "housing-properties",

            paint: {
                "circle-radius": 4,
                "circle-color": "#ff6b35",
                "circle-opacity": 0.8,
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1
            }
        });

        map.on(
            "click",
            "housing-properties",
            event => {

                const property =
                    event.features[0].properties;

                const price =
                    property.list_price
                        ? `$${Number(property.list_price).toLocaleString()}`
                        : "—";

                const address =
                    [
                        property.street,
                        property.unit
                    ]
                        .filter(Boolean)
                        .join(" ");


                new maplibregl.Popup({
                    offset: 8
                })
                    .setLngLat(event.lngLat)
                    .setHTML(`
                        <strong>${escapeHtml(address || "Property")}</strong><br>
                        ${escapeHtml(property.city)}, ${escapeHtml(property.state)} ${escapeHtml(property.zip || "")}
                        <br><br>
                        <strong>${price}</strong><br>
                        ${property.beds || "—"} beds ·
                        ${property.baths || "—"} baths<br>
                        ${
                            property.sqft
                                ? `${Number(property.sqft).toLocaleString()} sq ft`
                                : "—"
                        }
                    `)
                    .addTo(map);

            }
        );

        map.on(
            "mouseenter",
            "housing-properties",
            () => {
                map.getCanvas().style.cursor = "pointer";
            }
        );

        map.on(
            "mouseleave",
            "housing-properties",
            () => {
                map.getCanvas().style.cursor = "";
            }
        );

    } else {

        map
            .getSource("housing-properties")
            .setData(geojson);

    }


    map.setLayoutProperty(
        "housing-properties",
        "visibility",
        "visible"
    );

    housingVisible = true;

}


export function hideHousingProperties() {

    if (map.getLayer("housing-properties")) {

        map.setLayoutProperty(
            "housing-properties",
            "visibility",
            "none"
        );

    }

    housingVisible = false;

}


export function isHousingVisible() {
    return housingVisible;
}


export function clearHousingProperties() {

    housingProperties = [];
    housingVisible = false;

    if (map.getLayer("housing-properties")) {

        map.setLayoutProperty(
            "housing-properties",
            "visibility",
            "none"
        );

    }

}