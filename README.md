# Brokerage Transaction Analyzer

A FastAPI web application to upload your TastyTrade CSVs, parse and classify every trade (including option spreads), tag them (CORE, Satellite, Growth, Value, Speculative), fetch industry data, and deliver P&L, current holdings, and exposure analytics.

---

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [Tech Stack](#tech-stack)  
4. [Getting Started](#getting-started)  
5. [SPEC (final)](#spec-final)  
6. [Next Steps / Implementation Plan](#next-steps--implementation-plan)  
7. [Contributing](#contributing)  
8. [License](#license)  

---

## Overview

This tool ingests a TastyTrade CSV (with Europe/Bucharest timestamps and columns like `Type`, `Subtype`, `Action`, `Symbol`, `Quantity`, `Price`, `Fees`, etc.), then:

1. Parses each row into a `Transaction` record  
2. Auto-classifies into:
   - Deposits / Withdrawals  
   - Stock/ETF Buys & Sells  
   - Option trades (Buy, Sell, Assignment, Expiration)  
   - Option spreads (grouped by timestamp + root symbol + quantity)  
   - Dividends, Fees, Adjustments  
3. Fetches industry & sector data (via Yahoo Finance or a public API)  
4. Allows manual tagging and comments:
   - Strategy tag (CORE, Satellite, Growth, Value, Speculative)  
   - Industry tag (auto-fetched or manually overridden)  
   - Free-text comments & reasons (Open, Close, Keep)  
5. Persists data in SQLite for ongoing analysis  
6. Displays P&L (realized & unrealized), trade duration, current holdings, and exposure  
7. Exports filtered transactions back to CSV  

We’ll use server-rendered HTML (Jinja2) enhanced by HTMX for responsiveness, plus pytest for tests.

---

## Features

- CSV upload & parsing  
- Auto-classification based on CSV columns  
- Group option-spread legs automatically  
- Fetch industry & sector from public APIs (e.g., Yahoo Finance)  
- Manual tagging UI (strategy, industry, comments)  
- Persistent storage in SQLite (SQLModel)  
- Transaction list with date/type/tag filters & pagination  
- Summary dashboards:
  - Realized P&L by month & tag  
  - Unrealized P&L & current positions  
  - Exposure by symbol & spread  
  - Trade durations (open vs. close dates)  
- CSV export of filtered data  

---

## Tech Stack

- Python ≥ 3.9  
- FastAPI + Uvicorn  
- SQLModel (SQLite)  
- Jinja2 + HTMX  
- HTTPX or `yfinance` for industry data  
- pytest  

---

## Getting Started

### Prerequisites

- macOS (or Linux/Windows)  
- **Python 3.11 or 3.12** (Python 3.14 is not yet fully supported by SQLModel)
- `venv` or `virtualenv`  

### Installation

```bash
git clone https://github.com/you/brokerage-transactions.git
cd brokerage-transactions
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Locally

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## SPEC (final)

### 1. Purpose & Scope
- **Goal:** Single-user FastAPI app to upload, classify, tag, and analyze TastyTrade CSV transactions.  
- **Out of Scope (v1):** Authentication, billing/pay flows, multi-user.

### 2. Functional Requirements

1. **Upload & Parse**  
   - CSV upload endpoint reads Europe/Bucharest datetime and relevant columns.  
2. **Auto-Classification**  
   - Map CSV fields (`Type`, `Subtype`, `Action`) → categories:  
     - `deposit` / `withdrawal`  
     - `stock_buy` / `stock_sell`  
     - `option_buy` / `option_sell` / `option_assignment` / `option_expiration`  
     - `spread` (multi-leg grouping)  
     - `dividend` / `fee` / `adjustment`  
3. **Spread Grouping**  
   - Group legs by identical timestamp, root symbol, and matching quantity into `Spread` entities.  
4. **Industry & Sector**  
   - On transaction import, fetch industry & sector via public API (e.g., Yahoo Finance).  
   - Allow manual override.  
5. **Tagging**  
   - Manual tags:  
     - `strategy_tag` ∈ {CORE, Satellite, Growth, Value, Speculative}  
     - `industry_tag` (auto or manual)  
     - `comment` (reason: Open/Close/Keep)  
6. **Persistence**  
   - SQLite via SQLModel, with full history.  
7. **Filtering & Views**  
   - List transactions with filters (date range, category, tags, account).  
   - Detail view to edit tags/comments.  
8. **Summary & Analytics**  
   - Realized P&L by month & tag  
   - Unrealized P&L & current positions by symbol/spread  
   - Exposure (underlying notional)  
   - Trade duration metrics  
9. **Positions Table**  
   - Compute open positions and exposures, updated on each import.  
10. **CSV Export**  
    - Download filtered transactions as CSV.

### 3. Data Models

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Account(SQLModel, table=True):
    id:         int     = Field(default=None, primary_key=True)
    name:       str     # e.g. "TastyTrade Main"
    transactions: list["Transaction"] = Relationship(back_populates="account")

class Spread(SQLModel, table=True):
    id:          int      = Field(default=None, primary_key=True)
    created_at:  datetime
    description: Optional[str]
    legs:        list["Transaction"] = Relationship(back_populates="spread")

class Transaction(SQLModel, table=True):
    id:               int          = Field(default=None, primary_key=True)
    txn_id:           str          # original trade ID
    datetime:         datetime     # Europe/Bucharest tz
    type:             str          # e.g. "option_buy"
    subtype:          str          # raw CSV subtype
    action:           str          # raw CSV action
    symbol:           str
    quantity:         float
    price:            float
    fees:             float
    net_amount:       float
    description:      Optional[str]
    strategy_tag:     Optional[str]
    industry_tag:     Optional[str]
    comment:          Optional[str]  # reason: Open/Close/Keep
    account_id:       int
    account:          Account       = Relationship(back_populates="transactions")
    spread_id:        Optional[int]
    spread:           Optional[Spread] = Relationship(back_populates="legs")

class Position(SQLModel, table=True):
    id:               int          = Field(default=None, primary_key=True)
    symbol:           str
    quantity:         float
    average_price:    float
    updated_at:       datetime
```

### 4. Endpoints & Views

| Method | Path                 | Description                          |
| ------ | -------------------- | ------------------------------------ |
| GET    | `/`                  | Home & CSV upload form               |
| POST   | `/upload/`           | Upload CSV → parse, classify, tag    |
| GET    | `/transactions/`     | List + filters + pagination          |
| GET    | `/transactions/{id}` | Detail + edit tags/comments          |
| GET    | `/spreads/`          | List grouped spreads                 |
| GET    | `/positions/`        | Current positions & exposures        |
| GET    | `/summary/`          | Dashboards (P&L, durations, exposure)|
| GET    | `/export/`           | Download filtered CSV                |

### 5. Non-Functional Requirements

- **Local Run:** Python venv on macOS.  
- **Minimal Dependencies:** FastAPI, SQLModel, HTMX, pytest.  
- **Timezone Handling:** Store all datetimes in UTC internally, display in Europe/Bucharest.  
- **Testing:** Comprehensive pytest suite for parsing, classification, grouping, tagging.

---

## Next Steps / Implementation Plan

1. **Project Scaffold**  
   - Create FastAPI app structure (`app/main.py`, routers, models).  
2. **CSV Parsing Module**  
   - Read CSV, normalize datetimes, map to `Transaction`.  
3. **Classification Logic**  
   - Implement mapping from CSV columns → `type`.  
4. **Spread Grouping**  
   - Group by timestamp + root symbol + qty.  
5. **Industry Fetch Service**  
   - Integrate with Yahoo Finance / public API.  
6. **Database Models & Migrations**  
   - Define SQLModel schemas, initialize SQLite.  
7. **Views & Templates**  
   - Jinja2 + HTMX for upload, list, detail, summary.  
8. **Tests**  
   - pytest for each module.  
9. **CSV Export**  
   - Endpoint to stream filtered CSV.  

---

## Contributing

1. Fork & clone this repo.  
2. Create a feature branch (`git checkout -b feat/…`).  
3. Commit changes & open a Pull Request.  

---

## License

MIT © Your Name  