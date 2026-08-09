"""Database operations for the Support Desk ticket system.

Uses lakebase.py for all database connections and queries.
"""

import lakebase


def ensure_tables():
    """Create the tickets and ticket_messages tables if they don't exist."""
    lakebase.run_write(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    
    lakebase.run_write(
        """
        CREATE TABLE IF NOT EXISTS ticket_messages (
            message_id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id),
            message_text TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def get_tickets():
    """Return all support tickets ordered by creation date."""
    return lakebase.run_query(
        """
        SELECT
            ticket_id,
            title,
            status,
            created_by,
            created_at
        FROM tickets
        ORDER BY created_at DESC
        """
    )


def get_ticket(ticket_id: int):
    """Return a single ticket by ID."""
    results = lakebase.run_query(
        """
        SELECT
            ticket_id,
            title,
            status,
            created_by,
            created_at
        FROM tickets
        WHERE ticket_id = %s
        """,
        (ticket_id,)
    )
    return results[0] if results else None


def get_ticket_messages(ticket_id: int):
    """Return all messages for a specific ticket."""
    return lakebase.run_query(
        """
        SELECT
            message_id,
            ticket_id,
            message_text,
            author,
            created_at
        FROM ticket_messages
        WHERE ticket_id = %s
        ORDER BY created_at ASC
        """,
        (ticket_id,)
    )


def create_ticket(title: str, created_by: str) -> int:
    """Create a new support ticket and return its ID."""
    with lakebase.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tickets (title, status, created_by)
                VALUES (%s, 'OPEN', %s)
                RETURNING ticket_id
                """,
                (title, created_by)
            )
            ticket_id = cursor.fetchone()["ticket_id"]
        conn.commit()
    return ticket_id


def add_message(ticket_id: int, message_text: str, author: str) -> int:
    """Add a message to an existing ticket and return the message ID."""
    with lakebase.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ticket_messages (ticket_id, message_text, author)
                VALUES (%s, %s, %s)
                RETURNING message_id
                """,
                (ticket_id, message_text, author)
            )
            message_id = cursor.fetchone()["message_id"]
        conn.commit()
    return message_id


def update_ticket_status(ticket_id: int, status: str):
    """Update the status of an existing ticket."""
    allowed_statuses = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
    
    if status not in allowed_statuses:
        raise ValueError(f"Invalid ticket status: {status}")
    
    lakebase.run_write(
        """
        UPDATE tickets
        SET status = %s
        WHERE ticket_id = %s
        """,
        (status, ticket_id)
    )