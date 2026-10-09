import {
    showNeighborhoodBoundaries,
    hideNeighborhoodBoundaries
} from "./map.js";

import {
    getNeighborhoodAvailability
} from "./api.js";

let currentMode = "city";
let neighborhoodAvailable = false;

export function setupViewMode() {

    const cityButton =
        document.getElementById("city-mode-button");

    const neighborhoodButton =
        document.getElementById("neighborhood-mode-button");

    if (!cityButton || !neighborhoodButton) {
        return;
    }

    neighborhoodButton.style.display = "none";

    cityButton.onclick = () => {
        setMode("city");
    };

    neighborhoodButton.onclick = () => {
        setMode("neighborhood");
    };

    setMode("city");
}


export function setMode(mode) {

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
       if (!neighborhoodAvailable) {
            setMode("city");
            return;
        }

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

export async function setNeighborhoodAvailability(city, state) {

    try {

        const result =
            await getNeighborhoodAvailability(
                city,
                state
            );

        neighborhoodAvailable =
            result.available;

    } catch (error) {

        console.error(
            "Neighborhood availability check failed:",
            error
        );

        neighborhoodAvailable = false;
    }

    const neighborhoodButton =
        document.getElementById(
            "neighborhood-mode-button"
        );

    if (neighborhoodButton) {

        neighborhoodButton.style.display =
            neighborhoodAvailable
                ? ""
                : "none";
    }

    if (
        !neighborhoodAvailable &&
        currentMode === "neighborhood"
    ) {
        setMode("city");
    }
}