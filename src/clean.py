"""
clean.py

Exploratory analysis of the Online Retail II dataset (UCI), prior to
building the cleaned staging table and star schema.

Dataset:
    Two sheets - "Year 2009-2010" and "Year 2010-2011" - each ~540k+ rows,
    8 columns: Invoice, StockCode, Description, Quantity, InvoiceDate,
    Price, Customer ID, Country.

This module is organised in two parts:
    1. EXPLORATION  - the checks already run (missing values, invoice
       prefixes, cancelled orders, quantity/price outliers, missing
       Customer ID).
    2. INVESTIGATION - additional checks needed before the Customer ID
       cleaning decision can be finalised, plus the Price/Country/
       duplicate checks that hadn't been run yet.

Run as a script to print a full exploration + investigation report.
"""

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT_DIR / "data" / "raw" / "online_retail_II.xlsx"


# ---------------------------------------------------------------------------
# LOADING
# ---------------------------------------------------------------------------

def load_raw_sheets(file_path: Path) -> dict[str, pd.DataFrame]:
    """Load every sheet in the raw workbook into a dict keyed by sheet name."""
    excel_file = pd.ExcelFile(file_path)
    print(f"Sheets found: {excel_file.sheet_names}")
    return {name: pd.read_excel(excel_file, sheet_name=name) for name in excel_file.sheet_names}


def validate_schema_consistency(sheets: dict[str, pd.DataFrame]) -> None:
    """Confirm every sheet has matching columns and dtypes before concatenating.

    Concatenating sheets with mismatched dtypes silently upcasts columns
    (e.g. int -> float) and can hide problems later, so this is worth
    checking explicitly rather than assuming.
    """
    names = list(sheets)
    base_cols = sheets[names[0]].columns
    base_dtypes = sheets[names[0]].dtypes
    for name in names[1:]:
        cols_equal = sheets[name].columns.equals(base_cols)
        dtypes_equal = sheets[name].dtypes.equals(base_dtypes)
        print(f"{name}: columns match base -> {cols_equal}, dtypes match base -> {dtypes_equal}")


def concat_sheets(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine all sheets into a single DataFrame."""
    combined = pd.concat(sheets.values(), ignore_index=True)
    print(f"Combined shape: {combined.shape}")
    return combined


# ---------------------------------------------------------------------------
# PART 1: EXPLORATION (checks already run - now organised into functions)
# ---------------------------------------------------------------------------

def report_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Print count and percentage of missing values per column."""
    missing_count = df.isna().sum()
    missing_pct = (missing_count / len(df)) * 100
    report = pd.DataFrame({"missing_count": missing_count, "missing_pct": missing_pct})
    print("\nMissing values:\n", report)
    return report


def analyze_invoice_prefixes(df: pd.DataFrame) -> pd.Series:
    """Show the distribution of Invoice first-character prefixes.

    Convention in this dataset: '5'/'4' = normal sale, 'C' = cancellation,
    'A' = manual bad-debt adjustment (not a product sale).
    """
    prefixes = df["Invoice"].astype(str).str[0]
    print("\nInvoice prefix distribution:\n", prefixes.value_counts())
    return prefixes


def split_cancelled(df: pd.DataFrame, invoice_prefixes: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into cancelled ('C'-prefixed) vs non-cancelled rows."""
    cancelled_mask = invoice_prefixes.eq("C")
    cancelled_df = df[cancelled_mask]
    non_cancelled_df = df[~cancelled_mask]
    pct = len(cancelled_df) / len(df) * 100
    print(f"\nCancelled rows: {len(cancelled_df)} ({pct:.2f}%)")
    return cancelled_df, non_cancelled_df


def analyze_quantity(cancelled_df: pd.DataFrame, non_cancelled_df: pd.DataFrame) -> None:
    """Compare Quantity distributions between cancelled/non-cancelled rows,
    and flag negative quantities that appear OUTSIDE cancelled invoices
    (unexpected - worth explaining before deciding how to treat them).
    """
    print("\nCancelled Quantity stats:\n", cancelled_df["Quantity"].describe())
    print("\nNon-cancelled Quantity stats:\n", non_cancelled_df["Quantity"].describe())

    sign_counts = {
        "negative": int((cancelled_df["Quantity"] < 0).sum()),
        "positive": int((cancelled_df["Quantity"] > 0).sum()),
        "zero": int((cancelled_df["Quantity"] == 0).sum()),
    }
    print("Cancelled Quantity sign breakdown:", sign_counts)

    negative_in_normal = non_cancelled_df[non_cancelled_df["Quantity"] < 0]
    print(f"\nNegative Quantity in NON-cancelled invoices: {len(negative_in_normal)}")
    print(negative_in_normal.head(20))


def analyze_adjustment_invoices(df: pd.DataFrame) -> pd.DataFrame:
    """Isolate 'A'-prefixed rows - manual bad-debt adjustments, not sales.

    These should almost certainly be excluded from fact_sales regardless
    of what's decided about missing Customer IDs elsewhere.
    """
    a_df = df[df["Invoice"].astype(str).str.startswith("A")]
    print(f"\n'A'-prefixed adjustment rows: {len(a_df)}")
    print(a_df.to_string(index=False))
    return a_df


def analyze_price_outliers(df: pd.DataFrame) -> None:
    """Investigate Price distribution: negatives, zeros, and the max outlier."""
    print("Price < 0:", int((df["Price"] < 0).sum()))
    print("Price == 0:", int((df["Price"] == 0).sum()))
    print("Price > 0:", int((df["Price"] > 0).sum()))

    zero_price_df = df[df["Price"] == 0]
    negative_price_df = df[df["Price"] < 0]

    print(f"\nZero-price rows: {len(zero_price_df)}")
    print(zero_price_df.head(20))
    print(f"\nNegative-price rows: {len(negative_price_df)}")
    print(negative_price_df.to_string(index=False))

    print("\nZero-price Quantity stats:\n", zero_price_df["Quantity"].describe())
    print("\nZero-price Invoice prefix distribution:\n",
          zero_price_df["Invoice"].astype(str).str[0].value_counts())
    print("\nZero-price top Descriptions:\n",
          zero_price_df["Description"].value_counts(dropna=False).head(20))

    print("\nHighest-priced row:\n", df.loc[df["Price"].idxmax()])


def analyze_missing_customer_id(df: pd.DataFrame) -> None:
    """Break down missing-Customer-ID rows by invoice type (normal/cancelled/adjustment)."""
    missing_mask = df["Customer ID"].isna()
    missing_df = df[missing_mask]

    invoice_prefix = missing_df["Invoice"].astype(str).str[0]
    print("\nMissing-Customer-ID invoice prefix distribution:\n",
          invoice_prefix.value_counts(dropna=False))

    missing_and_cancelled = df[missing_mask & df["Invoice"].astype(str).str.startswith("C", na=False)]
    print(f"\nMissing Customer ID AND cancelled (C) invoice: {len(missing_and_cancelled)}")

    missing_normal = df[missing_mask & ~df["Invoice"].astype(str).str.startswith(("C", "A"), na=False)]
    print(f"\nMissing Customer ID, NOT cancelled/adjustment (normal sale rows): {len(missing_normal)}")
    print("\nQuantity stats:\n", missing_normal["Quantity"].describe())
    print("\nPrice stats:\n", missing_normal["Price"].describe())


# ---------------------------------------------------------------------------
# PART 2: INVESTIGATION (new - needed before finalising cleaning decisions)
# ---------------------------------------------------------------------------

def check_duplicate_rows(df: pd.DataFrame) -> None:
    """Count exact duplicate rows - outstanding from the original TASK list."""
    dup_count = int(df.duplicated().sum())
    print(f"\nExact duplicate rows: {dup_count} ({dup_count / len(df) * 100:.2f}%)")


def analyze_country(df: pd.DataFrame) -> None:
    """Investigate Country values: unique count and full distribution.

    Watch for near-duplicate/inconsistent naming (e.g. 'EIRE' for Ireland,
    'Unspecified', 'European Community') that needs standardising before
    these values become rows in dim_country.
    """
    print(f"\nUnique countries: {df['Country'].nunique()}")
    print("\nCountry value counts:\n", df["Country"].value_counts())


def analyze_customer_country_consistency(df: pd.DataFrame) -> pd.Series:
    """Check whether any single Customer ID is associated with more than
    one Country across the dataset.

    This directly determines whether SCD Type 2 tracking on dim_customer
    reflects a real, observed change in this data - or would need to be
    simulated on data that never actually changes.
    """
    country_counts_per_customer = (
        df.dropna(subset=["Customer ID"])
        .groupby("Customer ID")["Country"]
        .nunique()
    )
    multi_country_customers = country_counts_per_customer[country_counts_per_customer > 1]
    print(f"\nCustomers with more than one Country on record: {len(multi_country_customers)}")
    print(multi_country_customers.head(20))
    return multi_country_customers


def analyze_missing_customer_stockcodes(df: pd.DataFrame) -> None:
    """Check whether missing-Customer-ID, non-cancelled/adjustment rows
    cluster around non-product StockCodes (postage, manual entries, bank
    charges) rather than genuine anonymous product sales.

    This affects whether these rows belong in fact_sales at all, versus
    being warehouse/admin noise that should be filtered out entirely.
    """
    missing_mask = df["Customer ID"].isna()
    normal_missing = df[missing_mask & ~df["Invoice"].astype(str).str.startswith(("C", "A"), na=False)]
    print("\nTop StockCodes among missing-Customer-ID, non-cancelled/adjustment rows:\n",
          normal_missing["StockCode"].value_counts().head(20))


def analyze_revenue_impact_of_missing_customer(df: pd.DataFrame) -> None:
    """Quantify what share of total revenue the missing-Customer-ID rows
    represent - needed to judge how costly an exclude-vs-keep-as-'Guest'
    decision actually is, rather than deciding on row counts alone.
    """
    working = df.copy()
    working["revenue"] = working["Quantity"] * working["Price"]
    total_revenue = working["revenue"].sum()
    missing_revenue = working.loc[working["Customer ID"].isna(), "revenue"].sum()
    pct = (missing_revenue / total_revenue * 100) if total_revenue else 0
    print(f"\nRevenue from missing-Customer-ID rows: {missing_revenue:,.2f} "
          f"of {total_revenue:,.2f} total ({pct:.2f}%)")

def inspect_duplicate_rows(df: pd.DataFrame) -> None:
    duplicate_mask = df.duplicated(keep=False)
    duplicate_df = df[duplicate_mask]

    print("\n Duplicate rows sample:")
    print(duplicate_df.head(20).to_string(index=False))

def analyze_duplicate_groups(df: pd.DataFrame) -> None:

    duplicate_counts = (
        df.value_counts().reset_index(name="occurrence_count")
    )

    duplicate_groups = duplicate_counts[
        duplicate_counts["occurrence_count"] > 1
    ]

    print("\n Duplicate Groups:", len(duplicate_groups))
    print("\n Duplicate occurrence distribution")
    print(
        duplicate_groups["occurrence_count"]
        .value_counts()
        .sort_index()
    )

    print("\n Most repeated duplicated groups:")
    print(
        duplicate_groups.sort_values("occurrence_count", ascending=False)
        .head(20)
        .to_string(index=False)
    )

def inspect_duplicate_invoice_context(df: pd.DataFrame) -> None:
    """Inspect invoices containing exact duplicate rows."""

    duplicate_mask = df.duplicated(keep=False)

    duplicate_df = df[duplicate_mask].copy()

    invoice_summary = (
        duplicate_df
        .groupby("Invoice")
        .agg(
            duplicate_row_count=("Invoice", "size"),
            unique_stockcodes=("StockCode", "nunique"),
            invoice_total_quantity=("Quantity", "sum"),
        )
        .sort_values(
            "duplicate_row_count",
            ascending=False
        )
    )

    print("\nInvoices containing duplicate rows:")
    print(invoice_summary.head(20).to_string())

def inspect_specific_invoice(df: pd.DataFrame, invoice_number: str) -> None:
    """Inspect all rows belonging to one invoice."""

    invoice_df = df[
        df["Invoice"].astype(str) == invoice_number
    ].copy()

    print(f"\nInvoice {invoice_number} shape:", invoice_df.shape)

    print("\nInvoice row sample:")
    print(
        invoice_df
        .head(30)
        .to_string(index=False)
    )

    print("\nStockCode occurrence distribution:")
    print(
        invoice_df["StockCode"]
        .value_counts()
        .value_counts()
        .sort_index()
    )


# ---------------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------------

def run_exploration(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the checks already completed in the original script."""
    report_missing_values(df)
    invoice_prefixes = analyze_invoice_prefixes(df)
    cancelled_df, non_cancelled_df = split_cancelled(df, invoice_prefixes)
    analyze_quantity(cancelled_df, non_cancelled_df)
    analyze_adjustment_invoices(df)
    analyze_price_outliers(df)
    analyze_missing_customer_id(df)
    return cancelled_df, non_cancelled_df


def run_investigation(df: pd.DataFrame) -> None:
    """Run the additional checks needed before finalising cleaning decisions."""
    check_duplicate_rows(df)
    inspect_duplicate_rows(df)
    analyze_duplicate_groups(df)
    inspect_duplicate_invoice_context(df)
    inspect_specific_invoice(df, "537434git")
    analyze_country(df)
    analyze_customer_country_consistency(df)
    analyze_missing_customer_stockcodes(df)
    analyze_revenue_impact_of_missing_customer(df)


def main():
    sheets = load_raw_sheets(RAW_FILE)
    validate_schema_consistency(sheets)
    df = concat_sheets(sheets)

    run_exploration(df)
    run_investigation(df)


# ---------------------------------------------------------------------------
# PART 3: CLEANING (apply decisions already backed by evidence)
#
# Only decisions with confirmed supporting evidence are applied here.
# The Customer ID and Country decisions are NOT yet implemented - they
# depend on the output of run_investigation(), which hasn't been run/
# reviewed yet. See notes/cleaning_decisions.md for the full reasoning.
# ---------------------------------------------------------------------------

def exclude_adjustment_invoices(df: pd.DataFrame) -> pd.DataFrame:
    """Drop 'A'-prefixed rows (manual bad-debt adjustments).

    Evidence: 6 rows total, all labelled 'Adjust bad debt', no Customer ID,
    no real product/StockCode - these are not product sales.
    """
    before = len(df)
    cleaned = df[~df["Invoice"].astype(str).str.startswith("A")]
    print(f"Excluded {before - len(cleaned)} adjustment ('A'-prefix) rows.")
    return cleaned


def flag_cancelled_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Add an is_cancelled flag rather than dropping cancelled ('C'-prefix) rows.

    Evidence: 19,494 rows (1.83%), 19,493 of which have negative Quantity -
    these are real returns/cancellations and are kept for accurate net
    revenue reporting and return-rate analysis, not deleted.
    """
    df = df.copy()
    df["is_cancelled"] = df["Invoice"].astype(str).str.startswith("C")
    print(f"Flagged {df['is_cancelled'].sum()} cancelled rows via is_cancelled.")
    return df


def flag_non_sale_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Add an is_non_sale flag for zero-price rows (samples/damages/write-offs).

    Evidence: 6,202 rows (0.53%), disproportionately missing Description,
    with top labels 'damages', 'lost', 'found', 'sold as set on dotcom' -
    not paid transactions. Kept for traceability but excluded from
    revenue-based measures (RFM Monetary, total revenue) downstream.
    """
    df = df.copy()
    df["is_non_sale"] = df["Price"] == 0
    print(f"Flagged {df['is_non_sale'].sum()} zero-price non-sale rows via is_non_sale.")
    return df


def fill_missing_description(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing Description with 'UNKNOWN'.

    Evidence: 4,382 rows (0.41%) - low impact, Description is not a join
    key or a measure input, so a placeholder is sufficient.
    """
    df = df.copy()
    missing_before = df["Description"].isna().sum()
    df["Description"] = df["Description"].fillna("UNKNOWN")
    print(f"Filled {missing_before} missing Description values with 'UNKNOWN'.")
    return df


def remove_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows.

    This is standard practice regardless of count - an exact duplicate
    row is by definition redundant. Run check_duplicate_rows() first to
    log the actual count in cleaning_decisions.md.
    """
    before = len(df)
    cleaned = df.drop_duplicates()
    print(f"Removed {before - len(cleaned)} exact duplicate rows.")
    return cleaned


def apply_confirmed_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Apply every cleaning step that currently has confirmed evidence.

    NOT included yet (pending investigation review):
      - Missing Customer ID handling
      - Country name standardisation
    Add these once notes/cleaning_decisions.md sections 7 and 8 are final.
    """
    df = exclude_adjustment_invoices(df)
    df = flag_cancelled_orders(df)
    df = flag_non_sale_rows(df)
    df = fill_missing_description(df)
    df = remove_exact_duplicates(df)
    return df


if __name__ == "__main__":
    main()