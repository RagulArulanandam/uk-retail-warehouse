# Cleaning Decisions — Online Retail II

**Status:** Phase 1 partially complete. Sections 1–6 are confirmed and implemented in `src/clean.py`. Sections 7–8 are **pending** — they require output from `run_investigation()` that hasn't been reviewed yet. See "Next Steps" at the bottom.

---

## 1. Adjustment Invoices ('A' prefix)
**Evidence:** 6 rows total, all labelled `Adjust bad debt`, no linked product/StockCode beyond `B`, no Customer ID.
**Decision:** Exclude entirely from `fact_sales`. These are manual accounting adjustments, not product transactions, and including them would distort revenue figures (one row alone is -£53,594.36).
**Implemented in:** `exclude_adjustment_invoices()`

---

## 2. Cancelled Invoices ('C' prefix)
**Evidence:** 19,494 rows (1.83% of the dataset). 19,493 of 19,494 have negative Quantity (mean -25.19, the one positive-quantity exception is worth a manual look but is negligible at n=1). These map cleanly to real product returns/cancellations.
**Decision:** **Keep**, not drop — flag with `is_cancelled = True/False`. Deleting them would overstate net sales; keeping them flagged supports both a "gross sales" view and a "net of returns" view, and enables a return-rate metric in the Power BI dashboard.
**Implemented in:** `flag_cancelled_orders()`

---

## 3. Zero-Price Rows
**Evidence:** 6,202 rows (0.53%). Disproportionately missing Description; where Description exists, the top values are `damages`, `lost`, `found`, `sold as set on dotcom`, `Damaged`, `adjustment` — consistent with samples, write-offs, and stock corrections rather than paid sales.
**Decision:** **Keep the rows, flag with `is_non_sale = True/False`.** Exclude from revenue-based measures downstream (RFM Monetary component, total revenue, average order value) but retain for completeness and stock-movement traceability.
**Implemented in:** `flag_non_sale_rows()`

---

## 4. Negative-Price Rows
**Evidence:** 5 rows, all `Adjust bad debt` entries under `A`-prefixed invoices.
**Decision:** No separate handling needed — already excluded under Decision 1.

---

## 5. Missing Description
**Evidence:** 4,382 rows (0.41% of the dataset). Description is not a join key, primary key component, or measure input anywhere in the planned star schema.
**Decision:** Fill with `'UNKNOWN'`. Low-impact field; a placeholder avoids null-handling issues later in Power BI without requiring row exclusion.
**Implemented in:** `fill_missing_description()`

---

## 6. Exact Duplicate Rows
**Decision:** Drop. An exact duplicate row is redundant by definition — this doesn't require investigation output to justify, it's standard cleaning practice.
**Evidence (count):** *pending* — `check_duplicate_rows()` has been written but not yet run. **Update this line with the actual count once you run it**, for the audit trail.
**Implemented in:** `remove_exact_duplicates()`

---

## 7. Missing Customer ID — **PENDING**
**What's confirmed so far:** 243,007 rows missing (22.77%). Of these, 750 are cancelled ('C') invoices and 6 are adjustment ('A') invoices (already excluded/flagged above). The remaining **242,251 rows are normal sale invoices with no Customer ID** — this is the real decision.

**What's still needed before this can be finalised** (run `analyze_customer_country_consistency()`, `analyze_missing_customer_stockcodes()`, and `analyze_revenue_impact_of_missing_customer()` and paste the output):
- Does the missing-ID group cluster around non-product StockCodes (postage/manual/bank-charge codes), or genuine anonymous product sales?
- What % of total revenue do these rows represent?
- (Separately, for the SCD2 design) does any single Customer ID ever appear with more than one Country?

**Likely direction** (to confirm once evidence is in): keep these rows in `fact_sales` for accurate total-revenue reporting, but route them to a single `'Guest'` placeholder in `dim_customer` rather than dropping them — since RFM/customer-level analysis inherently can't apply to them anyway, this avoids losing real revenue from the top-line numbers while keeping customer-level analytics clean.

**Decision: NOT YET FINALISED.**

---

## 8. Country Standardisation — **PENDING**
**What's needed:** run `analyze_country()` and paste the full `Country` value distribution. Watch for near-duplicate or inconsistent naming (e.g. `EIRE` for Ireland, `Unspecified`, `European Community`) that needs mapping to a consistent name before these values become rows in `dim_country`.

**Decision: NOT YET FINALISED** — no mapping table can be written without seeing the actual distinct values.

---

## Next Steps
1. Run `python src/clean.py` (this now runs exploration + investigation + confirmed cleaning)
2. Paste the output of `run_investigation()` — specifically the Country distribution, the Customer-ID/Country consistency check, the missing-Customer-ID StockCode breakdown, and the revenue-impact figure, plus the duplicate row count
3. Sections 6 (count), 7, and 8 above get finalised and `handle_missing_customer_id()` / `standardize_country()` get added to `clean.py`
4. Only then does Phase 1 fully close and Phase 2 (staging load into SQL Server) begins — the grain of `dim_customer` and `dim_country` both depend on these two decisions
