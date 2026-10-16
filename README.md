# CityScope

**Explore cities. Compare neighborhoods. Make more informed relocation decisions.**

CityScope is an interactive city exploration platform designed to help people evaluate U.S. cities and neighborhoods using demographic, housing, crime, weather, education, and points-of-interest data.

Built with Python, Apache Spark, Apache Sedona, FastAPI, and a JavaScript mapping frontend, CityScope combines large-scale data processing, geospatial analytics, and similarity analysis into a single interactive application.

## Live Application

**[Launch CityScope](YOUR-CITYSCOPE-LIVE-URL)**

Replace the placeholder above with your live CityScope URL.

## Overview

Choosing where to live involves more than comparing population or housing prices. CityScope brings multiple data sources together to help users explore places at both the city and neighborhood levels.

Users can search for U.S. cities, inspect geographic boundaries, explore neighborhood-level information, examine nearby points of interest, and discover locations with similar characteristics.

The project includes a data processing pipeline, processed Parquet datasets, a FastAPI backend, and an interactive map-based frontend.

## Key Features

- **City Search:** Search for U.S. cities and explore available geographic and demographic information.
- **City Profiles:** Examine city-level indicators assembled from multiple datasets.
- **Neighborhood Exploration:** View neighborhood boundaries and investigate neighborhood-level information where data is available.
- **Interactive Mapping:** Explore city and neighborhood boundaries through a dynamic map interface.
- **Points of Interest:** Browse geographic points of interest to better understand the amenities and destinations around a location.
- **Housing Exploration:** Access housing-related information and property locations supported by the processed datasets.
- **City Similarity:** Discover cities with similar characteristics using standardized feature vectors, dimensionality reduction, and locality-sensitive hashing.
- **Neighborhood Similarity:** Apply a corresponding similarity workflow to neighborhood-level data.
- **Geospatial Data Processing:** Combine geographic datasets and perform spatial processing with Apache Sedona and Apache Spark.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python, JavaScript, HTML, CSS |
| Data Engineering | Apache Spark, PySpark, Parquet |
| Geospatial Processing | Apache Sedona |
| Machine Learning | Spark MLlib, feature standardization, PCA, locality-sensitive hashing |
| Backend | FastAPI, Uvicorn |
| Frontend | JavaScript, interactive mapping, HTML, CSS |
| Data Storage | Parquet datasets |
| Infrastructure | Linux, Google Cloud Compute Engine |

## System Architecture

CityScope separates data preparation from application serving. Raw datasets are processed into reusable analytical datasets before the API exposes information to the frontend.

```text
          Raw Data Sources
   ┌──────────┬──────────┬──────────┐
   │ Census   │ Housing  │  Crime   │
   ├──────────┼──────────┼──────────┤
   │ Weather  │ Education│   POIs   │
   └──────────┴──────────┴──────────┘
                  │
                  ▼
       PySpark Data Processing
                  │
                  ▼
       Apache Sedona Geospatial
          Processing & Integration
                  │
                  ▼
        Processed Parquet Data
                  │
          ┌───────┴────────┐
          ▼                ▼
     City/Neighborhood   Similarity
        Datasets         Workflows
          │                │
          └───────┬────────┘
                  ▼
             FastAPI
                  │
                  ▼
       Interactive JavaScript UI
                  │
                  ▼
          CityScope Map
```

### Data Processing Pipeline

Apache Spark handles large-scale transformations and aggregation across the source datasets. Apache Sedona supports geospatial operations that connect geographic boundaries and location-based information.

Processed outputs are stored as Parquet datasets, allowing the application to reuse prepared data without repeating the entire processing pipeline during ordinary user requests.

The project includes separate processed datasets for city-level information, neighborhood information, housing, crime, weather, and points of interest.

### Similarity Analysis

CityScope uses Spark MLlib to prepare feature vectors for city and neighborhood comparisons.

The workflow includes:

1. Preparing and standardizing numerical features.
2. Applying principal component analysis (PCA) to transform feature representations.
3. Using locality-sensitive hashing (LSH) to support similarity candidate discovery.
4. Comparing locations based on the features represented in the similarity workflow.

This provides a foundation for finding places with similar data characteristics rather than relying exclusively on geographic proximity.

### API Layer

The FastAPI backend connects the processed datasets and similarity workflows to the frontend.

Key API routes include:

| Endpoint | Purpose |
|---|---|
| `/api/neighborhood-available/{city}/{state}` | Check neighborhood data availability for a city |
| `/api/neighborhood-boundaries/{city}/{state}` | Retrieve neighborhood boundary information |
| `/api/neighborhood/{city}/{state}/{nbhd_id}` | Retrieve information for a specific neighborhood |
| `/api/neighborhood-similar` | Access neighborhood similarity functionality |

The API also supports city search, city-level information, and other application features.

Interactive frontend components use API requests to retrieve data as users explore the map.

## Data Sources

CityScope integrates multiple categories of public and geographic data, including:

- **Demographics:** Population, age distributions, and other census indicators.
- **Housing:** Housing characteristics and related geographic information.
- **Crime:** Processed crime data for location-based exploration.
- **Education:** Education-related indicators.
- **Weather:** Monthly weather aggregates.
- **Points of Interest:** Geographic locations representing amenities and destinations.
- **Spatial Boundaries:** Geographic data used to connect city and neighborhood information.

Individual sources are cleaned, transformed, and aggregated into datasets designed for the application's analytical workflows.

Specific source attribution, licensing, and dataset update dates should be documented alongside the relevant data-processing scripts.

## Repository Organization

The project is organized around data processing, API serving, frontend assets, and generated analytical datasets.

```text
CityScope/
├── api/
│   └── api.py
├── web/
│   ├── index.html
│   └── static/
│       └── js/
│           ├── map.js
│           ├── panel.js
│           └── neighborhood.js
├── data/
│   ├── raw/
│   └── processed/
└── ...
```

The `api/` directory contains the FastAPI application. The `web/` directory contains the frontend. The `data/raw/` and `data/processed/` directories hold source and generated datasets, respectively.

The full repository may contain additional processing scripts, configuration files, and similarity-model artifacts.

## Running the Application

Running the complete application requires the source code, compatible Python and Java environments, the required Python dependencies, and the processed datasets expected by the API.

### Prerequisites

- Python
- Java
- PySpark
- Apache Sedona and its compatible dependencies
- FastAPI and Uvicorn
- The processed Parquet datasets required by the application

Use the project's dependency files and configuration as the source of truth for exact package versions and installation commands.

### Start the API

From the project root, activate the configured Python environment and start the FastAPI application:

```bash
python -m uvicorn api.api:app --host 0.0.0.0 --port 8000
```

The API will listen on port `8000`.

For local development, the interactive API documentation is generally available at:

```text
http://127.0.0.1:8000/docs
```

### Serve the Frontend

From the project root, serve the `web/` directory using Python's static HTTP server:

```bash
python3 -m http.server 8080 --directory web --bind 0.0.0.0
```

Then open:

```text
http://127.0.0.1:8080
```

Ensure the frontend's API base URL points to the backend address reachable from the browser. The current local-development configuration has used `http://127.0.0.1:8000`.

**Note:** These commands start the web and API servers, but a successful full run also depends on the expected processed data being present and the Spark/Sedona environment being configured correctly.

## Engineering Challenges

Several important engineering concerns shaped CityScope's implementation:

- **Data integration:** Combining heterogeneous datasets with different schemas, geographic coverage, and levels of aggregation.
- **Geospatial processing:** Connecting geographic boundaries and location-based records across datasets.
- **Data quality:** Cleaning, validating, and matching city and neighborhood records before exposing them to the application.
- **Analytical performance:** Preprocessing large datasets into Parquet outputs to reduce repeated work during application serving.
- **Similarity workflows:** Preparing comparable feature representations for city and neighborhood similarity searches.
- **Interactive mapping:** Coordinating map layers, geographic boundaries, click behavior, and zoom transitions across different exploration levels.
- **Deployment:** Configuring the API and frontend to run as separate services on a cloud-hosted Linux environment.

## Future Development

Potential next steps include:

- Expanding data coverage and documenting dataset freshness.
- Improving similarity evaluation and feature selection.
- Adding clearer explanations for why two cities or neighborhoods are considered similar.
- Improving mobile responsiveness and accessibility.
- Automating data refreshes and validation.
- Optimizing deployment, API performance, and infrastructure costs.

## Author

**Kevin Lightfoot**

Computer Science graduate student at Louisiana State University, interested in software development, data engineering, geospatial analytics, and applied machine learning.

- **Portfolio:** https://kevlightfoot.github.io/Portfolio/
- **GitHub:** https://github.com/KevLightfoot
- **LinkedIn:** https://www.linkedin.com/in/kevin-lightfoot-1ba3b9205/
