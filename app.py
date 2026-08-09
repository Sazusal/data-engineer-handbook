"""Support Desk Flask Application.

Provides a REST API for managing support tickets stored in Lakebase (Postgres).

Endpoints:
- GET /: Main ticket management UI
- GET /healthz: Health check
- GET /tickets: List all tickets
- GET /tickets/<id>: Get a specific ticket
- GET /tickets/<id>/messages: Get messages for a ticket
- POST /tickets: Create a new ticket
- POST /tickets/<id>/messages: Add a message to a ticket
- PUT /tickets/<id>/status: Update ticket status

Deploy as a Databricks App using app.yaml.
"""

import logging
import os
from datetime import datetime

from databricks.sdk import WorkspaceClient
from flask import Flask, jsonify, render_template, request

import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("support-desk-app")

app = Flask(__name__)
_w = WorkspaceClient()


def _current_user_name() -> str:
    """
    Resolve the current user's name from the X-Forwarded-Email header.
    Falls back to SDK's current_user API for local development.
    """
    header_email = request.headers.get("X-Forwarded-Email")
    if header_email:
        return header_email.split("@")[0]  # Use email prefix as name
    return _w.current_user.me().user_name


@app.route("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.errorhandler(Exception)
def handle_exception(err):
    """Ensure all unhandled errors return JSON."""
    logger.exception("Unhandled exception while processing request")
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/")
def index():
    """Serve the main Support Desk UI."""
    return render_template("tickets.html")


@app.route("/tickets", methods=["GET"])
def list_tickets():
    """List all support tickets."""
    try:
        tickets = db.get_tickets()
        # Convert datetime objects to ISO strings
        for ticket in tickets:
            if ticket.get("created_at"):
                ticket["created_at"] = ticket["created_at"].isoformat()
        return jsonify(tickets)
    except Exception as e:
        logger.exception("Error listing tickets")
        return jsonify({"error": str(e)}), 500


@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Get a specific ticket by ID."""
    try:
        ticket = db.get_ticket(ticket_id)
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        
        # Convert datetime to ISO string
        if ticket.get("created_at"):
            ticket["created_at"] = ticket["created_at"].isoformat()
        
        return jsonify(ticket)
    except Exception as e:
        logger.exception(f"Error getting ticket {ticket_id}")
        return jsonify({"error": str(e)}), 500


@app.route("/tickets/<int:ticket_id>/messages", methods=["GET"])
def get_ticket_messages(ticket_id):
    """Get all messages for a specific ticket."""
    try:
        messages = db.get_ticket_messages(ticket_id)
        # Convert datetime objects to ISO strings
        for msg in messages:
            if msg.get("created_at"):
                msg["created_at"] = msg["created_at"].isoformat()
        return jsonify(messages)
    except Exception as e:
        logger.exception(f"Error getting messages for ticket {ticket_id}")
        return jsonify({"error": str(e)}), 500


@app.route("/tickets", methods=["POST"])
def create_ticket():
    """Create a new support ticket."""
    try:
        data = request.get_json()
        if not data or not data.get("title"):
            return jsonify({"error": "Title is required"}), 400
        
        title = data["title"].strip()
        created_by = data.get("created_by", _current_user_name()).strip()
        
        if not title:
            return jsonify({"error": "Title cannot be empty"}), 400
        
        # Ensure tables exist
        db.ensure_tables()
        
        ticket_id = db.create_ticket(title, created_by)
        return jsonify({"ticket_id": ticket_id, "message": "Ticket created successfully"}), 201
    
    except Exception as e:
        logger.exception("Error creating ticket")
        return jsonify({"error": str(e)}), 500


@app.route("/tickets/<int:ticket_id>/messages", methods=["POST"])
def add_message(ticket_id):
    """Add a message to an existing ticket."""
    try:
        data = request.get_json()
        if not data or not data.get("message_text"):
            return jsonify({"error": "Message text is required"}), 400
        
        message_text = data["message_text"].strip()
        author = data.get("author", _current_user_name()).strip()
        
        if not message_text:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        message_id = db.add_message(ticket_id, message_text, author)
        return jsonify({"message_id": message_id, "message": "Message added successfully"}), 201
    
    except Exception as e:
        logger.exception(f"Error adding message to ticket {ticket_id}")
        return jsonify({"error": str(e)}), 500


@app.route("/tickets/<int:ticket_id>/status", methods=["PUT"])
def update_status(ticket_id):
    """Update the status of an existing ticket."""
    try:
        data = request.get_json()
        if not data or not data.get("status"):
            return jsonify({"error": "Status is required"}), 400
        
        status = data["status"].strip().upper()
        db.update_ticket_status(ticket_id, status)
        
        return jsonify({"message": "Status updated successfully"})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error updating status for ticket {ticket_id}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Ensure database tables exist on startup
    try:
        db.ensure_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
    
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8000))
    app.run(debug=True, host=host, port=port)
    print(f"Support Desk app running on http://{host}:{port}")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
]


def format_datetime(value):
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Support Desk")

    st.divider()

    current_user = st.text_input(
        "Your name",
        value="Support Agent",
    )

    st.divider()

    if st.button(
        "🔄 Refresh tickets",
        use_container_width=True,
    ):
        st.rerun()


# ---------------------------------------------------------
# Main layout
# ---------------------------------------------------------

left_column, right_column = st.columns(
    [1, 2],
    gap="large",
)


# =========================================================
# LEFT: TICKET LIST
# =========================================================

with left_column:

    st.subheader("Tickets")

    try:
        tickets = get_tickets()
    except Exception as e:

        st.error(
            f"Unable to load tickets: {e}"
        )

        st.stop()

    if not tickets:

        st.info(
            "There are no support tickets yet."
        )

    else:

        ticket_options = {
            f"#{ticket['ticket_id']} — {ticket['title']} "
            f"({ticket['status']})":
            ticket["ticket_id"]
            for ticket in tickets
        }

        selected_label = st.radio(
            "Select a ticket",
            options=list(ticket_options.keys()),
        )

        selected_ticket_id = ticket_options[
            selected_label
        ]


# =========================================================
# RIGHT: TICKET DETAILS
# =========================================================

with right_column:

    if not tickets:

        st.info(
            "Create a ticket to get started."
        )

    else:

        ticket = get_ticket(
            selected_ticket_id
        )

        if not ticket:

            st.error(
                "Ticket no longer exists."
            )

            st.stop()

        st.subheader(
            f"Ticket #{ticket['ticket_id']}"
        )

        st.markdown(
            f"## {ticket['title']}"
        )

        # -------------------------------------------------
        # Ticket metadata
        # -------------------------------------------------

        metadata_col1, metadata_col2, metadata_col3 = (
            st.columns(3)
        )

        with metadata_col1:
            st.caption("Status")
            st.write(ticket["status"])

        with metadata_col2:
            st.caption("Created by")
            st.write(ticket["created_by"])

        with metadata_col3:
            st.caption("Created")
            st.write(
                format_datetime(
                    ticket["created_at"]
                )
            )

        st.divider()

        # -------------------------------------------------
        # Status update
        # -------------------------------------------------

        st.subheader("Update status")

        status_col1, status_col2 = st.columns(
            [2, 1]
        )

        with status_col1:

            new_status = st.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(
                    ticket["status"]
                ),
            )

        with status_col2:

            st.write("")
            st.write("")

            if st.button(
                "Update",
                use_container_width=True,
            ):

                try:

                    update_ticket_status(
                        selected_ticket_id,
                        new_status,
                    )

                    st.success(
                        "Status updated."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to update status: {e}"
                    )

        st.divider()

        # -------------------------------------------------
        # Messages
        # -------------------------------------------------

        st.subheader("Messages")

        try:

            messages = get_ticket_messages(
                selected_ticket_id
            )

        except Exception as e:

            st.error(
                f"Unable to load messages: {e}"
            )

            messages = []

        if not messages:

            st.info(
                "No messages yet."
            )

        else:

            for message in messages:

                with st.container(
                    border=True
                ):

                    author_col, date_col = st.columns(
                        [3, 2]
                    )

                    with author_col:

                        st.markdown(
                            f"**{message['author']}**"
                        )

                    with date_col:

                        st.caption(
                            format_datetime(
                                message["created_at"]
                            )
                        )

                    st.write(
                        message["message_text"]
                    )

        # -------------------------------------------------
        # Add message
        # -------------------------------------------------

        st.divider()

        st.subheader("Add message")

        with st.form("add_message_form"):

            message_text = st.text_area(
                "Message",
                placeholder=(
                    "Write your response..."
                ),
                height=120,
            )

            submitted = st.form_submit_button(
                "Send message",
                use_container_width=True,
            )

            if submitted:

                if not current_user.strip():

                    st.error(
                        "Please enter your name."
                    )

                elif not message_text.strip():

                    st.error(
                        "Message cannot be empty."
                    )

                else:

                    try:

                        add_message(
                            ticket_id=selected_ticket_id,
                            message_text=message_text.strip(),
                            author=current_user.strip(),
                        )

                        st.success(
                            "Message added."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Unable to add message: {e}"
                        )


# =========================================================
# CREATE TICKET
# =========================================================

st.divider()

st.subheader("➕ Create new ticket")

with st.form("create_ticket_form"):

    new_title = st.text_input(
        "Ticket title",
        placeholder="Example: Unable to access account",
    )

    create_submitted = st.form_submit_button(
        "Create ticket"
    )

    if create_submitted:

        if not current_user.strip():

            st.error(
                "Please enter your name."
            )

        elif not new_title.strip():

            st.error(
                "Ticket title cannot be empty."
            )

        else:

            try:

                ticket_id = create_ticket(
                    title=new_title.strip(),
                    created_by=current_user.strip(),
                )

                st.success(
                    f"Ticket #{ticket_id} created."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to create ticket: {e}"
                )