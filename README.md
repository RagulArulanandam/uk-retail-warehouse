# UK Online Retail Analytics & Data Warehouse

An end-to-end data project built on the UCI Online Retail II dataset — real UK e-commerce transactions from 2009–2011. Covers data cleaning, dimensional modelling (star schema with SCD Type 2), SQL analytics (window functions, query optimisation), and a Power BI dashboard.

---

## Pipeline

```
UCI Online Retail II (raw Excel)
        ↓
Cleaning & Investigation       src/clean.py
        ↓
Staging Load                   src/load_staging.py
        ↓
Star Schema Warehouse          sql/schema/, src/load_warehouse.py
        ↓
SCD Type 2 (dim_customer)      sql/scd/
        ↓
Analytical Queries             sql/analytics/
        ↓
Power BI Dashboard             dashboards/
```

---

## Project structure

```
uk-retail-warehouse/
│
├── data/                         # gitignored — raw file downloaded locally
│   ├── raw/
│   │   └── online_retail_II.xlsx
│   └── processed/
│
├── src/
│   ├── clean.py                  # Exploration, investigation, and confirmed cleaning steps
│   ├── load_staging.py           # Load cleaned data into SQL Server staging
│   └── load_warehouse.py         # Populate the star schema from staging
│
├── sql/
│   ├── schema/                   # DDL for fact/dimension tables
│   ├── scd/                      # SCD Type 2 logic for dim_customer
│   └── analytics/                # Window-function queries (RFM, rankings, trends)
│
├── dashboards/
│   └── uk_retail.pbix            # Power BI report
│
├── notes/
│   └── cleaning_decisions.md     # Documented cleaning decisions with evidence
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Tech stack

| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.12 | Cleaning, investigation, staging load |
| Data handling | Pandas | Exploration and cleaning |
| Database | SQL Server 2022 Express | Staging + star schema warehouse |
| DB client | SSMS | Query writing, execution plan analysis |
| Python↔DB | pyodbc | Loading cleaned data into SQL Server |
| Dashboard | Power BI Desktop | Data modelling (star schema) + visualisation |
| Version control | Git | — |

---

## Dataset

| Property | Detail |
|---|---|
| Source | [UCI Machine Learning Repository — Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) |
| Format | Excel (.xlsx), 2 sheets |
| Sheets | Year 2009-2010, Year 2010-2011 |
| Approx. rows | ~1.07 million combined |
| Key columns | Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country |

---

## Setup

### Prerequisites
- Python 3.12+
- SQL Server 2022 Express + SSMS
- Power BI Desktop (Windows only)

### 1. Clone the repo
```bash
git clone https://github.com/your-username/uk-retail-warehouse.git
cd uk-retail-warehouse
```

### 2. Create virtual environment and install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Download the dataset
Download `online_retail_II.xlsx` from the [UCI repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and place it at `data/raw/online_retail_II.xlsx`.

### 4. Run cleaning and investigation
```bash
python src/clean.py
```
Review the output against `notes/cleaning_decisions.md` before proceeding — some cleaning decisions are still pending investigation review as of this commit.

### 5. Load to SQL Server (once cleaning is finalised)
```bash
python src/load_staging.py
python src/load_warehouse.py
```

### 6. Open the dashboard
Open `dashboards/uk_retail.pbix` in Power BI Desktop and point the data source at your local SQL Server instance.

---

## Progress

| Step | Status |
|---|---|
| Data cleaning & investigation | In progress — Customer ID and Country decisions pending |
| Staging load (SQL Server) | Pending |
| Star schema design | Pending |
| SCD Type 2 (dim_customer) | Pending |
| Window-function analytics | Pending |
| Query optimisation | Pending |
| Power BI dashboard | Pending |

---

## License

MIT
