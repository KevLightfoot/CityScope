const API_BASE = "http://34.67.89.177:8000";

const US_BOUNDS = [
    [24.0, -125.0],
    [49.5, -66.0]
];

const map = L.map("map", {
    minZoom: 4,
    maxZoom: 12,
    maxBounds: US_BOUNDS,
    maxBoundsViscosity: 1.0
}).fitBounds(US_BOUNDS);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);


let cityMarker = null;
let searchTimer = null;
let currentResults = [];


const citySearch =
    document.getElementById("city-search");

const searchResults =
    document.getElementById("search-results");

const status =
    document.getElementById("status");

const cityPanel =
    document.getElementById("city-panel");


/* ---------------------------------------------------------
   SEARCH
--------------------------------------------------------- */

citySearch.addEventListener("input", function () {

    clearTimeout(searchTimer);

    const query = citySearch.value.trim();

    if (query.length < 2) {
        currentResults = [];
        searchResults.innerHTML = "";
        searchResults.style.display = "none";
        return;
    }

    searchTimer = setTimeout(
        () => searchCities(query),
        250
    );
});


/* ---------------------------------------------------------
   ENTER = SELECT FIRST RESULT
--------------------------------------------------------- */

citySearch.addEventListener(
    "keydown",
    function (event) {

        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();

        if (currentResults.length > 0) {
            selectCity(currentResults[0]);
        }
    }
);


/* ---------------------------------------------------------
   CLOSE CITY PANEL
--------------------------------------------------------- */

document.getElementById(
    "close-panel"
).addEventListener(
    "click",
    function () {

        cityPanel.classList.add("hidden");

        if (cityMarker) {
            map.removeLayer(cityMarker);
            cityMarker = null;
        }
    }
);


/* ---------------------------------------------------------
   SEARCH API
--------------------------------------------------------- */

async function searchCities(query) {

    try {

        const response = await fetch(
            `${API_BASE}/api/cities?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
            throw new Error(
                `Search failed (${response.status})`
            );
        }

        const cities = await response.json();

        currentResults = cities;

        displaySearchResults(cities);

    } catch (error) {

        console.error(
            "CityScope search error:",
            error
        );

        currentResults = [];

        searchResults.innerHTML = "";
        searchResults.style.display = "none";
    }
}


/* ---------------------------------------------------------
   SEARCH DROPDOWN
--------------------------------------------------------- */

function displaySearchResults(cities) {

    searchResults.innerHTML = "";

    if (!cities || cities.length === 0) {
        searchResults.style.display = "none";
        return;
    }


    cities.forEach(function (city) {

        const button =
            document.createElement("button");

        button.type = "button";
        button.className = "search-result";

        button.innerHTML = `
            <strong>${escapeHtml(city.city)}</strong>
            <span>${escapeHtml(city.state)}</span>
        `;

        button.addEventListener(
            "click",
            function () {
                selectCity(city);
            }
        );

        searchResults.appendChild(button);

    });


    searchResults.style.display = "block";
}


/* ---------------------------------------------------------
   SELECT CITY
--------------------------------------------------------- */

async function selectCity(city) {

    /*
     * Put selected city in search box.
     */
    citySearch.value =
        `${city.city}, ${city.state}`;


    /*
     * Hide dropdown.
     */
    searchResults.innerHTML = "";
    searchResults.style.display = "none";

    currentResults = [];


    /*
     * Get complete city data.
     */
    try {

        const response = await fetch(
            `${API_BASE}/api/city/${encodeURIComponent(city.city)}/${encodeURIComponent(city.state)}`
        );

        if (!response.ok) {
            throw new Error("City not found.");
        }

        const data = await response.json();

        displayCity(data);

    } catch (error) {

        console.error(
            "CityScope city error:",
            error
        );

        showStatus(error.message);

        return;
    }


    /*
     * -----------------------------------------------------
     * MAP LOCATION
     *
     * Coordinates now come from the API's Census geometry.
     * -----------------------------------------------------
     */

    if (
        city.latitude != null &&
        city.longitude != null
    ) {

        const latitude =
            Number(city.latitude);

        const longitude =
            Number(city.longitude);


        /*
         * Remove previous marker.
         */
        if (cityMarker) {
            map.removeLayer(cityMarker);
        }


        /*
         * Fly into the selected city.
         */
        map.flyTo(
            [latitude, longitude],
            10,
            {
                duration: 1.5
            }
        );


        /*
         * Add marker at city location.
         */
        cityMarker = L.marker(
            [latitude, longitude]
        )
        .addTo(map);


        /*
         * Popup attached to the map marker.
         */
        cityMarker.bindPopup(
            `
            <strong>${escapeHtml(city.city)}, ${escapeHtml(city.state)}</strong>
            `
        );


        /*
         * Open popup after the map finishes moving.
         */
        map.once(
            "moveend",
            function () {
                cityMarker.openPopup();
            }
        );

    } else {

        console.warn(
            "No coordinates returned for:",
            city.city,
            city.state
        );
    }


    hideStatus();
}


/* ---------------------------------------------------------
   CITY INFORMATION PANEL
--------------------------------------------------------- */

function displayCity(data) {

    document.getElementById(
        "city-name"
    ).textContent =
        data.city || "";


    document.getElementById(
        "city-state"
    ).textContent =
        data.state || "";


    document.getElementById(
        "population"
    ).textContent =
        formatNumber(data.population);


    document.getElementById(
        "median-age"
    ).textContent =
        data.median_age != null
            ? Number(data.median_age).toFixed(1)
            : "N/A";


    document.getElementById(
        "home-price"
    ).textContent =
        data.median_list_price != null
            ? formatCurrency(data.median_list_price)
            : "N/A";


    document.getElementById(
        "unemployment"
    ).textContent =
        data.unemployment_rate != null
            ? `${Number(data.unemployment_rate).toFixed(1)}%`
            : "N/A";


    cityPanel.classList.remove("hidden");
}


/* ---------------------------------------------------------
   FORMATTING
--------------------------------------------------------- */

function formatNumber(value) {

    if (value == null) {
        return "N/A";
    }

    return Number(value).toLocaleString();
}


function formatCurrency(value) {

    return Number(value).toLocaleString(
        "en-US",
        {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0
        }
    );
}


/* ---------------------------------------------------------
   STATUS
--------------------------------------------------------- */

function showStatus(message) {

    status.textContent = message;
    status.style.display = "block";
}


function hideStatus() {

    status.style.display = "none";
}


/* ---------------------------------------------------------
   HTML ESCAPING
--------------------------------------------------------- */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}