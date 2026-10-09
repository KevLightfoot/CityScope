import {
    showNeighborhoodBoundaries,
    hideNeighborhoodBoundaries
} from "./map.js";

let currentMode = "city";

export function setupViewMode() {

    const cityButton =
        document.getElementById("city-mode-button");

    const neighborhoodButton =
        document.getElementById("neighborhood-mode-button");

    if (!cityButton || !neighborhoodButton) {
        return;
    }

    cityButton.onclick = () => {
        setMode("city");
    };

    neighborhoodButton.onclick = () => {
        setMode("neighborhood");
    };

    setMode("city");
}


function setMode(mode) {

    currentMode = mode;

    const cityButton =
        document.getElementById("city-mode-button");

    const neighborhoodButton =
        document.getElementById("neighborhood-mode-button");

    cityButton?.classList.toggle(
        "active",
        mode === "city"
    );

    neighborhoodButton?.classList.toggle(
        "active",
        mode === "neighborhood"
    );

    if (mode === "neighborhood") {
        showNeighborhoodBoundaries();
    } else {
        hideNeighborhoodBoundaries();
    }

    updatePanelForMode();

    window.dispatchEvent(
        new CustomEvent("cityscope:view-mode", {
            detail: {
                mode
            }
        })
    );
}


function updatePanelForMode() {

    const sections =
        document.querySelectorAll(".panel-section");

    sections.forEach(section => {

        const title =
            section
                .querySelector(".section-header span")
                ?.textContent
                .trim()
                .toLowerCase();

        if (!title) {
            return;
        }

        const neighborhoodVisible =
            title === "demographics" ||
            title === "housing" ||
            title === "points of interest";

        if (currentMode === "neighborhood") {
            section.style.display =
                neighborhoodVisible
                    ? ""
                    : "none";
        } else {
            section.style.display = "";
        }
    });

    const compareButton =
        document.getElementById("compare-city-button");

    if (compareButton) {
        compareButton.textContent =
            currentMode === "neighborhood"
                ? "Compare Neighborhoods"
                : "Compare Cities";
    }
}


export function getViewMode() {
    return currentMode;
}