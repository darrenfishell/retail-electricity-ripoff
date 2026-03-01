# Retail Electricity Data Pipeline and Analysis

> A reproducible data engineering and analysis pipeline built with Python, dlt, dbt, DuckDB, and Observable Plot.

## Project Overview

This project includes a robust data pipeline that:
- Parses state and federal electricity data for loading into DuckDB
- Performs transformations using [dbt](https://www.getdbt.com/)
- Outputs clean datasets ready for analysis
- Generates summary reports and visualizations

The resulting analysis shows that retail electricity suppliers cost Maine customers **$200 million** more than the standard offer from 2012-2024.

I conducted the original analysis of this data for the [Bangor Daily News](https://www.bangordailynews.com/2016/08/31/business/business-energy/maine-competitive-electricity-providers-variable-rates/) in 2016. This project codifies the data extraction and transformations involved.

---

## Tools

- **[uv](https://docs.astral.sh/uv/)** -- Python dependency management
- **Python** -- data processing, orchestration
- **DuckDB** -- fast analytical SQL engine
- **dbt** -- SQL transformations and data modeling
- **dlt** -- data loading toolkit
- **Observable Framework** -- interactive data visualization
- **Pandas** -- data wrangling
- **Make** -- reproducible commands

---

## Project Structure

```
.
├── pyproject.toml                # Python dependencies (managed by uv)
├── .python-version               # Pins Python 3.11
├── Makefile                      # Workflow commands
├── run_pipeline.py               # Main pipeline runner
├── dlt_pipeline/                 # Parsing for EIA and state sources
├── dbt/                          # dbt models (SQL transformations)
├── data/                         # DuckDB database (generated)
├── prepared_data/                # Prepared CSV inputs
├── raw_data/                     # Source Excel files
├── observable/                   # Observable Framework app (visualization)
│   ├── src/index.md              # Main interactive page
│   ├── src/styles/style.css      # Custom styles
│   └── src/data/                 # Data loaders
├── .github/workflows/deploy.yml  # GitHub Pages CI/CD
└── README.md
```

---

## Setup

### Prerequisites

- **uv** -- Install from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js >= 18** -- For the Observable Framework app
- **npm** -- included with Node.js

### 1. Clone the repo

```bash
git clone https://github.com/darrenfishell/retail-electricity.git
cd retail-electricity
```

### 2. Run the full pipeline

```bash
make
```

This will:
1. Install Python dependencies into a `.venv` via uv
2. Run the data pipeline (`run_pipeline.py`), which downloads EIA data, loads it into DuckDB, and runs dbt transformations

### 3. Preview the Observable site locally

```bash
make dev
```

This starts the Observable Framework dev server (typically at `http://localhost:3000`) with hot-reload. The Python data loaders run within the uv-managed environment, so the DuckDB database must exist first (step 2).

### 4. Build the static site

```bash
make build
```

Produces a static site in `observable/dist/`, matching what GitHub Actions deploys to GitHub Pages.

---

## Makefile Reference

| Command        | Description                                      |
|----------------|--------------------------------------------------|
| `make install` | Install Python dependencies via uv               |
| `make run`     | Run the data pipeline                            |
| `make dev`     | Start Observable dev server (local preview)      |
| `make build`   | Build Observable static site to `observable/dist/`|
| `make clean`   | Remove the virtual environment                   |
| `make reset`   | Clean and reinstall dependencies                 |
| `make help`    | Show available commands                          |

---

## Manual Workflow (without Make)

```bash
# Install Python dependencies
uv sync

# Run the data pipeline
uv run python run_pipeline.py

# Preview the Observable site
cd observable
npm install
uv run npx observable preview

# Build static site
uv run npx observable build
```

The key pattern: `uv run <command>` runs any command within the Python virtual environment. When Observable Framework spawns Python data loaders, they inherit the correct environment and can access DuckDB, pandas, etc.

---

## License

MIT License. See `LICENSE` file for details.
