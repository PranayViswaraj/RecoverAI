import sqlite3
from pathlib import Path
from .config import DATABASE_URL

DB_PATH = Path(__file__).resolve().parent.parent / "recoverai.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        lifetime_value REAL NOT NULL DEFAULT 0,
        successful_payments INTEGER NOT NULL DEFAULT 0,
        avg_order_value REAL NOT NULL DEFAULT 0,
        last_purchase_days_ago INTEGER NOT NULL DEFAULT 0,
        preferred_channel TEXT DEFAULT 'SMS'
    );

    CREATE TABLE IF NOT EXISTS transactions (
        payment_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        failure_reason TEXT,
        transaction_type TEXT NOT NULL DEFAULT 'payment',
        timestamp TEXT NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS recoveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE NOT NULL,
        recoverable INTEGER NOT NULL DEFAULT 1,
        recovery_probability REAL NOT NULL DEFAULT 0,
        recommended_action TEXT,
        explanation TEXT,
        confidence REAL DEFAULT 0,
        expected_recovery REAL DEFAULT 0,
        action_cost REAL DEFAULT 0,
        expected_roi REAL DEFAULT 0,
        risk_score REAL DEFAULT 0,
        guardrail_status TEXT DEFAULT 'AUTO',
        action_status TEXT DEFAULT 'PENDING',
        razorpay_payment_link_id TEXT,
        razorpay_payment_link_url TEXT,
        recovered_amount REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        executed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT,
        action TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS webhook_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        received_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
