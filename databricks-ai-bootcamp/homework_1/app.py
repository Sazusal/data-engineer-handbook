import streamlit as st

from db import (
    get_tickets,
    get_ticket,
    get_ticket_messages,
    create_ticket,
    add_message,
    update_ticket_status,
)


st.set_page_config(
    page_title="Support Desk",
    page_icon="🎫",
    layout="wide",
)


st.title("🎫 Support Desk")


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