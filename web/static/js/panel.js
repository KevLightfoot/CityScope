import {
    formatNumber,
    formatCurrency,
} from "./utils.js";

import {
    getWeather,
    getHousing, 
    getNeighborhood
} from "./api.js";

import {
    setHousingProperties,
    showHousingProperties,
    hideHousingProperties,
    clearHousingProperties,
    isHousingVisible,
    hidePOIs,
    closePOIPopup
} from "./map.js";

import { openPOIPanel,
        closePOIPanel
} from "./poi-panel.js";

let currentCity = null;
let housingRequestId = 0;

let currentNeighborhood = null;

export function setupPanel() {


    document
        .getElementById("close-panel")
        .addEventListener("click", () => {
            closePOIPopup();

            document
                .getElementById("city-panel")
                .classList.add("hidden");
        });

    // Close the small map popup when interacting with either info panel.
    // Do not remove POI markers or close the POI browser.
    document.addEventListener("click", event => {
        const panel = event.target.closest(
            "#city-panel, #neighborhood-panel"
        );

        if (!panel) {
            return;
        }

        closePOIPopup();
    });



    document
        .querySelectorAll(".section-header")
        .forEach(button => {

            button.addEventListener("click", () => {

                const section =
                    button.closest(".panel-section");

                const wasExpanded =
                    section.classList.contains("expanded");

                section.classList.toggle("expanded");

                const title =
                    button.querySelector("span")?.textContent.trim();

                if (
                    title === "Housing" &&
                    !wasExpanded &&
                    section.closest("#city-panel")
                ) {
                    preloadHousing();
                }

            });

        });


    const housingButton =
        document.getElementById("show-housing-button");

    if (housingButton) {

        housingButton.addEventListener("click", () => {

            if (isHousingVisible()) {

                hideHousingProperties();

                housingButton.textContent =
                    "Show Properties on Map";

            } else {

                showHousingProperties();

                housingButton.textContent =
                    "Hide Properties";
            }
        });
    }
}

export function showCity(city) {
    closePOIPanel();
    currentCity = city;
    housingRequestId++;

    clearHousingProperties();

    const housingButton =
        document.getElementById("show-housing-button");

    if (housingButton) {
        housingButton.disabled = true;
        housingButton.textContent =
            "Loading Properties...";
    }

    document
        .getElementById("city-panel")
        .classList.remove("hidden");


    document.getElementById("city-name").textContent =
        city.city || "Unknown City";


    document.getElementById("city-location").textContent =
        city.state || "";


    // =========================
    // DEMOGRAPHICS
    // =========================

    setText(
        "population",
        formatNumber(city.population)
    );

    setText(
        "median-age",
        formatNumber(city.median_age)
    );

    setPercent(
        "under-18",
        city.under_18_pct
    );

    setPercent(
        "age-20-24",
        city.age_20_24_pct
    );

    setPercent(
        "age-25-34",
        city.age_25_34_pct
    );

    setPercent(
        "age-35-44",
        city.age_35_44_pct
    );

    setPercent(
        "age-45-54",
        city.age_45_54_pct
    );

    setPercent(
        "age-55-64",
        combinePercent(
            city.age_55_59_pct,
            city.age_60_64_pct
        )
    );

    setPercent(
        "age-65-plus",
        combinePercent(
            city.age_65_74_pct,
            city.age_75_84_pct,
            city.age_85_plus_pct
        )
    );

    setPercent(
        "male-percent",
        city.male_pct
    );

    setPercent(
        "female-percent",
        city.female_pct
    );

    setPercent(
        "white-percent",
        city.white_pct
    );

    setPercent(
        "black-percent",
        city.black_pct
    );

    setPercent(
        "asian-percent",
        city.asian_pct
    );

    setPercent(
        "other-race-percent",
        city.other_race_pct
    );

    setText(
        "labor-force",
        formatNumber(city.labor_force)
    );

    setPercent(
        "unemployment",
        city.unemployment_rate
    );


    // =========================
    // WEATHER
    // =========================

    setTemperature(
        "avg-temp",
        city.avg_temp
    );

    setTemperature(
        "avg-low",
        city.avg_low
    );

    setTemperature(
        "avg-high",
        city.avg_high
    );

    setTemperature(
        "recorded-low",
        city.recorded_low
    );

    setTemperature(
        "recorded-high",
        city.recorded_high
    );

    // Additional monthly / seasonal weather
    loadWeather(city.place_GEOID);


    // =========================
    // CRIME
    // =========================

    const population =
        Number(city.population);

    const incidents =
        Number(city.incident_count);

    const crimeRate =
        Number.isFinite(population) &&
        population > 0 &&
        Number.isFinite(incidents)
            ? (incidents / population) * 1000
            : null;

    setText(
        "crime-rate",
        crimeRate !== null
            ? `${crimeRate.toFixed(1)} per 1,000`
            : "—"
    );


    // =========================
    // HOUSING
    // =========================

    setText(
        "property-count",
        formatNumber(city.property_count)
    );

    setText(
        "home-price",
        formatWholeCurrency(city.median_list_price)
    );

    setText(
        "avg-list-price",
        formatWholeCurrency(city.avg_list_price)
    );

    setText(
        "median-price-sqft",
        formatWholeCurrency(city.median_price_per_sqft)
    );

    setText(
        "avg-sqft",
        city.avg_sqft != null
            ? `${Math.round(Number(city.avg_sqft)).toLocaleString()} sq ft`
            : "—"
    );

    const housingSection = Array.from(
        document.querySelectorAll("#city-panel .panel-section")
    ).find(
        section =>
            section.querySelector(".section-header span")
                ?.textContent.trim() === "Housing"
    );

    if (housingSection?.classList.contains("expanded")) {
        preloadHousing();
    }

}




function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }

}


function setPercent(id, value) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    if (value === null || value === undefined) {
        element.textContent = "—";
        return;
    }

    const number =
        Number(value);

    element.textContent =
        Number.isFinite(number)
            ? `${number.toFixed(1)}%`
            : "—";

}


function setTemperature(id, value) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    if (value === null || value === undefined) {
        element.textContent = "—";
        return;
    }

    const number =
        Number(value);

    element.textContent =
        Number.isFinite(number)
            ? `${number.toFixed(1)}°`
            : "—";

}


function formatWholeCurrency(value) {

    if (value === null || value === undefined) {
        return "—";
    }

    const number =
        Number(value);

    return Number.isFinite(number)
        ? `$${Math.round(number).toLocaleString()}`
        : "—";

}


function combinePercent(...values) {

    const numbers =
        values
            .map(Number)
            .filter(Number.isFinite);

    if (!numbers.length) {
        return null;
    }

    return numbers.reduce(
        (total, value) => total + value,
        0
    );

}

async function loadWeather(geoid) {

    const container =
        document.getElementById("weather-data");

    const monthlyButton =
        document.getElementById("weather-monthly-button");

    const seasonalButton =
        document.getElementById("weather-seasonal-button");

    if (!container || !monthlyButton || !seasonalButton) {
        return;
    }

    container.innerHTML = "Loading...";

    try {

        const weather =
            await getWeather(geoid);

        function renderMonthly() {

            monthlyButton.classList.add("active");
            seasonalButton.classList.remove("active");

            container.innerHTML = `
                <div class="weather-header">
                    <span></span>
                    <span>Average</span>
                    <span>Low</span>
                    <span>High</span>
                </div>
            ` +
            weather.monthly
                .map(row => {
                    const name =
                        monthName(row.month);

                    return weatherRow(
                        name,
                        row.avg_temp,
                        row.avg_low,
                        row.avg_high
                    );
                })
                .join("");
        }


        function renderSeasonal() {

            seasonalButton.classList.add("active");
            monthlyButton.classList.remove("active");

            container.innerHTML = `
                <div class="weather-header">
                    <span></span>
                    <span>Average</span>
                    <span>Low</span>
                    <span>High</span>
                </div>
            ` +
            weather.seasonal
                .map(row => {

                    return weatherRow(
                        row.season,
                        row.avg_temp,
                        row.avg_low,
                        row.avg_high
                    );

                })
                .join("");
        }


        monthlyButton.onclick =
            renderMonthly;

        seasonalButton.onclick =
            renderSeasonal;

        renderMonthly();

    } catch (error) {

        console.error(error);

        container.innerHTML =
            `<div class="weather-error">
                Weather data unavailable
            </div>`;

    }
}


function weatherRow(
    label,
    average,
    low,
    high
) {

    return `
        <div class="weather-row">

            <span class="weather-label">
                ${label}
            </span>

            <span>
                ${formatTemperature(average)}
            </span>

            <span>
                ${formatTemperature(low)}
            </span>

            <span>
                ${formatTemperature(high)}
            </span>

        </div>
    `;
}


function formatTemperature(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "—";
    }

    const number =
        Number(value);

    return Number.isFinite(number)
        ? `${number.toFixed(1)}°`
        : "—";
}


function monthName(month) {

    const names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ];

    return names[month - 1] || "Unknown";
}

async function preloadHousing() {

    if (!currentCity) {
        return;
    }

    const requestId =
        ++housingRequestId;

    const button =
        document.getElementById("show-housing-button");

    if (button) {
        button.disabled = true;
        button.textContent =
            "Loading Properties...";
    }

    try {

        const properties =
            await getHousing(
                currentCity.city,
                currentCity.state
            );

        if (requestId !== housingRequestId) {
            return;
        }

        setHousingProperties(properties);

        if (button) {
            button.disabled = false;
            button.textContent =
                "Show Properties on Map";
        }

    } catch (error) {

        console.error(error);

        if (requestId !== housingRequestId) {
            return;
        }

        if (button) {
            button.disabled = true;
            button.textContent =
                "Properties Unavailable";
        }

    }

}