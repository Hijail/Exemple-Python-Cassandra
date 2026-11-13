"""Local Streamlit dashboard for the Cassandra read projections."""
from datetime import date

import pandas as pd
import streamlit as st

from app.config import get_settings
from app.load.cassandra_client import connect


MAX_ROWS = 500


def read_partition(session, query, values):
    statement = session.prepare(query)
    statement.fetch_size = MAX_ROWS
    result = session.execute(statement, values)
    return pd.DataFrame(list(result))


def main():
    st.set_page_config(page_title="Cassandra Analytics", page_icon="📊", layout="wide")
    st.title("Cassandra Analytics")
    st.caption("Exploration des projections ETL — requêtes limitées aux partitions Cassandra.")
    settings = get_settings()

    try:
        cluster, session = connect(
            settings.cassandra_hosts, settings.cassandra_port, settings.local_dc
        )
    except Exception as exc:
        st.error("Connexion à Cassandra impossible. Vérifiez le service et le fichier .env.")
        st.exception(exc)
        return

    try:
        tabs = st.tabs(["Joueur / jour", "Type / jour", "Achats / mois"])

        with tabs[0]:
            with st.form("player_day_form"):
                player_id = st.text_input("Player ID", "player-001")
                event_day = st.date_input("Date", value=date.today())
                submitted = st.form_submit_button("Charger les événements")
            if submitted:
                if not player_id.strip():
                    st.warning("Saisissez un player ID.")
                else:
                    try:
                        frame = read_partition(
                            session,
                            f"SELECT * FROM {settings.keyspace}.events_by_player_day "
                            "WHERE player_id = ? AND event_day = ? LIMIT 500",
                            (player_id.strip(), event_day),
                        )
                        st.metric("Événements", len(frame))
                        if not frame.empty:
                            st.dataframe(frame, use_container_width=True, hide_index=True)
                            if "event_type" in frame:
                                st.bar_chart(frame["event_type"].value_counts())
                        else:
                            st.info("Aucun événement dans cette partition.")
                    except Exception as exc:
                        st.error("Lecture Cassandra impossible pour cette partition.")
                        st.exception(exc)

        with tabs[1]:
            with st.form("type_day_form"):
                event_type = st.selectbox(
                    "Type d'événement", ["login", "logout", "level_completed", "purchase"]
                )
                type_day = st.date_input("Date", value=date.today(), key="type_day")
                submitted = st.form_submit_button("Charger les événements")
            if submitted:
                try:
                    frame = read_partition(
                        session,
                        f"SELECT * FROM {settings.keyspace}.events_by_type_day "
                        "WHERE event_type = ? AND event_day = ? LIMIT 500",
                        (event_type, type_day),
                    )
                    st.metric("Événements", len(frame))
                    if frame.empty:
                        st.info("Aucun événement dans cette partition.")
                    else:
                        st.dataframe(frame, use_container_width=True, hide_index=True)
                        if "amount" in frame and frame["amount"].notna().any():
                            st.metric("Montant total", f"{frame['amount'].sum():,.2f}")
                except Exception as exc:
                    st.error("Lecture Cassandra impossible pour cette partition.")
                    st.exception(exc)

        with tabs[2]:
            with st.form("purchase_form"):
                player_id = st.text_input("Player ID", "player-001", key="purchase_player")
                purchase_month = st.text_input("Mois (AAAA-MM)", date.today().strftime("%Y-%m"))
                submitted = st.form_submit_button("Charger les achats")
            if submitted:
                if not player_id.strip() or len(purchase_month) != 7:
                    st.warning("Saisissez un player ID et un mois au format AAAA-MM.")
                else:
                    try:
                        frame = read_partition(
                            session,
                            f"SELECT * FROM {settings.keyspace}.purchases_by_player_month "
                            "WHERE player_id = ? AND purchase_month = ? LIMIT 500",
                            (player_id.strip(), purchase_month),
                        )
                        if frame.empty:
                            st.info("Aucun achat dans cette partition.")
                        else:
                            anomalies = int(frame["is_anomaly"].fillna(False).sum())
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Achats", len(frame))
                            col2.metric("Anomalies", anomalies)
                            col3.metric("Montant total", f"{frame['amount'].sum():,.2f}")
                            st.dataframe(frame, use_container_width=True, hide_index=True)
                            st.bar_chart(frame.set_index("occurred_at")["amount"])
                    except Exception as exc:
                        st.error("Lecture Cassandra impossible pour cette partition.")
                        st.exception(exc)
    finally:
        cluster.shutdown()


if __name__ == "__main__":
    main()
