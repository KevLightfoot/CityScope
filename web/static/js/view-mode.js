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

        currentMode = "city";

        cityButton.classList.add("active");
        neighborhoodButton.classList.remove("active");

        window.dispatchEvent(
            new CustomEvent("cityscope:view-mode", {
                detail: {
                    mode: "city"
                }
            })
        );
    };

    neighborhoodButton.onclick = () => {

        currentMode = "neighborhood";

        neighborhoodButton.classList.add("active");
        cityButton.classList.remove("active");

        window.dispatchEvent(
            new CustomEvent("cityscope:view-mode", {
                detail: {
                    mode: "neighborhood"
                }
            })
        );
    };
}

export function getViewMode() {
    return currentMode;
}