import {
    getCity,
    getPOIs
} from "./api.js";

import {
    closePOIPopup,
    clearPOICategory,
    clearPOIs,
    setPOIs,
    showPOIs
} from "./map.js";


let city = null;
let category = null;
let search = "";
let letter = "";
let offset = 0;
let selected = new Map();

const PAGE_SIZE = 50;

let scopeType = "city";
let scopeId = null;
let activePanelId = "city-panel";


document.addEventListener("click", event => {
    // Neighborhood category buttons
    const neighborhoodButton = event.target.closest(
        "#neighborhood-panel .poi-button"
    );

    if (neighborhoodButton) {
        openPOIPanel(neighborhoodButton.dataset.category || "");
        return;
    }

    // Existing neighborhood browse button, if present
    if (event.target.closest("#browse-neighborhood-pois")) {
        openPOIPanel("");
        return;
    }

    // Existing city-level category buttons
    const cityButton = event.target.closest(
        "#city-panel .poi-button"
    );

    if (cityButton) {
        openPOIPanel(cityButton.dataset.category || "");
    }
});

window.addEventListener("cityscope:neighborhood-changing", () => {
    closePOIPanel();
});


export async function openPOIPanel(selectedCategory) {
    document.getElementById("neighborhood-compare-panel")?.remove();

    category = selectedCategory || "";

    const neighborhoodPanel =
        document.getElementById("neighborhood-panel");

    const selectedNeighborhood =
        window.cityscopeCurrentNeighborhood;

    const neighborhoodMode =
        neighborhoodPanel &&
        !neighborhoodPanel.classList.contains("hidden") &&
        selectedNeighborhood;

    if (neighborhoodMode) {
        scopeType = "neighborhood";

        scopeId = [
            selectedNeighborhood.city,
            selectedNeighborhood.state,
            selectedNeighborhood.nbhd_id
        ].join("~");

        activePanelId = "neighborhood-panel";

        city = null;
    } else {
        scopeType = "city";
        activePanelId = "city-panel";

        const cityName =
            document.getElementById("city-name")?.textContent.trim();

        const state =
            document.getElementById("city-location")?.textContent.trim();

        if (!cityName || !state) return;

        city = await getCity(cityName, state);
        if (!city || !city.place_GEOID) {
            console.error("Could not find city:", cityName, state);
            return;
        }
        scopeId = city.place_GEOID;
    }

    search = "";
    letter = "";
    offset = 0;
    selected.clear();

    renderPanel();
    loadPOIs();
}


function renderPanel() {

    document
        .getElementById("poi-browser-panel")
        ?.remove();

    const panel = document.createElement("aside");

    panel.id = "poi-browser-panel";

    panel.innerHTML = `
        <div class="poi-browser-header">
            <strong>${title(category)}</strong>

            <button
                id="poi-close"
                type="button"
            >
                ×
            </button>
        </div>

        <input
            id="poi-search"
            type="text"
            placeholder="Search businesses..."
        >

        <div id="poi-letters">
            <button data-letter="">All</button>
            ${"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                .split("")
                .map(letter =>
                    `<button data-letter="${letter.toLowerCase()}">${letter}</button>`
                )
                .join("")}
        </div>

        <div id="poi-results">
            Loading...
        </div>


        <div class="poi-actions">
            <button id="poi-all" type="button">
                Show All ${title(category)} on Map
            </button>

            <button id="poi-clear-category" type="button">
                Clear ${title(category)}
            </button>

            <button id="poi-reset" type="button">
                Clear All POIs
            </button>
        </div>

    `;

    document.body.appendChild(panel);

    panel.addEventListener("click", () => {
        closePOIPopup();
    });

    positionPanel();

    document
        .getElementById("poi-close")
        .onclick = closePOIPanel;

    document
        .getElementById("poi-all")
        .onclick = showAll;

    document
        .getElementById("poi-search")
        .oninput = event => {

            search = event.target.value.trim();

            letter = "";
            offset = 0;

            loadPOIs();
        };

    panel
        .querySelectorAll("[data-letter]")
        .forEach(button => {

            button.onclick = () => {

                letter =
                    button.dataset.letter;

                search = "";
                offset = 0;

                document
                    .getElementById("poi-search")
                    .value = "";

                loadPOIs();
            };

        });


    document
        .getElementById("poi-clear-category")
        .onclick = () => {
            if (!category) {
                alert("Open a specific POI category to clear it.");
                return;
            }

            closePOIPopup();
            clearPOICategory(category);

            for (const [id, poi] of selected.entries()) {
                if (
                    String(poi.cityscope_category || "").toLowerCase() ===
                    category.toLowerCase()
                ) {
                    selected.delete(id);
                }
            }
            
            offset = 0;
            loadPOIs();
        };

    document
        .getElementById("poi-reset")
        .onclick = () => {
            closePOIPopup();
            clearPOIs();
            selected.clear();
            closePOIPanel();
        };

}


function positionPanel() {

    const panel =
        document.getElementById("poi-browser-panel");

    const cityPanel =
        document.getElementById(activePanelId);

    if (!panel || !cityPanel) {
        return;
    }

    const rect =
        cityPanel.getBoundingClientRect();

    panel.style.left =
        `${Math.max(18, rect.left - panel.offsetWidth - 4)}px`;

    panel.style.right = "auto";

    panel.style.top =
        `${rect.top}px`;
}


async function loadPOIs() {

    const results =
        document.getElementById("poi-results");

    if (!results) {
        return;
    }

    results.textContent = "Loading...";

    try {

        const options = {
            limit: PAGE_SIZE,
            offset
        };

        if (search) {
            options.search = search;
        }

        if (letter) {
            options.startsWith = letter;
        }

        const data =
            await getPOIs(
                scopeType,
                scopeId,
                category,
                options
            );

        renderResults(data);

    } catch (error) {

        console.error(error);

        results.textContent =
            "Unable to load places.";
    }
}


function renderResults(data) {

    const results =
        document.getElementById("poi-results");

    results.innerHTML = "";

    const nameCounts = new Map();

    data.results.forEach(poi => {
        const name = (poi.name || "").trim();

        if (!name) {
            return;
        }

        const key = name.toLowerCase();

        if (!nameCounts.has(key)) {
            nameCounts.set(key, {
                name,
                count: 0
            });
        }

        nameCounts.get(key).count++;
    });

    for (const { name, count } of nameCounts.values()) {

        if (count <= 10) {
            continue;
        }

        const button =
            document.createElement("button");

        button.type = "button";
        button.className = "poi-duplicate-button";


        button.textContent =
            `Select all "${name}" (${count})`;

        button.onclick = async () => {

            let all = [];
            let currentOffset = 0;
            let hasMore = true;

            while (hasMore) {

                const response =
                    await getPOIs(
                        scopeType,
                        scopeId,
                        category,
                        {
                            search: name,
                            limit: 100,
                            offset: currentOffset
                        }
                    );

                all.push(
                    ...response.results.filter(
                        poi =>
                            (poi.name || "").trim().toLowerCase() ===
                            name.toLowerCase()
                    )
                );

                hasMore = response.has_more;

                currentOffset +=
                    response.results.length;

                if (!response.results.length) {
                    break;
                }
            }

                all.forEach(poi => {
                    selected.set(poi.id, poi);
                });

                setPOIs([...selected.values()]);
                showPOIs(category);
                renderResults(data);
        };

        results.appendChild(button);
    }

    if (!data.results.length) {

        results.textContent =
            "No places found.";

        return;
    }

    data.results.forEach(poi => {

        const row =
            document.createElement("div");

        row.className = "poi-result";

        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";

        checkbox.checked =
            selected.has(poi.id);

        checkbox.onchange = () => {

            if (checkbox.checked) {
                selected.set(poi.id, poi);
            } else {
                selected.delete(poi.id);
            }

            setPOIs([...selected.values()]);
            showPOIs(category);
        };

        const name =
            document.createElement("span");

        name.textContent =
            poi.name || "Unnamed place";

        row.append(
            checkbox,
            name
        );

        results.appendChild(row);
    });


    const pagination =
        document.createElement("div");

    pagination.className =
        "poi-pagination";


    if (offset > 0) {

        const previous =
            document.createElement("button");

        previous.textContent =
            "Previous";

        previous.onclick = () => {

            offset -= PAGE_SIZE;

            loadPOIs();
        };

        pagination.appendChild(previous);
    }


    if (data.has_more) {

        const next =
            document.createElement("button");

        next.textContent =
            "Next";

        next.onclick = () => {

            offset += PAGE_SIZE;

            loadPOIs();
        };

        pagination.appendChild(next);
    }


    results.appendChild(pagination);
}


async function showAll() {

    const all = [];

    let currentOffset = 0;
    let hasMore = true;

    while (hasMore) {

        const data =
            await getPOIs(
                scopeType,
                scopeId,
                category,
                {
                    limit: 100,
                    offset: currentOffset
                }
            );

        all.push(
            ...data.results
        );

        hasMore =
            data.has_more;

        currentOffset +=
            data.results.length;

        if (!data.results.length) {
            break;
        }
    }

    setPOIs(all);

    showPOIs(category);
}

export function closePOIPanel() {

    document
        .getElementById("poi-browser-panel")
        ?.remove();
}


function title(value) {

    if (!value) {
        return "Places";
    }

    return value.charAt(0).toUpperCase()
        + value.slice(1);
}