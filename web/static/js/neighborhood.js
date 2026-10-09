import {
    getNeighborhood,
    getNeighborhoodSimilar,
    searchNeighborhoods
} from "./api.js";

import {
    formatNumber
} from "./utils.js";

let currentNeighborhood = null;
let neighborhoodRequestId = 0;

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


function createSimilarNeighborhood(neighborhood) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "similar-neighborhood";
    row.style.width = "100%";
    row.style.textAlign = "left";
    row.style.cursor = "pointer";

    const name = document.createElement("span");
    name.textContent = neighborhood.nbhd_name || "Unnamed neighborhood";

    const location = document.createElement("small");
    location.textContent = `${neighborhood.city}, ${neighborhood.state}`;

    const score = document.createElement("strong");
    score.textContent = neighborhood.match_score ?? "";

    const left = document.createElement("div");
    left.appendChild(name);
    left.appendChild(location);

    row.appendChild(left);
    row.appendChild(score);

    row.addEventListener("click", () => {
        const comparisonRequest = {
            city: neighborhood.city,
            state: neighborhood.state,
            nbhd_id: neighborhood.nbhd_id
        };

        document.dispatchEvent(
            new CustomEvent("neighborhood:compare", {
                detail: comparisonRequest
            })
        );
    });

    return row;
}


async function openNeighborhoodComparison(selectedNeighborhood = null) {
    if (!currentNeighborhood) return;

    document.getElementById("neighborhood-compare-panel")?.remove();

    const panel = document.createElement("aside");
    panel.id = "neighborhood-compare-panel";
    panel.innerHTML = `
        <div class="compare-header">
            <strong>Compare Neighborhoods</strong>
            <button id="neighborhood-compare-close" type="button">×</button>
        </div>

        <div id="neighborhood-compare-current" class="compare-current"></div>

        <input
            id="neighborhood-compare-search"
            type="search"
            placeholder="Search any neighborhood or city..."
            autocomplete="off"
            aria-label="Search neighborhoods to compare"
        >

        <div id="neighborhood-compare-choices">
            Search for a neighborhood to compare.
        </div>

        <div id="neighborhood-compare-table"></div>
    `;

    document.body.appendChild(panel);

    panel.querySelector("#neighborhood-compare-close")
        .addEventListener("click", () => panel.remove());

    const currentLabel = panel.querySelector("#neighborhood-compare-current");
    const searchInput = panel.querySelector("#neighborhood-compare-search");
    const choices = panel.querySelector("#neighborhood-compare-choices");
    const table = panel.querySelector("#neighborhood-compare-table");

    currentLabel.textContent =
        `Comparing with: ${currentNeighborhood.neighborhood}, ` +
        `${currentNeighborhood.city}, ${currentNeighborhood.state}`;

    let timer = null;
    let requestId = 0;

    async function runSearch(query = "") {
        const thisRequest = ++requestId;
        choices.textContent = "Searching neighborhoods...";

        try {
            const candidates = await searchNeighborhoods(
                query,
                query ? "" : currentNeighborhood.city,
                query ? "" : currentNeighborhood.state,
                50
            );

            if (
                thisRequest !== requestId ||
                !document.body.contains(panel)
            ) {
                return;
            }

            choices.replaceChildren();

            const filtered = candidates.filter(item =>
                !(
                    item.city === currentNeighborhood.city &&
                    item.state === currentNeighborhood.state &&
                    Number(item.nbhd_id) === Number(currentNeighborhood.nbhd_id)
                )
            );

            if (!filtered.length) {
                choices.textContent = query
                    ? "No matching neighborhoods found."
                    : "No other neighborhoods found in this city.";
                return;
            }

            filtered.forEach(candidate => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "compare-city-result";

                const name = document.createElement("strong");
                name.textContent = candidate.nbhd_name || "Unnamed neighborhood";

                const location = document.createElement("small");
                location.textContent = `${candidate.city}, ${candidate.state}`;

                button.replaceChildren(name, location);

                button.addEventListener("click", async () => {
                    choices.textContent = "";
                    table.textContent = "Loading comparison...";

                    try {
                        await renderNeighborhoodComparison(candidate, panel);
                    } catch (error) {
                        console.error("Neighborhood comparison failed:", error);
                        table.textContent =
                            "Unable to load this comparison. Please try another neighborhood.";
                    }
                });

                choices.appendChild(button);
            });
        } catch (error) {
            if (thisRequest !== requestId) return;

            console.error("Neighborhood search failed:", error);
            choices.textContent =
                "Neighborhood search failed. Please try again.";
        }
    }

    searchInput.addEventListener("input", () => {
        window.clearTimeout(timer);

        const query = searchInput.value.trim();

        timer = window.setTimeout(() => {
            runSearch(query);
        }, 250);
    });

    if (selectedNeighborhood) {
        await renderNeighborhoodComparison(selectedNeighborhood, panel);
    } else {
        await runSearch();
    }
}
async function renderNeighborhoodComparison(other, panel) {
    if (!currentNeighborhood) {
        return;
    }

    const table = panel.querySelector("#neighborhood-compare-table");
    const choices = panel.querySelector("#neighborhood-compare-choices");

    table.textContent = "Loading comparison...";

    const current = await getNeighborhood(
        currentNeighborhood.city,
        currentNeighborhood.state,
        currentNeighborhood.nbhd_id
    );

    const comparison = await getNeighborhood(
        other.city,
        other.state,
        other.nbhd_id
    );

    const formatNumberValue = value => {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const number = Number(value);
        return Number.isFinite(number) ? number.toLocaleString(undefined, {
            maximumFractionDigits: 1
        }) : "—";
    };

    const formatPercentValue = value => {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const number = Number(value);
        return Number.isFinite(number) ? `${number.toFixed(1)}%` : "—";
    };

    const formatCurrencyValue = value => {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const number = Number(value);
        return Number.isFinite(number)
            ? `$${Math.round(number).toLocaleString()}`
            : "—";
    };

    const grid = document.createElement("div");
    grid.className = "compare-grid neighborhood-compare-grid";

    const addCell = (value, className = "") => {
        const cell = document.createElement("div");
        cell.textContent = value;
        if (className) cell.className = className;
        grid.appendChild(cell);
    };

    addCell("");
    addCell(`${current.nbhd_name || currentNeighborhood.neighborhood}`);
    addCell(`${comparison.nbhd_name || other.nbhd_name}`);

    const addSection = title => addCell(title, "compare-category");

    const addMetric = (label, field, formatter = formatNumberValue) => {
        addCell(label);
        addCell(formatter(current[field]));
        addCell(formatter(comparison[field]));
    };

    addSection("DEMOGRAPHICS");
    addMetric("Population", "pop");
    addMetric("White", "white_pct", formatPercentValue);
    addMetric("Black", "black_pct", formatPercentValue);
    addMetric("Hispanic", "hisp_pct", formatPercentValue);
    addMetric("Asian", "asian_pct", formatPercentValue);
    addMetric("American Indian / Alaska Native", "aian_pct", formatPercentValue);
    addMetric("Native Hawaiian / Pacific Islander", "nhpi_pct", formatPercentValue);
    addMetric("Other Race", "other_pct", formatPercentValue);
    addMetric("Two or More Races", "two_pct", formatPercentValue);

    addSection("HOUSING");
    addMetric("Properties", "property_count");
    addMetric("Median List Price", "median_list_price", formatCurrencyValue);
    addMetric("Average List Price", "avg_list_price", formatCurrencyValue);
    addMetric("Median Price / Sq Ft", "median_price_per_sqft", formatCurrencyValue);
    addMetric("Average Sq Ft", "avg_sqft");

    addSection("POINTS OF INTEREST");
    addMetric("Total POIs", "poi_count");
    addMetric("Food", "food_count");
    addMetric("Grocery", "grocery_count");
    addMetric("Healthcare", "healthcare_count");
    addMetric("Education", "education_count");
    addMetric("Shopping", "shopping_count");
    addMetric("Fitness", "fitness_count");
    addMetric("Recreation", "recreation_count");
    addMetric("Entertainment", "entertainment_count");

    table.replaceChildren(grid);
    choices.replaceChildren();

    const chooseAnother = document.createElement("button");
    chooseAnother.type = "button";
    chooseAnother.className = "compare-city-result";
    chooseAnother.textContent = "← Choose another neighborhood";
    chooseAnother.addEventListener("click", () => {
        table.replaceChildren();
        openNeighborhoodComparison();
    });

    choices.appendChild(chooseAnother);
}

export function setupNeighborhood() {
    window.addEventListener(
        "cityscope:neighborhood-selected",
        async event => {
            const requestId = ++neighborhoodRequestId;

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

                // Ignore responses from older clicks.
                if (requestId !== neighborhoodRequestId) {
                    return;
                }

                renderNeighborhood(
                    data,
                    city,
                    state,
                    neighborhood
                );

            } catch (error) {
                if (requestId !== neighborhoodRequestId) {
                    return;
                }

                console.error(
                    "Failed to load neighborhood:",
                    error
                );
            }
        }
    );

    const closeButton = document.getElementById("close-neighborhood-panel");

    if (closeButton) {
        closeButton.addEventListener("click", closeNeighborhoodPanel);
    }

    const compareButton = document.getElementById("compare-neighborhood-button");

    if (compareButton) {
        compareButton.addEventListener("click", () => {
            openNeighborhoodComparison();
        });
    }
    document.addEventListener("neighborhood:compare", event => {
        openNeighborhoodComparison(event.detail);
    });
}

export function getCurrentNeighborhood() {
    return currentNeighborhood;
}

export function clearNeighborhood() {
    neighborhoodRequestId++;
    currentNeighborhood = null;
    closeNeighborhoodPanel();
}