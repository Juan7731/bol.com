"""
Database module for tracking processed orders
Prevents duplicate order processing
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Set, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file path
DB_FILE = "bol_orders.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table to track processed orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_orders (
                order_id TEXT NOT NULL,
                order_item_id TEXT,
                batch_number TEXT NOT NULL,
                batch_type TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (order_id, order_item_id)
            )
        """)
        
        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_id 
            ON processed_orders(order_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_item_id 
            ON processed_orders(order_item_id)
        """)
        
        logger.info("Database initialized successfully")


def is_order_processed(order_id: str, order_item_id: Optional[str] = None) -> bool:
    """
    Check if an order (or order item) has already been processed
    
    Args:
        order_id: Bol.com order ID
        order_item_id: Optional order item ID (for item-level tracking)
        
    Returns:
        True if order/item has been processed, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if order_item_id:
            cursor.execute("""
                SELECT 1 FROM processed_orders 
                WHERE order_id = ? AND order_item_id = ?
            """, (order_id, order_item_id))
        else:
            cursor.execute("""
                SELECT 1 FROM processed_orders 
                WHERE order_id = ?
            """, (order_id,))
        
        return cursor.fetchone() is not None


def mark_order_processed(
    order_id: str,
    batch_number: str,
    batch_type: str,
    order_item_id: Optional[str] = None
) -> None:
    """
    Mark an order (or order item) as processed
    
    Args:
        order_id: Bol.com order ID
        batch_number: Batch number (e.g., "001")
        batch_type: Batch type (Single, SingleLine, Multi)
        order_item_id: Optional order item ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO processed_orders 
            (order_id, order_item_id, batch_number, batch_type, processed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, order_item_id, batch_number, batch_type, datetime.now()))
        
        logger.debug(
            "Marked order %s (item: %s) as processed in batch %s (%s)",
            order_id, order_item_id or "N/A", batch_number, batch_type
        )


def get_unprocessed_orders(order_ids: List[str]) -> List[str]:
    """
    Filter out already processed orders
    
    Args:
        order_ids: List of order IDs to check
        
    Returns:
        List of order IDs that haven't been processed yet
    """
    if not order_ids:
        return []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(order_ids))
        cursor.execute(f"""
            SELECT order_id FROM processed_orders 
            WHERE order_id IN ({placeholders})
        """, order_ids)
        
        processed = {row[0] for row in cursor.fetchall()}
        unprocessed = [oid for oid in order_ids if oid not in processed]
        
        logger.info(
            "Filtered orders: %d unprocessed out of %d total",
            len(unprocessed), len(order_ids)
        )
        
        return unprocessed


def get_processed_count() -> int:
    """Get total number of processed orders"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_orders")
        return cursor.fetchone()[0]


def get_processed_orders_summary() -> dict:
    """Get summary of processed orders by batch type"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT batch_type, COUNT(*) as count
            FROM processed_orders
            GROUP BY batch_type
        """)
        
        summary = {}
        for row in cursor.fetchall():
            summary[row['batch_type']] = row['count']
        
        return summary

