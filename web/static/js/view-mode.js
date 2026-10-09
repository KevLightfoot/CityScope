import {
    showNeighborhoodBoundaries,
    hideNeighborhoodBoundaries,
    hidePOIs,
    closePOIPopup
} from "./map.js";

import { closePOIPanel } from "./poi-panel.js";

import {
    getNeighborhoodAvailability
} from "./api.js";

let currentMode = "city";
let neighborhoodAvailable = false;

export function setupViewMode() {

    const cityButton =
        document.getElementById("city-mode-button");

    const neighborhoodButton =
        document.getElementById(
            "neighborhood-mode-button"
        );

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
    document.getElementById("neighborhood-compare-panel")?.remove();
    closePOIPanel();
    hidePOIs();
     closePOIPopup();

    if (mode === "neighborhood" && !neighborhoodAvailable) {
        mode = "city";
    }

    currentMode = mode;

    const cityButton =
        document.getElementById("city-mode-button");

    const neighborhoodButton =
        document.getElementById(
            "neighborhood-mode-button"
        );

    const cityPanel =
        document.getElementById("city-panel");

    const neighborhoodPanel =
        document.getElementById("neighborhood-panel");

    cityButton?.classList.toggle(
        "active",
        mode === "city"
    );

    neighborhoodButton?.classList.toggle(
        "active",
        mode === "neighborhood"
    );

    if (mode === "neighborhood") {

        cityPanel?.classList.add("hidden");

        showNeighborhoodBoundaries();

    } else {

        neighborhoodPanel?.classList.add("hidden");

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

    const cityPanel =
        document.getElementById("city-panel");

    const neighborhoodPanel =
        document.getElementById(
            "neighborhood-panel"
        );

    if (currentMode === "neighborhood") {

        cityPanel?.classList.add("hidden");

        if (neighborhoodPanel) {
            neighborhoodPanel.classList.remove("hidden");
        }

        return;
    }

    neighborhoodPanel?.classList.add("hidden");

    if (cityPanel) {
        cityPanel.classList.remove("hidden");
    }
}


export function getViewMode() {
    return currentMode;
}


export async function setNeighborhoodAvailability(
    city,
    state
) {

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