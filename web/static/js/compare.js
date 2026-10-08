import { searchCities, getCity } from "./api.js";

let currentCity = null;

export function setupCompare() {

    const button =
        document.getElementById("compare-city-button");

    if (!button) {
        return;
    }

    button.onclick = openComparePanel;
}


async function openComparePanel() {

    const cityName =
        document.getElementById("city-name")?.textContent.trim();

    const state =
        document.getElementById("city-location")?.textContent.trim();

    if (!cityName || !state) {
        return;
    }

    currentCity =
        await getCity(cityName, state);

    document
        .getElementById("compare-panel")
        ?.remove();

    const panel =
        document.createElement("aside");

    panel.id = "compare-panel";

    panel.innerHTML = `
        <div class="compare-header">
            <strong>Compare Cities</strong>

            <button
                id="compare-close"
                type="button"
            >
                ×
            </button>
        </div>

        <div class="compare-current">
            <strong>${currentCity.city}</strong>
            <span>${currentCity.state}</span>
        </div>

        <input
            id="compare-search"
            type="text"
            placeholder="Search for a city..."
        >

        <div id="compare-results">
            Search for a city to compare.
        </div>

        <div id="compare-table"></div>
    `;

    document.body.appendChild(panel);

    positionComparePanel();

    document
        .getElementById("compare-close")
        .onclick = () => {
            panel.remove();
        };

    document
        .getElementById("compare-search")
        .oninput = async event => {

            const value =
                event.target.value.trim();

            if (!value) {
                document
                    .getElementById("compare-results")
                    .textContent =
                    "Search for a city to compare.";

                return;
            }

            await searchForCity(value);
        };
}


async function searchForCity(value) {

    const results =
        document.getElementById("compare-results");

    results.textContent = "Searching...";

    try {

        const cities =
            await searchCities(value);

        const matches =
            cities
                .filter(city =>
                    !(
                        city.city === currentCity.city &&
                        city.state === currentCity.state
                    )
                )
                .slice(0, 10);

        results.innerHTML = "";

        if (!matches.length) {
            results.textContent = "No cities found.";
            return;
        }

        matches.forEach(city => {

            const button =
                document.createElement("button");

            button.className =
                "compare-city-result";

            button.textContent =
                `${city.city}, ${city.state}`;

            button.onclick = () =>
                compareWith(city);

            results.appendChild(button);
        });

    } catch (error) {

        console.error(error);

        results.textContent =
            "Unable to search cities.";
    }
}


async function compareWith(city) {

    const table =
        document.getElementById("compare-table");

    table.textContent = "Loading...";

    try {

        const comparisonCity =
            await getCity(
                city.city,
                city.state
            );

        table.innerHTML = `
            <div class="compare-grid">

                <div></div>

                <strong>
                    ${currentCity.city}
                </strong>

                <strong>
                    ${comparisonCity.city}
                </strong>

                <span>Population</span>
                <span>${formatNumber(currentCity.population)}</span>
                <span>${formatNumber(comparisonCity.population)}</span>

                <span>Median Age</span>
                <span>${formatValue(currentCity.median_age)}</span>
                <span>${formatValue(comparisonCity.median_age)}</span>

                <span>Median Household Income</span>
                <span>${formatCurrency(currentCity.median_household_income)}</span>
                <span>${formatCurrency(comparisonCity.median_household_income)}</span>

                <span>Per Capita Income</span>
                <span>${formatCurrency(currentCity.per_capita_income)}</span>
                <span>${formatCurrency(comparisonCity.per_capita_income)}</span>

                <span>Poverty Rate</span>
                <span>${formatPercent(currentCity.poverty_rate)}</span>
                <span>${formatPercent(comparisonCity.poverty_rate)}</span>

                <span>Unemployment</span>
                <span>${formatPercent(currentCity.unemployment_rate)}</span>
                <span>${formatPercent(comparisonCity.unemployment_rate)}</span>

                <span>Median Home Price</span>
                <span>${formatCurrency(currentCity.median_list_price)}</span>
                <span>${formatCurrency(comparisonCity.median_list_price)}</span>

                <span>Average Home Price</span>
                <span>${formatCurrency(currentCity.avg_list_price)}</span>
                <span>${formatCurrency(comparisonCity.avg_list_price)}</span>

                <span>Price / Sq Ft</span>
                <span>${formatCurrency(currentCity.median_price_per_sqft)}</span>
                <span>${formatCurrency(comparisonCity.median_price_per_sqft)}</span>

            </div>
        `;

    } catch (error) {

        console.error(error);

        table.textContent =
            "Unable to load comparison.";
    }
}


function positionComparePanel() {

    const panel =
        document.getElementById("compare-panel");

    const cityPanel =
        document.getElementById("city-panel");

    if (!panel || !cityPanel) {
        return;
    }

    const rect =
        cityPanel.getBoundingClientRect();

    panel.style.left =
        `${rect.left}px`;

    panel.style.top =
        `${rect.top}px`;
}


function formatNumber(value) {

    if (value === null || value === undefined) {
        return "—";
    }

    return Number(value).toLocaleString();
}


function formatCurrency(value) {

    if (value === null || value === undefined) {
        return "—";
    }

    return `$${Number(value).toLocaleString()}`;
}


function formatPercent(value) {

    if (value === null || value === undefined) {
        return "—";
    }

    return `${Number(value).toFixed(1)}%`;
}


function formatValue(value) {

    if (value === null || value === undefined) {
        return "—";
    }

    return Number(value).toFixed(1);
}