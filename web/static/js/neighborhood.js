import {
    getNeighborhood,
    getNeighborhoodSimilar
} from "./api.js";

import {
    formatNumber
} from "./utils.js";

let currentNeighborhood = null;

function setText(id, value) {
    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    element.textContent =
        value;
}

function setPercent(id, value) {
    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value))
    ) {
        element.textContent = "—";
        return;
    }

    element.textContent =
        `${Number(value).toFixed(1)}%`;
}

function formatWholeCurrency(value) {
    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value))
    ) {
        return "—";
    }

    return `$${Math.round(Number(value)).toLocaleString()}`;
}

function showNeighborhoodPanel() {
    const panel =
        document.getElementById(
            "neighborhood-panel"
        );

    if (!panel) {
        return;
    }

    panel.classList.remove("hidden");
}

function closeNeighborhoodPanel() {
    const panel =
        document.getElementById(
            "neighborhood-panel"
        );

    if (!panel) {
        return;
    }

    panel.classList.add("hidden");
}

function renderNeighborhood(data, city, state, neighborhood) {
    currentNeighborhood = {
        city,
        state,
        neighborhood,
        nbhd_id: data.nbhd_id
    };

    showNeighborhoodPanel();

    setText(
        "neighborhood-name",
        data.nbhd_name ||
        neighborhood ||
        "Neighborhood"
    );

    setText(
        "neighborhood-location",
        `${city}, ${state}`
    );

    // ---------------------------------------------------------
    // DEMOGRAPHICS
    // ---------------------------------------------------------

    setText(
        "neighborhood-population",
        formatNumber(data.pop)
    );

    setPercent(
        "neighborhood-white",
        data.white_pct
    );

    setPercent(
        "neighborhood-black",
        data.black_pct
    );

    setPercent(
        "neighborhood-hispanic",
        data.hisp_pct
    );

    setPercent(
        "neighborhood-asian",
        data.asian_pct
    );

    setPercent(
        "neighborhood-aian",
        data.aian_pct
    );

    setPercent(
        "neighborhood-nhpi",
        data.nhpi_pct
    );

    setPercent(
        "neighborhood-other",
        data.other_pct
    );

    setPercent(
        "neighborhood-two-races",
        data.two_pct
    );

    // ---------------------------------------------------------
    // HOUSING
    // ---------------------------------------------------------

    setText(
        "neighborhood-property-count",
        formatNumber(data.property_count)
    );

    setText(
        "neighborhood-home-price",
        formatWholeCurrency(
            data.median_list_price
        )
    );

    setText(
        "neighborhood-avg-price",
        formatWholeCurrency(
            data.avg_list_price
        )
    );

    setText(
        "neighborhood-price-sqft",
        formatWholeCurrency(
            data.median_price_per_sqft
        )
    );

    setText(
        "neighborhood-avg-sqft",
        data.avg_sqft != null
            ? `${Math.round(
                Number(data.avg_sqft)
            ).toLocaleString()} sq ft`
            : "—"
    );

    // ---------------------------------------------------------
    // POINTS OF INTEREST
    // ---------------------------------------------------------

    const poiFields = [
        ["poi-count", "poi_count"],
        ["food-count", "food_count"],
        ["grocery-count", "grocery_count"],
        ["healthcare-count", "healthcare_count"],
        ["education-count", "education_count"],
        ["shopping-count", "shopping_count"],
        ["fitness-count", "fitness_count"],
        ["recreation-count", "recreation_count"],
        ["entertainment-count", "entertainment_count"],
        ["restaurant-count", "restaurant_count"],
        ["park-count", "park_count"],
        ["gym-count", "gym_count"],
        ["hospital-count", "hospital_count"],
        ["school-count", "school_count"]
    ];

    poiFields.forEach(([id, field]) => {
        setText(
            `neighborhood-${id}`,
            formatNumber(data[field])
        );
    });

    // ---------------------------------------------------------
    // CLOSE SECTIONS
    // ---------------------------------------------------------

    document
        .querySelectorAll(
            "#neighborhood-panel .panel-section"
        )
        .forEach(section => {
            section.classList.remove(
                "expanded"
            );
        });

    loadSimilarNeighborhoods(
        city,
        neighborhood
    );
}

async function loadSimilarNeighborhoods(
    city,
    neighborhood
) {
    const container =
        document.getElementById(
            "neighborhood-similar-content"
        );

    if (!container) {
        return;
    }

    container.textContent =
        "Loading...";

    try {
        const data =
            await getNeighborhoodSimilar(
                city,
                neighborhood
            );

        const sameCity =
            data.same_city || [];

        const otherCities =
            data.other_cities || [];

        container.innerHTML = "";

        if (
            !sameCity.length &&
            !otherCities.length
        ) {
            container.textContent =
                "No similar neighborhoods found.";
            return;
        }

        if (sameCity.length) {
            const heading =
                document.createElement(
                    "div"
                );

            heading.className =
                "similar-group-title";

            heading.textContent =
                "Same City";

            container.appendChild(
                heading
            );

            sameCity.forEach(
                neighborhood => {
                    container.appendChild(
                        createSimilarNeighborhood(
                            neighborhood
                        )
                    );
                }
            );
        }

        if (otherCities.length) {
            const heading =
                document.createElement(
                    "div"
                );

            heading.className =
                "similar-group-title";

            heading.textContent =
                "Other Cities";

            container.appendChild(
                heading
            );

            otherCities.forEach(
                neighborhood => {
                    container.appendChild(
                        createSimilarNeighborhood(
                            neighborhood
                        )
                    );
                }
            );
        }

    } catch (error) {
        console.error(
            "Failed to load similar neighborhoods:",
            error
        );

        container.textContent =
            "Similar neighborhoods unavailable.";
    }
}

function createSimilarNeighborhood(
    neighborhood
) {
    const row =
        document.createElement(
            "div"
        );

    row.className =
        "similar-neighborhood";

    const name =
        document.createElement(
            "span"
        );

    name.textContent =
        neighborhood.nbhd_name;

    const location =
        document.createElement(
            "small"
        );

    location.textContent =
        `${neighborhood.city}, ${neighborhood.state}`;

    const score =
        document.createElement(
            "strong"
        );

    score.textContent =
        `${neighborhood.match_score}`;

    const left =
        document.createElement(
            "div"
        );

    left.appendChild(name);
    left.appendChild(location);

    row.appendChild(left);
    row.appendChild(score);

    return row;
}

export function setupNeighborhood() {
    window.addEventListener(
        "cityscope:neighborhood-selected",
        async event => {
            const {
                city,
                state,
                neighborhood,
                nbhd_id
            } = event.detail;

            try {
                const data =
                    await getNeighborhood(
                        city,
                        state,
                        nbhd_id
                    );

                renderNeighborhood(
                    data,
                    city,
                    state,
                    neighborhood
                );

            } catch (error) {
                console.error(
                    "Failed to load neighborhood:",
                    error
                );
            }
        }
    );

    const closeButton =
        document.getElementById(
            "close-neighborhood-panel"
        );

    if (closeButton) {
        closeButton.addEventListener(
            "click",
            closeNeighborhoodPanel
        );
    }
}

export function getCurrentNeighborhood() {
    return currentNeighborhood;
}

export function clearNeighborhood() {
    currentNeighborhood = null;
    closeNeighborhoodPanel();
}