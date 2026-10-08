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


    // Expand / collapse sections
    document
        .querySelectorAll(".section-header")
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


    document.getElementById("population").textContent =
        formatNumber(city.population);


    document.getElementById("median-age").textContent =
        formatNumber(city.median_age);


    document.getElementById("home-price").textContent =
        formatCurrency(city.median_list_price);


    document.getElementById("unemployment").textContent =
        formatPercent(city.unemployment_rate);


    // Reset sections when selecting a new city
    document
        .querySelectorAll(".panel-section")
        .forEach(section => {

            section.classList.remove("expanded");

        });


    // Open demographics automatically
    const demographics =
        document.querySelector(".panel-section");

    if (demographics) {
        demographics.classList.add("expanded");
    }

}