import { searchCities, getCity, getWeather } from "./api.js";

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
            <strong>
                ${currentCity.city}, ${currentCity.state}
            </strong>
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

    const results =
        document.getElementById("compare-results");

    const searchInput =
        document.getElementById("compare-search");

    table.textContent = "Loading...";

    try {

        const comparisonCity =
            await getCity(
                city.city,
                city.state
            );

        /*
         * Update the header
         */
        const current =
            document.querySelector(".compare-current");

        current.innerHTML = `
            <strong>
                ${currentCity.city}, ${currentCity.state}
                <span class="compare-vs">vs</span>
                ${comparisonCity.city}, ${comparisonCity.state}
            </strong>
        `;

        /*
         * Hide the search after selecting a city
         */
        searchInput.style.display = "none";
        results.style.display = "none";

        /*
         * Build comparison table
         */
        table.innerHTML = `
            <div class="compare-grid">
                <div class="compare-city-header"></div>
                <div class="compare-city-header">
                    ${currentCity.city}, ${currentCity.state}
                </div>
                <div class="compare-city-header">
                    ${comparisonCity.city}, ${comparisonCity.state}
                </div>

                <div class="compare-category">
                    DEMOGRAPHICS
                </div>

                <div>Population</div>
                <div>${formatNumber(currentCity.population)}</div>
                <div>${formatNumber(comparisonCity.population)}</div>

                <div>Median Age</div>
                <div>${formatValue(currentCity.median_age)}</div>
                <div>${formatValue(comparisonCity.median_age)}</div>

                <div>Under 18</div>
                <div>${formatValue(currentCity.under_18_pct)}</div>
                <div>${formatValue(comparisonCity.under_18_pct)}</div>

                <div>Age 20–24</div>
                <div>${formatValue(currentCity.age_20_24_pct)}</div>
                <div>${formatValue(comparisonCity.age_20_24_pct)}</div>

                <div>Age 25–34</div>
                <div>${formatValue(currentCity.age_25_34_pct)}</div>
                <div>${formatValue(comparisonCity.age_25_34_pct)}</div>

                <div>Age 35–44</div>
                <div>${formatValue(currentCity.age_35_44_pct)}</div>
                <div>${formatValue(comparisonCity.age_35_44_pct)}</div>

                <div>Age 45–54</div>
                <div>${formatValue(currentCity.age_45_54_pct)}</div>
                <div>${formatValue(comparisonCity.age_45_54_pct)}</div>

                <div>Age 65+</div>
                <div>${formatValue(currentCity.age_65_plus_pct)}</div>
                <div>${formatValue(comparisonCity.age_65_plus_pct)}</div>

                <div>Male</div>
                <div>${formatValue(currentCity.male_pct)}</div>
                <div>${formatValue(comparisonCity.male_pct)}</div>

                <div>Female</div>
                <div>${formatValue(currentCity.female_pct)}</div>
                <div>${formatValue(comparisonCity.female_pct)}</div>

                <div>White</div>
                <div>${formatValue(currentCity.white_pct)}</div>
                <div>${formatValue(comparisonCity.white_pct)}</div>

                <div>Black</div>
                <div>${formatValue(currentCity.black_pct)}</div>
                <div>${formatValue(comparisonCity.black_pct)}</div>

                <div>Asian</div>
                <div>${formatValue(currentCity.asian_pct)}</div>
                <div>${formatValue(comparisonCity.asian_pct)}</div>

                <div>Other Race</div>
                <div>${formatValue(currentCity.other_race_pct)}</div>
                <div>${formatValue(comparisonCity.other_race_pct)}</div>

                <div>Labor Force</div>
                <div>${formatNumber(currentCity.labor_force)}</div>
                <div>${formatNumber(comparisonCity.labor_force)}</div>

                <div>Unemployment</div>
                <div>${formatPercent(currentCity.unemployment_rate)}</div>
                <div>${formatPercent(comparisonCity.unemployment_rate)}</div>


                <div class="compare-category">
                    HOUSING
                </div>

                <div>Properties</div>
                <div>${formatNumber(currentCity.property_count)}</div>
                <div>${formatNumber(comparisonCity.property_count)}</div>

                <div>Median List Price</div>
                <div>${formatCurrency(currentCity.median_list_price)}</div>
                <div>${formatCurrency(comparisonCity.median_list_price)}</div>

                <div>Average List Price</div>
                <div>${formatCurrency(currentCity.avg_list_price)}</div>
                <div>${formatCurrency(comparisonCity.avg_list_price)}</div>

                <div>Median Price / Sq Ft</div>
                <div>${formatCurrency(currentCity.median_price_per_sqft)}</div>
                <div>${formatCurrency(comparisonCity.median_price_per_sqft)}</div>

                <div>Average Sq Ft</div>
                <div>${formatNumber(currentCity.avg_sqft)}</div>
                <div>${formatNumber(comparisonCity.avg_sqft)}</div>


                <div class="compare-category">
                    WEATHER
                </div>

                <div>Average Temperature</div>
                <div id="compare-current-temp">—</div>
                <div id="compare-other-temp">—</div>


                <div class="compare-category">
                    CRIME
                </div>

                <div>Crime Rate / 1,000</div>
                <div>${crimeRate(currentCity)}</div>
                <div>${crimeRate(comparisonCity)}</div>

            </div>
        `;

        /*
         * Load weather after the table exists
         */
        loadComparisonWeather(
            currentCity,
            comparisonCity
        );

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

    panel.style.left = `${Math.max(18, rect.left - panel.offsetWidth - 8)}px`;

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


function crimeRate(city) {
    const incidents = Number(city.incident_count);
    const population = Number(city.population);

    if (
        !Number.isFinite(incidents) ||
        !Number.isFinite(population) ||
        population <= 0
    ) {
        return "—";
    }

    return `${((incidents / population) * 1000).toFixed(1)}`;
}

function formatValue(value) {
    const number = Number(value);

    return Number.isFinite(number)
        ? number.toLocaleString(undefined, {
            maximumFractionDigits: 1
        })
        : "—";
}

async function loadComparisonWeather(currentCity, comparisonCity) {
    const currentTemp =
        document.getElementById("compare-current-temp");

    const otherTemp =
        document.getElementById("compare-other-temp");

    if (!currentTemp || !otherTemp) {
        return;
    }

    try {
        const [currentWeather, otherWeather] =
            await Promise.all([
                getWeather(currentCity.place_GEOID),
                getWeather(comparisonCity.place_GEOID)
            ]);

        currentTemp.textContent =
            averageWeatherTemperature(currentWeather);

        otherTemp.textContent =
            averageWeatherTemperature(otherWeather);

    } catch (error) {
        console.error(error);

        currentTemp.textContent = "—";
        otherTemp.textContent = "—";
    }
}

function averageWeatherTemperature(weather) {
    if (
        !weather ||
        !weather.monthly ||
        !weather.monthly.length
    ) {
        return "—";
    }

    const values = weather.monthly
        .map(row => Number(row.avg_temp))
        .filter(Number.isFinite);

    if (!values.length) {
        return "—";
    }

    const average =
        values.reduce(
            (sum, value) => sum + value,
            0
        ) / values.length;

    return `${average.toFixed(1)}°`;
}