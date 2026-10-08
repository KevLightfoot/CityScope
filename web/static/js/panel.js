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
}

export function showCity(city) {
    document
        .getElementById("city-panel")
        .classList.remove("hidden");

    document.getElementById("city-name").textContent =
        city.city || "Unknown City";

    document.getElementById("city-location").textContent =
        city.state || "";

    document.getElementById("population").textContent =
        formatNumber(city.population);

    document.getElementById("median-age").textContent =
        formatNumber(city.median_age);

    document.getElementById("home-price").textContent =
        formatCurrency(city.median_list_price);

    document.getElementById("unemployment").textContent =
        formatPercent(city.unemployment_rate);
}