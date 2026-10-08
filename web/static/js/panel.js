import {
    formatNumber,
    formatCurrency,
    formatPercent
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
        .querySelectorAll(".section-header")
        .forEach(header => {
            header.addEventListener("click", () => {
                const section = header.closest(".panel-section");

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

    const population =
        document.getElementById("population");

    if (population) {
        population.textContent =
            formatNumber(city.population);
    }

    const medianAge =
        document.getElementById("median-age");

    if (medianAge) {
        medianAge.textContent =
            formatNumber(city.median_age);
    }

    const homePrice =
        document.getElementById("home-price");

    if (homePrice) {
        homePrice.textContent =
            formatCurrency(city.median_list_price);
    }

    const unemployment =
        document.getElementById("unemployment");

    if (unemployment) {
        unemployment.textContent =
            formatPercent(city.unemployment_rate);
    }
}