import base64
import os

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from databricks.sdk import WorkspaceClient


_workspace = WorkspaceClient()

SECRET_SCOPE = os.environ.get(
    "LAKEBASE_SECRET_SCOPE",
    "database",
)

SECRET_KEY = os.environ.get(
    "LAKEBASE_SECRET_KEY",
    "lakebase-url",
)


def get_lakebase_url() -> str:
    """
    Retrieve the Lakebase PostgreSQL connection URL
    from the Databricks secret scope.
    """

    secret = _workspace.secrets.get_secret(
        scope=SECRET_SCOPE,
        key=SECRET_KEY,
    )

    return base64.b64decode(secret.value).decode("utf-8")


@contextmanager
def get_connection():
    """
    Open a Lakebase connection and close it automatically.
    """

    conn = psycopg2.connect(
        get_lakebase_url(),
        cursor_factory=RealDictCursor,
    )

    try:
        yield conn
    finally:
        conn.close()


def get_tickets():
    """
    Return all support tickets.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
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

            return cursor.fetchall()


def get_ticket(ticket_id: int):
    """
    Return one ticket.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
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
                (ticket_id,),
            )

            return cursor.fetchone()


def get_ticket_messages(ticket_id: int):
    """
    Return all messages belonging to a ticket.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
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
                (ticket_id,),
            )

            return cursor.fetchall()


def create_ticket(title: str, created_by: str):
    """
    Create a new support ticket.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO tickets (
                    title,
                    status,
                    created_by
                )
                VALUES (%s, 'OPEN', %s)
                RETURNING ticket_id
                """,
                (title, created_by),
            )

            ticket_id = cursor.fetchone()["ticket_id"]

        conn.commit()

    return ticket_id


def add_message(
    ticket_id: int,
    message_text: str,
    author: str,
):
    """
    Add a message to an existing ticket.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO ticket_messages (
                    ticket_id,
                    message_text,
                    author
                )
                VALUES (%s, %s, %s)
                RETURNING message_id
                """,
                (
                    ticket_id,
                    message_text,
                    author,
                ),
            )

            message_id = cursor.fetchone()["message_id"]

        conn.commit()

    return message_id


def update_ticket_status(
    ticket_id: int,
    status: str,
):
    """
    Update the status of an existing ticket.
    """

    allowed_statuses = {
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED",
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid ticket status")

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE tickets
                SET status = %s
                WHERE ticket_id = %s
                """,
                (
                    status,
                    ticket_id,
                ),
            )

        conn.commit()