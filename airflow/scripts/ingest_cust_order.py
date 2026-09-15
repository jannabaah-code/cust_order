#!/usr/bin/env python3
"""
=============================================================
ETL PIPELINE: customer_orders.csv → SQLite Star Schema
=============================================================
Tables loaded (in order):
  1. dim_customers  — deduplicated customer reference data
  2. dim_products   — deduplicated product catalog
  3. fct_orders     — one row per order transaction (fact)

Usage:
  python ingest_pipeline.py [--csv PATH] [--db PATH]

Defaults:
  --csv  customer_orders.csv
  --db   orders.db
=============================================================
"""

import sqlite3
import csv
import logging
import argparse
import sys
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
VALID_STATUSES   = {"delivered", "shipped", "processing", "cancelled"}
VALID_CURRENCIES = {"USD"}
REQUIRED_COLUMNS = {
    "order_id", "customer_id", "customer_name", "customer_email",
    "product_id", "product_name", "product_category",
    "order_amount", "order_currency", "order_date", "order_status",
}

# ─────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────
DDL_DIM_CUSTOMERS = """
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     INTEGER         NOT NULL,
    customer_name   TEXT            NOT NULL,
    customer_email  TEXT            NOT NULL,
    CONSTRAINT pk_dim_customers   PRIMARY KEY (customer_id),
    CONSTRAINT uq_customer_email  UNIQUE      (customer_email)
);
"""

DDL_DIM_PRODUCTS = """
CREATE TABLE IF NOT EXISTS dim_products (
    product_id       INTEGER NOT NULL,
    product_name     TEXT    NOT NULL,
    product_category TEXT    NOT NULL,
    CONSTRAINT pk_dim_products PRIMARY KEY (product_id)
);
"""

DDL_FCT_ORDERS = """
CREATE TABLE IF NOT EXISTS fct_orders (
    order_id        INTEGER         NOT NULL,
    customer_id     INTEGER         NOT NULL,
    product_id      INTEGER         NOT NULL,
    order_amount    REAL            NOT NULL,
    order_currency  TEXT            NOT NULL DEFAULT 'USD',
    order_date      TEXT            NOT NULL,
    order_status    TEXT            NOT NULL,
    CONSTRAINT pk_fct_orders
        PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    CONSTRAINT fk_orders_product
        FOREIGN KEY (product_id)  REFERENCES dim_products(product_id),
    CONSTRAINT chk_order_status
        CHECK (order_status IN ('delivered','shipped','processing','cancelled'))
);
"""

# ─────────────────────────────────────────────
# STEP 1 — EXTRACT
# ─────────────────────────────────────────────
def extract(csv_path: Path) -> list[dict]:
    """Read CSV and return list of raw row dicts."""
    log.info(f"[EXTRACT] Reading: {csv_path}")
    if not csv_path.exists():
        log.error(f"File not found: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Strip BOM / whitespace from header names
        reader.fieldnames = [h.strip().lstrip("\ufeff") for h in reader.fieldnames]

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            log.error(f"Missing columns in CSV: {missing}")
            sys.exit(1)

        for i, row in enumerate(reader, start=2):           # row 1 = header
            rows.append({k.strip(): v.strip() for k, v in row.items()})

    log.info(f"[EXTRACT] Rows read: {len(rows)}")
    return rows

# ─────────────────────────────────────────────
# STEP 2 — TRANSFORM & VALIDATE
# ─────────────────────────────────────────────
def _parse_date(value: str, row_num: int) -> str:
    """Validate and normalise date to YYYY-MM-DD."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Row {row_num}: unparseable date '{value}'")

def _parse_decimal(value: str, row_num: int) -> float:
    """Validate numeric amount."""
    try:
        d = Decimal(value)
        if d < 0:
            raise ValueError("Negative amount")
        return float(d)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Row {row_num}: invalid order_amount '{value}'")

def transform(raw_rows: list[dict]) -> dict:
    """
    Clean, validate, and split raw rows into three target datasets.
    Returns:
        {
          "customers": deduplicated list of customer dicts,
          "products":  deduplicated list of product dicts,
          "orders":    list of order fact dicts,
          "skipped":   count of invalid rows,
        }
    """
    log.info("[TRANSFORM] Cleaning and validating rows …")

    customers_seen = {}   # customer_id -> dict
    products_seen  = {}   # product_id  -> dict
    orders         = []
    skipped        = 0

    for i, row in enumerate(raw_rows, start=2):
        try:
            # ── Type casting ──────────────────────────────
            order_id    = int(row["order_id"])
            customer_id = int(row["customer_id"])
            product_id  = int(row["product_id"])
            order_amount = _parse_decimal(row["order_amount"], i)
            order_date   = _parse_date(row["order_date"], i)

            # ── Normalise strings ─────────────────────────
            customer_name   = row["customer_name"].strip().title()
            customer_email  = row["customer_email"].strip().lower()
            product_name    = row["product_name"].strip()
            product_category = row["product_category"].strip()
            order_currency  = row["order_currency"].strip().upper()
            order_status    = row["order_status"].strip().lower()

            # ── Validate constrained fields ───────────────
            if order_status not in VALID_STATUSES:
                raise ValueError(f"Invalid order_status '{order_status}'")
            if order_currency not in VALID_CURRENCIES:
                raise ValueError(f"Unsupported currency '{order_currency}'")
            if not customer_email or "@" not in customer_email:
                raise ValueError(f"Invalid email '{customer_email}'")

            # ── Deduplicate dimensions ────────────────────
            if customer_id not in customers_seen:
                customers_seen[customer_id] = {
                    "customer_id":    customer_id,
                    "customer_name":  customer_name,
                    "customer_email": customer_email,
                }

            if product_id not in products_seen:
                products_seen[product_id] = {
                    "product_id":       product_id,
                    "product_name":     product_name,
                    "product_category": product_category,
                }

            orders.append({
                "order_id":       order_id,
                "customer_id":    customer_id,
                "product_id":     product_id,
                "order_amount":   order_amount,
                "order_currency": order_currency,
                "order_date":     order_date,
                "order_status":   order_status,
            })

        except ValueError as e:
            log.warning(f"[TRANSFORM] Skipping row {i}: {e}")
            skipped += 1

    log.info(
        f"[TRANSFORM] Valid orders: {len(orders)} | "
        f"Customers: {len(customers_seen)} | "
        f"Products: {len(products_seen)} | "
        f"Skipped: {skipped}"
    )
    return {
        "customers": list(customers_seen.values()),
        "products":  list(products_seen.values()),
        "orders":    orders,
        "skipped":   skipped,
    }

# ─────────────────────────────────────────────
# STEP 3 — LOAD
# ─────────────────────────────────────────────
def load(db_path: Path, data: dict) -> None:
    """Create tables and insert all records into SQLite."""
    log.info(f"[LOAD] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    try:
        # Create tables
        log.info("[LOAD] Creating tables (if not exist) …")
        cur.executescript(DDL_DIM_CUSTOMERS + DDL_DIM_PRODUCTS + DDL_FCT_ORDERS)

        # ── dim_customers ─────────────────────────────────
        log.info(f"[LOAD] Inserting {len(data['customers'])} rows → dim_customers …")
        cur.executemany(
            """INSERT OR IGNORE INTO dim_customers
               (customer_id, customer_name, customer_email)
               VALUES (:customer_id, :customer_name, :customer_email)""",
            data["customers"],
        )

        # ── dim_products ──────────────────────────────────
        log.info(f"[LOAD] Inserting {len(data['products'])} rows → dim_products …")
        cur.executemany(
            """INSERT OR IGNORE INTO dim_products
               (product_id, product_name, product_category)
               VALUES (:product_id, :product_name, :product_category)""",
            data["products"],
        )

        # ── fct_orders ────────────────────────────────────
        log.info(f"[LOAD] Inserting {len(data['orders'])} rows → fct_orders …")
        cur.executemany(
            """INSERT OR IGNORE INTO fct_orders
               (order_id, customer_id, product_id, order_amount,
                order_currency, order_date, order_status)
               VALUES (:order_id, :customer_id, :product_id, :order_amount,
                       :order_currency, :order_date, :order_status)""",
            data["orders"],
        )

        conn.commit()
        log.info("[LOAD] Commit successful.")

    except sqlite3.Error as e:
        conn.rollback()
        log.error(f"[LOAD] Database error — rolled back: {e}")
        sys.exit(1)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# STEP 4 — VALIDATE
# ─────────────────────────────────────────────
def validate(db_path: Path) -> None:
    """Run post-load row-count and integrity checks."""
    log.info("[VALIDATE] Running post-load checks …")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    checks = {
        "dim_customers row count": "SELECT COUNT(*) FROM dim_customers",
        "dim_products  row count": "SELECT COUNT(*) FROM dim_products",
        "fct_orders    row count": "SELECT COUNT(*) FROM fct_orders",
        "Orphan customer FKs"    : """SELECT COUNT(*) FROM fct_orders o
                                       LEFT JOIN dim_customers c USING (customer_id)
                                       WHERE c.customer_id IS NULL""",
        "Orphan product FKs"     : """SELECT COUNT(*) FROM fct_orders o
                                       LEFT JOIN dim_products p USING (product_id)
                                       WHERE p.product_id IS NULL""",
        "NULL order amounts"     : "SELECT COUNT(*) FROM fct_orders WHERE order_amount IS NULL",
        "Invalid statuses"       : """SELECT COUNT(*) FROM fct_orders
                                       WHERE order_status NOT IN
                                       ('delivered','shipped','processing','cancelled')""",
    }

    all_passed = True
    for label, sql in checks.items():
        count = cur.execute(sql).fetchone()[0]
        orphan_check = "Orphan" in label or "Invalid" in label or "NULL" in label
        status = "✓ PASS" if (count == 0 if orphan_check else count > 0) else "✗ FAIL"
        if "FAIL" in status:
            all_passed = False
        log.info(f"[VALIDATE]  {status}  |  {label}: {count}")

    conn.close()
    if all_passed:
        log.info("[VALIDATE] All checks passed. Pipeline complete. ✓")
    else:
        log.warning("[VALIDATE] One or more checks failed. Review the output above.")

# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ingest customer_orders.csv into SQLite star schema.")
    parser.add_argument("--csv", default="customer_orders.csv", help="Path to source CSV file")
    parser.add_argument("--db",  default="orders.db",           help="Path to target SQLite database")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    db_path  = Path(args.db)

    log.info("=" * 60)
    log.info("  ETL PIPELINE START")
    log.info(f"  Source : {csv_path}")
    log.info(f"  Target : {db_path}")
    log.info("=" * 60)

    raw   = extract(csv_path)
    data  = transform(raw)
    load(db_path, data)
    validate(db_path)

    log.info("=" * 60)
    log.info("  ETL PIPELINE COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
