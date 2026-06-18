import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite tables for logs and histories."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. AI Scores History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_scores_history (
        date TEXT PRIMARY KEY,
        market_score INTEGER,
        risk_score INTEGER,
        opportunity_score INTEGER,
        logged_at TEXT
    )
    """)
    
    # 2. VNINDEX Forecast History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vnindex_predictions (
        date TEXT PRIMARY KEY,
        trend TEXT,
        probability REAL,
        predicted_range TEXT,
        warning TEXT,
        logged_at TEXT
    )
    """)
    
    # 3. Portfolio History Snapshot Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_history (
        date TEXT PRIMARY KEY,
        total_cost REAL,
        total_value REAL,
        pnl REAL,
        pnl_pct REAL,
        logged_at TEXT
    )
    """)
    
    # Insert initial historical data to mock database if empty
    cursor.execute("SELECT COUNT(*) FROM ai_scores_history")
    if cursor.fetchone()[0] == 0:
        # Generate some mock history for the past 10 days
        import random
        from datetime import timedelta
        base_date = datetime.now()
        for i in range(15, -1, -1):
            date_str = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
            m_score = random.randint(55, 75)
            r_score = random.randint(25, 45)
            o_score = random.randint(60, 80)
            cursor.execute(
                "INSERT INTO ai_scores_history (date, market_score, risk_score, opportunity_score, logged_at) VALUES (?, ?, ?, ?, ?)",
                (date_str, m_score, r_score, o_score, datetime.now().isoformat())
            )
            
            # Forecasts history
            trends = ["Tăng nhẹ", "Đi ngang", "Giảm nhẹ", "Tăng mạnh"]
            trend = random.choice(trends)
            prob = round(random.uniform(0.55, 0.78), 2)
            lower = random.randint(1230, 1250)
            upper = lower + random.randint(8, 15)
            range_str = f"{lower:,} - {upper:,} điểm"
            warn = "Ổn định thị trường" if "Tăng" in trend else "Áp lực tỷ giá tăng cao"
            cursor.execute(
                "INSERT OR IGNORE INTO vnindex_predictions (date, trend, probability, predicted_range, warning, logged_at) VALUES (?, ?, ?, ?, ?, ?)",
                (date_str, trend, prob, range_str, warn, datetime.now().isoformat())
            )
            
            # Portfolio history
            cost = 445000000.0
            val = cost + random.uniform(-10000000, 45000000)
            pnl = val - cost
            pnl_pct = pnl / cost
            cursor.execute(
                "INSERT OR IGNORE INTO portfolio_history (date, total_cost, total_value, pnl, pnl_pct, logged_at) VALUES (?, ?, ?, ?, ?, ?)",
                (date_str, cost, val, pnl, pnl_pct, datetime.now().isoformat())
            )
            
    conn.commit()
    conn.close()

def log_ai_scores(market_score: int, risk_score: int, opportunity_score: int, date_str: str = None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO ai_scores_history (date, market_score, risk_score, opportunity_score, logged_at)
    VALUES (?, ?, ?, ?, ?)
    """, (date_str, market_score, risk_score, opportunity_score, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_historical_scores(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_scores_history ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)] # chronological order

def log_prediction(trend: str, probability: float, predicted_range: str, warning: str, date_str: str = None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO vnindex_predictions (date, trend, probability, predicted_range, warning, logged_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, trend, probability, predicted_range, warning, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_historical_predictions(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vnindex_predictions ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def log_portfolio_snapshot(total_cost: float, total_value: float, pnl: float, pnl_pct: float, date_str: str = None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO portfolio_history (date, total_cost, total_value, pnl, pnl_pct, logged_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, total_cost, total_value, pnl, pnl_pct, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_portfolio_history(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio_history ORDER BY date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]
