# Gemini Project Analysis: ChatBI

This document provides a comprehensive analysis of the ChatBI project, derived from the project's source code and documentation.

## 1. Project Overview

**ChatBI** is an intelligent, conversational data analysis system designed to emulate the core functionalities of platforms like Tencent Cloud's ChatBI. It allows users to interact with their data using natural language, enabling them to quickly obtain data analysis results and generate visual reports without writing complex SQL queries.

### Core Features

-   **Natural Language Querying (NLQ):** Users can ask questions in plain language (e.g., "What were the total sales in 2024?"), and the system translates them into SQL queries, executes them, and returns the results.
-   **Multi-Source Data Support:** Natively supports connections to MySQL databases and the ability to upload and analyze data from Excel files.
-   **Dual-Mode Analysis:** Offers two primary modes for interaction:
    -   **"Smart Query"**: For direct question-and-answer data retrieval.
    -   **"Report Generation"**: For creating structured reports with multiple charts and insights.
-   **Conversational Context:** Maintains session history and context, allowing for multi-turn dialogues.
-   **Data Preparation & Management:** Includes features for managing data sources, configuring data tables, and maintaining data dictionaries.
-   **Query Caching:** Implements a caching layer to store query results, significantly speeding up responses for repeated questions.

## 2. Technology Stack

The project is a modern full-stack web application with a clear separation between the frontend and backend.

-   **Backend:**
    -   **Framework:** Python with **FastAPI**.
    -   **Dependencies & Environment:** `uv` for package management, `pydantic` for data validation.
    -   **Database:** **MySQL**.
    -   **ORM/Migrations:** **SQLAlchemy** (inferred from context) with **Alembic** for database schema migrations.
    -   **AI Integration:** A component named `qwen_integration.py` suggests integration with Alibaba's **Qwen** large language model for the NL-to-SQL functionality.

-   **Frontend:**
    -   **Framework:** **Vue 3** with the Composition API.
    -   **Build Tool:** **Vite**.
    -   **State Management:** **Pinia**.
    -   **Language:** JavaScript/TypeScript.
    -   **Testing:** **Vitest** for unit tests and **Playwright** for end-to-end tests.
    -   **Styling:** Standard CSS and scoped styles within Vue components.

-   **DevOps & Deployment:**
    -   **Containerization:** **Docker** and **docker-compose** for creating reproducible environments.
    -   **Web Server/Proxy:** **Nginx** is used as a reverse proxy for the backend service.

## 3. Architecture & Data Flow

The application follows a classic three-tier architecture:

```
+-----------------+      +----------------------+      +----------------+
| Frontend (Vue)  |----->|   Backend (FastAPI)  |----->| Database (MySQL)|
+-----------------+      +----------------------+      +----------------+
        |                          |
        |                          |
        |      +---------------------------------------+
        +----->|   LLM Service (e.g., Qwen) for NL-to-SQL |
               +---------------------------------------+

```

### High-Level Data Flow (User Query)

1.  **User Input:** A user types a question (e.g., "show me sales by region") into the Vue.js frontend.
2.  **Frontend Cache Check:** The Pinia store (`chat.ts`) checks if an identical query has been made recently. If a cached result exists, it is displayed immediately.
3.  **API Request:** If no cache is found, the frontend sends a POST request to the `/api/query` endpoint on the FastAPI backend. The payload includes the user's text, the current session ID, and the active data source ID.
4.  **Backend Processing (`QueryService`):**
    -   The backend's `QueryService` receives the request.
    -   It passes the natural language text to an NLU module (likely the Qwen integration) to parse intent and generate a SQL query.
    -   The generated SQL is validated.
5.  **Database Execution:** The `DatabaseService` executes the SQL query against the appropriate user-configured MySQL database.
6.  **Result Formatting:** The raw database result is processed, formatted into a JSON structure, and a suitable chart type (e.g., `bar`, `line`) is inferred.
7.  **API Response:** The backend returns a JSON object containing the query result, chart type, and a textual explanation.
8.  **Frontend Rendering:** The frontend receives the response, caches it for future use, and renders the data, typically as a combination of a chart and a data table.

## 4. Project Structure Highlights

```
ChatBI/
├── backend/
│   ├── src/
│   │   ├── main.py            # FastAPI app entry point & core routes
│   │   ├── api/               # API endpoint router modules
│   │   ├── services/          # Business logic (e.g., QueryService, SessionService)
│   │   ├── models/            # SQLAlchemy database models
│   │   └── sql_generator_qwen.py # Logic for interacting with the LLM
│   ├── alembic/               # Database migration scripts
│   ├── pyproject.toml         # Python project definition and dependencies
│   └── Dockerfile             # Container definition for the backend
│
├── frontend/
│   ├── src/
│   │   ├── App.vue            # Root Vue component
│   │   ├── main.js            # Frontend application entry point
│   │   ├── components/        # Reusable UI components (charts, inputs, etc.)
│   │   ├── views/             # Top-level page components
│   │   ├── store/             # Pinia state management modules (chat.ts, ui.ts)
│   │   └── router/            # Vue Router configuration
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite build configuration
│
├── database/
│   └── init.sql               # Initial database schema setup script
│
└── scripts/
    ├── start.sh               # Utility script to start all services
    └── stop.sh                # Utility script to stop all services
```

## 5. How to Run the Project

The project includes simple shell scripts for easy setup.

1.  **Prerequisites:** Ensure Docker, Node.js (v18+), and Python (v3.12+) are installed.
2.  **Start Services:** From the project root, execute the start script:
    ```bash
    ./scripts/start.sh
    ```
    This script handles setting up the Python virtual environment, installing dependencies for both frontend and backend, and starting the services via `docker-compose`.
3.  **Access Application:**
    -   **Frontend:** `http://localhost:3000`
    -   **Backend API Docs:** `http://localhost:8000/docs`
4.  **Stop Services:**
    ```bash
    ./scripts/stop.sh
    ```
