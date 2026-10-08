import {
    formatNumber,
    formatCurrency
} from "./utils.js";


export function setupPanel() {

    document
        .getElementById("close-panel")
        .addEventListener("click", () => {

            document
                .getElementById("city-panel")
                .classList.add("hidden");

        });


    document
        .querySelectorAll(".panel-section-header")
        .forEach(button => {

            button.addEventListener("click", () => {

                const section =
                    button.closest(".panel-section");

                section.classList.toggle("expanded");

            });

        });

}


export function showCity(city) {

    document
        .getElementById("city-panel")
        .classList.remove("hidden");


    document.getElementById("city-name").textContent =
        city.city || "Unknown City";


    document.getElementById("city-location").textContent =
        city.state || "";


    // DEMOGRAPHICS

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
        "multi-race-percent",
        city.two_or_more_races_pct
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


    // WEATHER

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

    setText(
        "months-available",
        formatNumber(city.months_available)
    );


    // CRIME

    setText(
        "incident-count",
        formatNumber(city.incident_count)
    );


    // HOUSING

    setText(
        "property-count",
        formatNumber(city.property_count)
    );

    setText(
        "home-price",
        formatCurrency(city.median_list_price)
    );

    setText(
        "avg-list-price",
        formatCurrency(city.avg_list_price)
    );

    setText(
        "median-price-sqft",
        formatCurrency(city.median_price_per_sqft)
    );

    setText(
        "avg-sqft",
        city.avg_sqft != null
            ? `${Number(city.avg_sqft).toLocaleString()} sq ft`
            : "—"
    );


    // CLOSE ALL SECTIONS

    document
        .querySelectorAll(".panel-section")
        .forEach(section => {
            section.classList.remove("expanded");
        });

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

    const number = Number(value);

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

    const number = Number(value);

    element.textContent =
        Number.isFinite(number)
            ? `${number.toFixed(1)}°`
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