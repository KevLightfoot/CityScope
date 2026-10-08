import {
    getCity,
    getPOIs
} from "./api.js";

import {
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


export async function openPOIPanel(selectedCategory) {

    category = selectedCategory;

    const cityName =
        document.getElementById("city-name")?.textContent.trim();

    const state =
        document.getElementById("city-location")?.textContent.trim();

    if (!cityName || !state) {
        return;
    }

    city = await getCity(cityName, state);

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

            <button
                id="poi-selected"
                disabled
            >
                Show Selected on Map
            </button>

            <button id="poi-all">
                Show All ${title(category)} on Map
            </button>

        </div>
    `;

    document.body.appendChild(panel);

    document
        .getElementById("poi-close")
        .onclick = closePOIPanel;

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
        .getElementById("poi-selected")
        .onclick = showSelected;

    document
        .getElementById("poi-all")
        .onclick = showAll;
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

        const data = await getPOIs(
            "city",
            city.place_GEOID,
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

            updateSelectedButton();
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

    updateSelectedButton();
}


function updateSelectedButton() {

    const button =
        document.getElementById("poi-selected");

    if (!button) {
        return;
    }

    button.disabled =
        selected.size === 0;

    button.textContent =
        selected.size
            ? `Show ${selected.size} Selected on Map`
            : "Show Selected on Map";
}


function showSelected() {

    const pois =
        [...selected.values()];

    if (!pois.length) {
        return;
    }

    setPOIs(pois);

    showPOIs(category);
}


async function showAll() {

    const all = [];

    let currentOffset = 0;
    let hasMore = true;

    while (hasMore) {

        const data =
            await getPOIs(
                "city",
                city.place_GEOID,
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