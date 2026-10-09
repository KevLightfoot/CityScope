import { searchCities, getCity } from "./api.js";
import { showCityOnMap } from "./map.js";
import { showCity } from "./panel.js";
import { setNeighborhoodAvailability, setMode } from "./view-mode.js";
import { escapeHtml } from "./utils.js";

export function setupSearch() {
    const input = document.getElementById("city-search");
    const results = document.getElementById("search-results");

    let timer;
    let searchId = 0;

    input.addEventListener("input", () => {
        clearTimeout(timer);

        const query = input.value.trim();

        if (!query) {
            hideResults(results);
            return;
        }

        const currentSearchId = ++searchId;

        timer = setTimeout(
            () => performSearch(query, input, results, currentSearchId, () => searchId),
            200
        );
    });

    input.addEventListener("keydown", event => {
        if (event.key !== "Enter") {
            return;
        }

        const first = results.querySelector(".search-result");

        if (first) {
            first.click();
        }
    });
}

async function performSearch(
    query,
    input,
    results,
    currentSearchId,
    getCurrentSearchId
) {
    try {
        const cities = await searchCities(query);

        if (currentSearchId !== getCurrentSearchId()) {
            return;
        }

        results.innerHTML = "";

        if (!cities.length) {
            results.innerHTML =
                `<div class="search-message">No cities found</div>`;

            results.style.display = "block";
            return;
        }

        cities.forEach(city => {
            const result = document.createElement("div");

            result.className = "search-result";

            result.innerHTML = `
                <span class="search-result-city">
                    ${escapeHtml(city.city)}
                </span>
                <span class="search-result-state">
                    ${escapeHtml(city.state)}
                </span>
            `;

            result.addEventListener("click", async () => {
                input.value = `${city.city}, ${city.state}`;
                hideResults(results);

            const data = await getCity(city.city, city.state);

            window.dispatchEvent(new Event("cityscope:neighborhood-housing-reset"));
            window.cityscopeCurrentNeighborhood = null;

            showCity(data);
            showCityOnMap(data);

            setMode("city");

                await setNeighborhoodAvailability(
                    data.city,
                    data.state
                );
                
            });

            results.appendChild(result);
        });

        results.style.display = "block";

    } catch (error) {
        console.error(error);

        if (currentSearchId !== getCurrentSearchId()) {
            return;
        }

        results.innerHTML =
            `<div class="search-message">Search unavailable</div>`;

        results.style.display = "block";
    }
}

function hideResults(results) {
    results.style.display = "none";
    results.innerHTML = "";
}