import { getPOIs } from "./api.js";
import {
    setPOIs,
    showPOIs,
    hidePOIs
} from "./map.js";

let activeCategory = null;
let activeCity = null;

let currentSearch = "";
let currentLetter = "";
let currentOffset = 0;
let currentResults = [];
let selectedPOIs = [];

const PAGE_SIZE = 50;

export function setupPOIPanel() {
    // Nothing to initialize yet.
    // The panel is created when a POI category is opened.
}

export function openPOIPanel(category, city) {
    activeCategory = category;
    activeCity = city;

    currentSearch = "";
    currentLetter = "";
    currentOffset = 0;
    currentResults = [];
    selectedPOIs = [];

    createPanel();
    loadResults();
}

function createPanel() {
    closeExistingPanel();

    const panel = document.createElement("div");

    panel.id = "poi-browser-panel";
    panel.className = "poi-browser-panel";

    panel.innerHTML = `
        <div class="poi-browser-header">
            <div class="poi-browser-title">
                ${formatCategory(activeCategory)}
            </div>

            <button
                class="poi-browser-close"
                id="poi-browser-close"
                type="button"
            >
                ×
            </button>
        </div>

        <div class="poi-browser-controls">

            <input
                id="poi-search"
                class="poi-search"
                type="text"
                placeholder="Search businesses..."
                autocomplete="off"
            >

            <div class="poi-letters">
                <button
                    type="button"
                    class="poi-letter active"
                    data-letter=""
                >
                    All
                </button>

                ${"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    .split("")
                    .map(letter => `
                        <button
                            type="button"
                            class="poi-letter"
                            data-letter="${letter.toLowerCase()}"
                        >
                            ${letter}
                        </button>
                    `)
                    .join("")}
            </div>

        </div>

        <div class="poi-browser-results" id="poi-browser-results">
            <div class="poi-loading">
                Loading...
            </div>
        </div>

        <div class="poi-browser-footer">

            <button
                type="button"
                class="poi-map-button"
                id="poi-show-selected"
                disabled
            >
                Show Selected on Map
            </button>

            <button
                type="button"
                class="poi-map-button secondary"
                id="poi-show-all"
            >
                Show All ${formatCategory(activeCategory)} on Map
            </button>

        </div>
    `;

    document.body.appendChild(panel);

    document
        .getElementById("poi-browser-close")
        .addEventListener("click", closePOIPanel);

    document
        .getElementById("poi-search")
        .addEventListener("input", handleSearch);

    document
        .querySelectorAll(".poi-letter")
        .forEach(button => {
            button.addEventListener("click", () => {
                handleLetter(button.dataset.letter);
            });
        });

    document
        .getElementById("poi-show-selected")
        .addEventListener("click", showSelectedOnMap);

    document
        .getElementById("poi-show-all")
        .addEventListener("click", showAllOnMap);
}

async function loadResults() {
    const resultsContainer =
        document.getElementById("poi-browser-results");

    if (!resultsContainer) {
        return;
    }

    resultsContainer.innerHTML = `
        <div class="poi-loading">
            Loading...
        </div>
    `;

    try {
        const options = {
            limit: PAGE_SIZE,
            offset: currentOffset
        };

        if (currentSearch) {
            options.search = currentSearch;
        }

        if (currentLetter) {
            options.startsWith = currentLetter;
        }

        const response = await getPOIs(
            "city",
            activeCity.place_GEOID,
            activeCategory,
            options
        );

        currentResults = response.results || [];

        renderResults(response);

    } catch (error) {
        console.error("POI load failed:", error);

        resultsContainer.innerHTML = `
            <div class="poi-message">
                Unable to load places.
            </div>
        `;
    }
}

function renderResults(response) {
    const resultsContainer =
        document.getElementById("poi-browser-results");

    if (!resultsContainer) {
        return;
    }

    if (!currentResults.length) {
        resultsContainer.innerHTML = `
            <div class="poi-message">
                No places found.
            </div>
        `;

        updateSelectedButton();
        return;
    }

    resultsContainer.innerHTML = currentResults
        .map((poi, index) => {
            const selected = selectedPOIs.some(
                selectedPOI => selectedPOI.id === poi.id
            );

            return `
                <label class="poi-result ${selected ? "selected" : ""}">
                    <input
                        type="checkbox"
                        class="poi-checkbox"
                        data-index="${index}"
                        ${selected ? "checked" : ""}
                    >

                    <span class="poi-result-info">
                        <span class="poi-result-name">
                            ${escapeHtml(poi.name || "Unnamed place")}
                        </span>

                        <span class="poi-result-type">
                            ${escapeHtml(poi.category || "")}
                        </span>
                    </span>
                </label>
            `;
        })
        .join("");

    resultsContainer
        .querySelectorAll(".poi-checkbox")
        .forEach(checkbox => {
            checkbox.addEventListener(
                "change",
                handleSelection
            );
        });

    renderPagination(response.has_more);
    updateSelectedButton();
}

function renderPagination(hasMore) {
    const resultsContainer =
        document.getElementById("poi-browser-results");

    const pagination = document.createElement("div");

    pagination.className = "poi-pagination";

    const previousDisabled = currentOffset === 0;
    const nextDisabled = !hasMore;

    pagination.innerHTML = `
        <button
            type="button"
            class="poi-page-button"
            id="poi-previous"
            ${previousDisabled ? "disabled" : ""}
        >
            Previous
        </button>

        <span>
            Showing ${currentOffset + 1}–${currentOffset + currentResults.length}
        </span>

        <button
            type="button"
            class="poi-page-button"
            id="poi-next"
            ${nextDisabled ? "disabled" : ""}
        >
            Next
        </button>
    `;

    resultsContainer.appendChild(pagination);

    document
        .getElementById("poi-previous")
        ?.addEventListener("click", () => {
            currentOffset = Math.max(
                0,
                currentOffset - PAGE_SIZE
            );

            loadResults();
        });

    document
        .getElementById("poi-next")
        ?.addEventListener("click", () => {
            currentOffset += PAGE_SIZE;
            loadResults();
        });
}

function handleSearch(event) {
    currentSearch = event.target.value.trim().toLowerCase();

    currentLetter = "";
    currentOffset = 0;

    updateLetterButtons();
    loadResults();
}

function handleLetter(letter) {
    currentLetter = letter;
    currentSearch = "";
    currentOffset = 0;

    const searchInput =
        document.getElementById("poi-search");

    if (searchInput) {
        searchInput.value = "";
    }

    updateLetterButtons();
    loadResults();
}

function updateLetterButtons() {
    document
        .querySelectorAll(".poi-letter")
        .forEach(button => {
            button.classList.toggle(
                "active",
                button.dataset.letter === currentLetter
            );
        });
}

function handleSelection(event) {
    const index = Number(
        event.target.dataset.index
    );

    const poi = currentResults[index];

    if (!poi) {
        return;
    }

    if (event.target.checked) {
        if (
            !selectedPOIs.some(
                selectedPOI => selectedPOI.id === poi.id
            )
        ) {
            selectedPOIs.push(poi);
        }
    } else {
        selectedPOIs = selectedPOIs.filter(
            selectedPOI => selectedPOI.id !== poi.id
        );
    }

    event.target
        .closest(".poi-result")
        ?.classList.toggle(
            "selected",
            event.target.checked
        );

    updateSelectedButton();
}

function updateSelectedButton() {
    const button =
        document.getElementById("poi-show-selected");

    if (!button) {
        return;
    }

    button.disabled = selectedPOIs.length === 0;

    button.textContent =
        selectedPOIs.length
            ? `Show ${selectedPOIs.length} Selected on Map`
            : "Show Selected on Map";
}

function showSelectedOnMap() {
    if (!selectedPOIs.length) {
        return;
    }

    setPOIs(selectedPOIs);

    showPOIs(activeCategory);
}

async function showAllOnMap() {
    try {
        const allPOIs = [];
        let offset = 0;
        let hasMore = true;

        while (hasMore) {
            const response = await getPOIs(
                "city",
                activeCity.place_GEOID,
                activeCategory,
                {
                    limit: 100,
                    offset
                }
            );

            const results = response.results || [];

            allPOIs.push(...results);

            hasMore = response.has_more;
            offset += results.length;

            if (!results.length) {
                break;
            }
        }

        setPOIs(allPOIs);
        showPOIs(activeCategory);

    } catch (error) {
        console.error(
            "Unable to load all POIs:",
            error
        );
    }
}

export function closePOIPanel() {
    closeExistingPanel();
}

function closeExistingPanel() {
    const existing =
        document.getElementById("poi-browser-panel");

    if (existing) {
        existing.remove();
    }
}

function formatCategory(category) {
    if (!category) {
        return "Places";
    }

    return category.charAt(0).toUpperCase()
        + category.slice(1);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}