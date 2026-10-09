import * as maplibregl from "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs";
import { getBoundary, getNeighborhoodBoundaries } from "./api.js";


let map;
let marker = null;
let housingProperties = [];
let housingVisible = false;
let poiFeatures = [];
let poiVisible = false;
let activePoiCategory = null;
let poiPopup = null;
let currentCity = null;
let neighborhoodVisible = false;
let plottedPoiIds = new Set();
let plottedHousingIds = new Set();


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

    currentCity = city;


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


    const cityMarkerIcon = marker.getElement().querySelector("svg");

    if (cityMarkerIcon) {
        cityMarkerIcon.animate(
            [
                {
                    transform: "translateY(-12px) scale(0.65)",
                    opacity: 0
                },
                {
                    transform: "translateY(2px) scale(1.12)",
                    opacity: 1,
                    offset: 0.75
                },
                {
                    transform: "translateY(0) scale(1)",
                    opacity: 1
                }
            ],
            {
                duration: 500,
                easing: "ease-out"
            }
        );
    }



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





function animateMarkerLayer(layerId, sourceId, features) {
    if (!map.getLayer(layerId) || !map.getSource(sourceId)) {
        return;
    }

    const ids = features
        .map(feature => feature.id)
        .filter(id => id !== undefined && id !== null);

    if (ids.length === 0) {
        return;
    }

    const duration = 450;
    const startTime = performance.now();

    ids.forEach(id => {
        map.setFeatureState(
            { source: sourceId, id },
            { animationProgress: 0 }
        );
    });

    function frame(now) {
        const t = Math.min((now - startTime) / duration, 1);

        // Ease out with a slight overshoot to create a visible bounce.
        const progress = t < 1
            ? Math.max(
                0,
                Math.min(
                    1.15,
                    1 +
                    2.70158 * Math.pow(t - 1, 3) +
                    1.70158 * Math.pow(t - 1, 2)
                )
            )
            : 1;

        ids.forEach(id => {
            map.setFeatureState(
                { source: sourceId, id },
                { animationProgress: Math.max(0, progress) }
            );
        });

        if (t < 1) {
            requestAnimationFrame(frame);
        } else {
            ids.forEach(id => {
                map.setFeatureState(
                    { source: sourceId, id },
                    { animationProgress: 1 }
                );
            });
        }
    }

    requestAnimationFrame(frame);
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
    plottedHousingIds.clear();
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

                id: property.id ?? `${lng}:${lat}:${property.address || ""}`,

                geometry: {
                    type: "Point",
                    coordinates: [lng, lat]
                },

                properties: property
            };


        })
        .filter(Boolean);


    const currentHousingIds = new Set(
        features.map(feature => feature.id)
    );

    const newHousingFeatures = features.filter(
        feature => !plottedHousingIds.has(feature.id)
    );

    plottedHousingIds = currentHousingIds;



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
                "circle-radius": [
                    "*",
                    6,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ],
                "circle-color": "#F472B6",
                "circle-opacity": [
                    "*",
                    0.8,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ],
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


    if (newHousingFeatures.length > 0) {
        map.once("idle", () => {
            animateMarkerLayer(
                "housing-properties",
                "housing-properties",
                newHousingFeatures
            );
        });
    }


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
    plottedHousingIds.clear();
    housingVisible = false;

    if (map.getLayer("housing-properties")) {

        map.setLayoutProperty(
            "housing-properties",
            "visibility",
            "none"
        );

    }

}

export function setPOIs(pois) {
    const incoming = pois || [];

    // An empty list is the explicit Reset POIs action.
    if (incoming.length === 0) {
        poiFeatures = [];
        plottedPoiIds.clear();
        poiVisible = false;
        activePoiCategory = null;

        if (poiPopup) {
            poiPopup.remove();
            poiPopup = null;
        }

        if (map?.getLayer("poi-properties")) {
            map.setLayoutProperty(
                "poi-properties",
                "visibility",
                "none"
            );
        }

        return;
    }

    // Merge new results without removing previously plotted categories.
    const combined = new Map(
        poiFeatures.map(poi => [
            String(poi.id ?? `${poi.longitude}:${poi.latitude}:${poi.name || ""}`),
            poi
        ])
    );

    incoming.forEach(poi => {
        const id = String(
            poi.id ?? `${poi.longitude}:${poi.latitude}:${poi.name || ""}`
        );
        combined.set(id, poi);
    });

    poiFeatures = [...combined.values()];
}

export function showPOIs(category) {
    const features = poiFeatures
        .map(poi => {
            const lat = Number(poi.latitude);
            const lng = Number(poi.longitude);

            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lng)
            ) {
                return null;
            }


            return {
                type: "Feature",

                id: poi.id ?? `${lng}:${lat}:${poi.name || ""}`,

                geometry: {
                    type: "Point",
                    coordinates: [lng, lat]
                },

                properties: poi
            };

        })
        .filter(Boolean);


    const currentPoiIds = new Set(
        features.map(feature => String(feature.id))
    );

    const newPoiFeatures = features.filter(
        feature => !plottedPoiIds.has(String(feature.id))
    );

    currentPoiIds.forEach(id => plottedPoiIds.add(id));


    const geojson = {
        type: "FeatureCollection",
        features
    };

    if (!map.getSource("poi-properties")) {

        map.addSource(
            "poi-properties",
            {
                type: "geojson",
                data: geojson
            }
        );

        map.addLayer({
            id: "poi-properties",
            type: "circle",
            source: "poi-properties",


            paint: {
                "circle-radius": [
                    "*",
                    7.5,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ],
                "circle-color": [
                    "match",
                    ["downcase", ["to-string", ["get", "cityscope_category"]]],
                    "food", "#FF1744",
                    "grocery", "#00C853",
                    "healthcare", "#F500D4",
                    "education", "#2979FF",
                    "shopping", "#FFEA00",
                    "financial", "#8B4513",
                    "fitness", "#FFFFFF",
                    "recreation", "#00E5FF",
                    "entertainment", "#FF9100",
                    "lodging", "#000000",
                    "religious", "#00897B",
                    "#9E9E9E"
                ],
                "circle-opacity": [
                    "*",
                    0.85,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ],
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1
            }

        });

        map.on(
            "click",
            "poi-properties",
            event => {

                const poi = event.features[0].properties;
                if (poiPopup) {
                    poiPopup.remove();
                }

                poiPopup = new maplibregl.Popup({
                    offset: 8
                })
                    .setLngLat(event.lngLat)
                    .setHTML(`
                        <strong>${escapeHtml(poi.name || "Place")}</strong><br>
                        ${escapeHtml(poi.category || "")}
                    `)
                    .addTo(map);
            }
        );

        map.on(
            "mouseenter",
            "poi-properties",
            () => {
                map.getCanvas().style.cursor = "pointer";
            }
        );

        map.on(
            "mouseleave",
            "poi-properties",
            () => {
                map.getCanvas().style.cursor = "";
            }
        );

    } else {

        map
            .getSource("poi-properties")
            .setData(geojson);

    }

    map.setLayoutProperty(
        "poi-properties",
        "visibility",
        "visible"
    );

    poiVisible = true;

    if (newPoiFeatures.length > 0) {
        map.once("idle", () => {
            animateMarkerLayer(
                "poi-properties",
                "poi-properties",
                newPoiFeatures
            );
        });
    }

    activePoiCategory = category;
}

export function hidePOIs() {

    if (map.getLayer("poi-properties")) {

        map.setLayoutProperty(
            "poi-properties",
            "visibility",
            "none"
        );

    }

    poiVisible = false;
    activePoiCategory = null;
}

export function clearPOIs() {

    poiFeatures = [];
    plottedPoiIds.clear();
    poiVisible = false;
    activePoiCategory = null;

    if (map.getLayer("poi-properties")) {

        map.setLayoutProperty(
            "poi-properties",
            "visibility",
            "none"
        );

    }
}

export function isPOIVisible() {
    return poiVisible;
}

export function closePOIPopup() {
    if (poiPopup) {
        poiPopup.remove();
        poiPopup = null;
    }
}

export async function showNeighborhoodBoundaries() {

    if (!map || !currentCity) {
        return;
    }

    neighborhoodVisible = true;

    try {

        const data = await getNeighborhoodBoundaries(
            currentCity.city,
            currentCity.state
        );

        const features = data.results.map(neighborhood => ({
            type: "Feature",
            geometry: JSON.parse(neighborhood.geojson),
            properties: {
                nbhd_id: neighborhood.nbhd_id,
                neighborhood: neighborhood.neighborhood,
                city: neighborhood.city,
                state: neighborhood.state
            }
        }));

        const geojson = {
            type: "FeatureCollection",
            features
        };

        const addNeighborhoodLayers = () => {

            if (map.getSource("neighborhood-boundaries")) {
                map.getSource("neighborhood-boundaries")
                    .setData(geojson);
            } else {

                map.addSource("neighborhood-boundaries", {
                    type: "geojson",
                    data: geojson
                });

                map.addLayer({
                    id: "neighborhood-boundaries-fill",
                    type: "fill",
                    source: "neighborhood-boundaries",
                    paint: {
                        "fill-color": "#630b0b",
                        "fill-opacity": 0.06
                    }
                });

                map.addLayer({
                    id: "neighborhood-boundaries-outline",
                    type: "line",
                    source: "neighborhood-boundaries",
                    paint: {
                        "line-color": "#630b0b",
                        "line-width": 2,
                        "line-opacity": 0.85
                    }
                });

                map.on(
                    "click",
                    "neighborhood-boundaries-fill",
                    event => {

                        // If a POI was clicked at this location, let its handler own the click.
                        const poiAtClick = map.queryRenderedFeatures(event.point, {
                            layers: ["poi-properties"]
                        });

                        if (poiAtClick.length > 0) {
                            return;
                        }

                        const feature =
                            event.features?.[0];

                        if (!feature) {
                            return;
                        }

                        const bounds = getGeoJsonBounds(feature.geometry);


                        if (bounds) {
                            const neighborhoodPanel =
                                document.getElementById(
                                    "neighborhood-panel"
                                );

                            const panelWidth =
                                neighborhoodPanel &&
                                !neighborhoodPanel.classList.contains("hidden")
                                    ? neighborhoodPanel.getBoundingClientRect().width
                                    : 0;

                            map.fitBounds(bounds, {
                                padding: {
                                    top: 60,
                                    bottom: 60,
                                    left: 60,
                                    right: panelWidth + 60
                                },
                                maxZoom: 15,
                                duration: 1000,
                                essential: true
                            });
                        }


                        const name =
                            feature.properties?.neighborhood;

                        const nbhdId =
                            feature.properties?.nbhd_id;

                        const city =
                            feature.properties?.city;

                        const state =
                            feature.properties?.state;

                        closePOIPopup();
                        hidePOIs();
                        window.dispatchEvent(new Event("cityscope:neighborhood-changing"));

                        window.cityscopeCurrentNeighborhood = {
                            city,
                            state,
                            neighborhood: name,
                            nbhd_id: nbhdId
                        };

                        window.dispatchEvent(
                            new CustomEvent("cityscope:neighborhood-selected", {
                                detail: {
                                    city,
                                    state,
                                    neighborhood: name,
                                    nbhd_id: nbhdId
                                }
                            })
                        );

                        new maplibregl.Popup()
                            .setLngLat(event.lngLat)
                            .setHTML(
                                `<strong>${escapeHtml(name || "Neighborhood")}</strong>`
                            )
                            .addTo(map);
                    }
                );

                map.on(
                    "mouseenter",
                    "neighborhood-boundaries-fill",
                    () => {
                        map.getCanvas().style.cursor = "pointer";
                    }
                );

                map.on(
                    "mouseleave",
                    "neighborhood-boundaries-fill",
                    () => {
                        map.getCanvas().style.cursor = "";
                    }
                );
            }

            map.setLayoutProperty(
                "neighborhood-boundaries-fill",
                "visibility",
                "visible"
            );

            map.setLayoutProperty(
                "neighborhood-boundaries-outline",
                "visibility",
                "visible"
            );
        };

        if (map.isStyleLoaded()) {
            addNeighborhoodLayers();
        } else {
            map.once("load", addNeighborhoodLayers);
        }

    } catch (error) {
        console.error(
            "Failed to load neighborhood boundaries:",
            error
        );
    }
}


export function hideNeighborhoodBoundaries() {

    neighborhoodVisible = false;

    if (!map) {
        return;
    }

    if (map.getLayer("neighborhood-boundaries-fill")) {
        map.setLayoutProperty(
            "neighborhood-boundaries-fill",
            "visibility",
            "none"
        );
    }

    if (map.getLayer("neighborhood-boundaries-outline")) {
        map.setLayoutProperty(
            "neighborhood-boundaries-outline",
            "visibility",
            "none"
        );
    }
}