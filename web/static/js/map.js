import * as maplibregl from "https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs";
import { getBoundary, getNeighborhoodBoundaries } from "./api.js";


let map;
let marker = null;
let housingProperties = [];
let housingVisible = false;
let neighborhoodHousingVisible = false;
let neighborhoodHousingProperties = [];
let poiFeatures = [];
let poiVisible = false;
let activePoiCategory = null;
let poiPopup = null;
let currentCity = null;
let currentCityBounds = null;
let neighborhoodVisible = false;
let plottedPoiIds = new Set();
let plottedHousingIds = new Set();

function registerPinImages() {
    if (!map) return;

    const pinColors = {
        food: "#FF1744",
        grocery: "#00C853",
        healthcare: "#F500D4",
        education: "#2979FF",
        shopping: "#FFEA00",
        financial: "#8B4513",
        fitness: "#334155",
        recreation: "#00E5FF",
        entertainment: "#FF9100",
        lodging: "#000000",
        religious: "#00897B",
        housing: "#F472B6",
        default: "#9E9E9E"
    };

    Object.entries(pinColors).forEach(([name, color]) => {
        const imageId = `cityscope-pin-${name}`;

        if (map.hasImage(imageId)) return;

        const canvas = document.createElement("canvas");
        canvas.width = 64;
        canvas.height = 80;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;


        // Draw a clean teardrop pin.
        ctx.beginPath();
        ctx.moveTo(32, 76);
        ctx.bezierCurveTo(26, 65, 5, 43, 5, 27);
        ctx.arc(32, 27, 27, Math.PI, 0, true);
        ctx.bezierCurveTo(59, 43, 38, 65, 32, 76);
        ctx.closePath();

        ctx.fillStyle = color;
        ctx.fill();

        // Subtle dark outline instead of a thick white border.
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#253047";
        ctx.stroke();

        // Solid white center: no transparency cutout.
        ctx.beginPath();
        ctx.arc(32, 27, 8, 0, Math.PI * 2);
        ctx.fillStyle = "#FFFFFF";
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = "#253047";
        ctx.stroke();


        map.addImage(
            imageId,
            ctx.getImageData(0, 0, canvas.width, canvas.height),
            { pixelRatio: 2 }
        );
    });
}


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

    map.on("load", registerPinImages);
    map.on("styledata", () => {

        const layers =
            map.getStyle().layers || [];


        layers.forEach(layer => {

            if (
                layer.type === "symbol" &&
                layer.id !== "poi-properties" &&
                layer.id !== "housing-properties" &&
                layer.id !== "neighborhood-housing-properties"
            ) {

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
                duration: 900,
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


    const bounds = getGeoJsonBounds(geojson);
    currentCityBounds = bounds;


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

function isPointInPolygon(lng, lat, geometry) {
    if (!geometry) return false;

    const ringContainsPoint = ring => {
        let inside = false;

        for (
            let i = 0, j = ring.length - 1;
            i < ring.length;
            j = i++
        ) {
            const [xi, yi] = ring[i];
            const [xj, yj] = ring[j];

            const intersects =
                (yi > lat) !== (yj > lat) &&
                lng < ((xj - xi) * (lat - yi)) /
                    ((yj - yi) || Number.EPSILON) + xi;

            if (intersects) inside = !inside;
        }

        return inside;
    };

    const polygons = geometry.type === "Polygon"
        ? [geometry.coordinates]
        : geometry.type === "MultiPolygon"
            ? geometry.coordinates
            : [];

    return polygons.some(polygon =>
        ringContainsPoint(polygon[0]) &&
        !polygon.slice(1).some(hole => ringContainsPoint(hole))
    );
}

export function plotNeighborhoodHousing(properties, boundary) {
    if (!map || !boundary) return 0;

    const geometry = boundary.type === "Feature"
        ? boundary.geometry
        : boundary;

    const filtered = (properties || []).filter(property => {
        const lat = Number(property.lat);
        const lng = Number(property.lng);

        return Number.isFinite(lat) &&
            Number.isFinite(lng) &&
            isPointInPolygon(lng, lat, geometry);
    });

    console.log("[Neighborhood Housing]", {
        receivedListings: properties?.length,
        validCoordinates: (properties || []).filter(p =>
            Number.isFinite(Number(p.lat)) &&
            Number.isFinite(Number(p.lng))
        ).length,
        matchedNeighborhood: filtered.length,
        geometryType: geometry?.type
    });

    neighborhoodHousingProperties = filtered;

    const features = filtered.map((property, index) => ({
        type: "Feature",
        id: property.id ?? `${property.lng}:${property.lat}:${index}`,
        geometry: {
            type: "Point",
            coordinates: [Number(property.lng), Number(property.lat)]
        },
        properties: property
    }));

    const geojson = {
        type: "FeatureCollection",
        features
    };

    if (!map.getSource("neighborhood-housing-properties")) {
        map.addSource("neighborhood-housing-properties", {
            type: "geojson",
            data: geojson
        });

        map.addLayer({
            id: "neighborhood-housing-properties",
            type: "symbol",
            source: "neighborhood-housing-properties",
            layout: {
                "icon-image": "cityscope-pin-housing",
                "icon-size": 0.85,
                "icon-anchor": "bottom",
                "icon-allow-overlap": true,
                "icon-ignore-placement": true,
                visibility: "visible"
            },
            paint: {
                "icon-opacity": 1
            }
        });

    map.on("click", "neighborhood-housing-properties", event => {

        const feature = event.features?.[0];
        const property = feature?.properties;
        if (!property) return;

        const address = [property.street, property.unit]
            .filter(Boolean)
            .join(" ");

        const price = property.list_price != null
            ? `$${Number(property.list_price).toLocaleString()}`
            : "—";

        new maplibregl.Popup({ offset: 8 })
        .setLngLat(event.lngLat)
        .setHTML(`
            <strong>${escapeHtml(address || "Property")}</strong><br>
            ${escapeHtml(property.city || "")},
            ${escapeHtml(property.state || "")}
            ${escapeHtml(property.zip || "")}
            <br><br>
            <strong>${escapeHtml(price)}</strong><br>
            ${escapeHtml(property.beds ?? "—")} beds ·
            ${escapeHtml(property.baths ?? "—")} baths<br>
            ${property.sqft
                ? `${Number(property.sqft).toLocaleString()} sq ft`
                : "—"}
        `)
        .addTo(map);
});

        map.on("mouseenter", "neighborhood-housing-properties", () => {
            map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", "neighborhood-housing-properties", () => {
            map.getCanvas().style.cursor = "";
        });
    } else {
        map.getSource("neighborhood-housing-properties").setData(geojson);
    }

    map.setLayoutProperty(
        "neighborhood-housing-properties",
        "visibility",
        features.length ? "visible" : "none"
    );

    neighborhoodHousingVisible = features.length > 0;

    return features.length;
}

export function hideNeighborhoodHousing() {
    if (map?.getLayer("neighborhood-housing-properties")) {
        map.setLayoutProperty(
            "neighborhood-housing-properties",
            "visibility",
            "none"
        );
    }

    neighborhoodHousingVisible = false;
}

export function isNeighborhoodHousingVisible() {
    return neighborhoodHousingVisible;
}

export function clearNeighborhoodHousing() {
    hideNeighborhoodHousing();
    neighborhoodHousingProperties = [];

    const source = map?.getSource("neighborhood-housing-properties");

    if (source) {
        source.setData({
            type: "FeatureCollection",
            features: []
        });
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
            type: "symbol",
            source: "housing-properties",
            layout: {
                "icon-image": "cityscope-pin-housing",
                "icon-size": 0.7,
                "icon-anchor": "bottom",
                "icon-allow-overlap": true,
                "icon-ignore-placement": true
            },
            paint: {
                "icon-opacity": [
                    "*",
                    0.95,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ]
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
            type: "symbol",
            source: "poi-properties",
            layout: {
                "icon-image": [
                    "match",
                    ["downcase", ["to-string", ["get", "cityscope_category"]]],
                    "food", "cityscope-pin-food",
                    "grocery", "cityscope-pin-grocery",
                    "healthcare", "cityscope-pin-healthcare",
                    "education", "cityscope-pin-education",
                    "shopping", "cityscope-pin-shopping",
                    "financial", "cityscope-pin-financial",
                    "fitness", "cityscope-pin-fitness",
                    "recreation", "cityscope-pin-recreation",
                    "entertainment", "cityscope-pin-entertainment",
                    "lodging", "cityscope-pin-lodging",
                    "religious", "cityscope-pin-religious",
                    "cityscope-pin-default"
                ],
                "icon-size": 1,
                "icon-anchor": "bottom",
                "icon-allow-overlap": true,
                "icon-ignore-placement": true
            },
            paint: {
                "icon-opacity": [
                    "*",
                    0.95,
                    ["coalesce", ["feature-state", "animationProgress"], 1]
                ]
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


export function clearPOICategory(category) {
    if (!category) return;

    const normalizedCategory = category.toLowerCase();

    poiFeatures = poiFeatures.filter(
        poi =>
            String(poi.cityscope_category || "").toLowerCase() !==
            normalizedCategory
    );

    plottedPoiIds = new Set(
        poiFeatures.map(
            poi => String(
                poi.id ??
                `${Number(poi.longitude)}:${Number(poi.latitude)}:${poi.name || ""}`
            )
        )
    );

    if (poiPopup) {
        poiPopup.remove();
        poiPopup = null;
    }

    const source = map?.getSource("poi-properties");

    if (source) {
        source.setData({
            type: "FeatureCollection",
            features: poiFeatures
                .map(poi => {
                    const lat = Number(poi.latitude);
                    const lng = Number(poi.longitude);

                    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
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
                .filter(Boolean)
        });
    }

    poiVisible = poiFeatures.length > 0;

    if (map?.getLayer("poi-properties")) {
        map.setLayoutProperty(
            "poi-properties",
            "visibility",
            poiVisible ? "visible" : "none"
        );
    }

    activePoiCategory = null;
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
                        const interactiveLayers = [
                            "poi-properties",
                            "housing-properties",
                            "neighborhood-housing-properties"
                        ].filter(layerId => map.getLayer(layerId));

                        const interactiveFeatures = interactiveLayers.length
                            ? map.queryRenderedFeatures(event.point, {
                                layers: interactiveLayers
                            })
                            : [];

                        if (interactiveFeatures.length > 0) {
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

                            const zoomIntoNeighborhood = () => {
                                map.fitBounds(bounds, {
                                    padding: {
                                        top: 60,
                                        bottom: 60,
                                        left: 60,
                                        right: panelWidth + 60
                                    },
                                    maxZoom: 15,
                                    duration: 1400,
                                    essential: true
                                });
                            };

                            if (currentCityBounds) {
                                map.fitBounds(currentCityBounds, {
                                    padding: {
                                        top: 80,
                                        bottom: 80,
                                        left: 80,
                                        right: panelWidth + 80
                                    },
                                    duration: 1800,
                                    essential: true
                                });

                                map.once("moveend", zoomIntoNeighborhood);
                            } else {
                                zoomIntoNeighborhood();
                            }
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