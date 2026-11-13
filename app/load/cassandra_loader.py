import logging
from typing import Dict

import pandas as pd
from cassandra.cluster import Session
from cassandra.query import PreparedStatement

LOGGER = logging.getLogger(__name__)

INSERTS = {
    "events_by_player_day": (
        "INSERT INTO {keyspace}.events_by_player_day "
        "(player_id, event_day, occurred_at, event_id, event_type, "
        "session_id, level_id, score, amount, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
    "events_by_type_day": (
        "INSERT INTO {keyspace}.events_by_type_day "
        "(event_type, event_day, occurred_at, event_id, player_id, "
        "session_id, level_id, amount, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
    "purchases_by_player_month": (
        "INSERT INTO {keyspace}.purchases_by_player_month "
        "(player_id, purchase_month, occurred_at, event_id, product_id, "
        "category, quantity, amount, currency, anomaly_score, is_anomaly) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
}

# Pandas promotes nullable integer columns (such as quantity) to float64.
INTEGER_COLUMNS = {"purchases_by_player_month": {"quantity"}}


class CassandraLoader:
    def __init__(self, session: Session, keyspace: str, max_in_flight: int = 64):
        self.session = session
        self.max_in_flight = max_in_flight
        self.statements: Dict[str, PreparedStatement] = {
            table: session.prepare(query.format(keyspace=keyspace))
            for table, query in INSERTS.items()
        }

    @staticmethod
    def _python_value(value, integer=False):
        if pd.isna(value):
            return None
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()
        if hasattr(value, "item"):
            value = value.item()
        if integer:
            numeric = float(value)
            if not numeric.is_integer() or not -(2**31) <= numeric < 2**31:
                raise ValueError("La quantité doit être un entier Cassandra 32 bits.")
            return int(numeric)
        return value

    def load(self, table_name: str, df: pd.DataFrame) -> int:
        if table_name not in self.statements:
            raise KeyError("Table non autorisée : {}".format(table_name))

        statement = self.statements[table_name]
        pending = []
        loaded = 0

        if self.max_in_flight < 1:
            raise ValueError("max_in_flight doit être supérieur ou égal à 1.")

        def drain_batch(futures):
            """Wait for Cassandra driver's ResponseFuture objects."""
            first_error = None
            completed = 0
            for future in futures:
                try:
                    future.result()
                    completed += 1
                except Exception as exc:  # drain the batch before surfacing failure
                    if first_error is None:
                        first_error = exc
            if first_error is not None:
                raise first_error
            return completed

        # Limite le nombre de futures en vol pour éviter de saturer le driver.
        for row in df.itertuples(index=False, name=None):
            values = tuple(
                self._python_value(
                    value,
                    integer=column in INTEGER_COLUMNS.get(table_name, set()),
                )
                for column, value in zip(df.columns, row)
            )
            pending.append(self.session.execute_async(statement, values))

            if len(pending) >= self.max_in_flight:
                loaded += drain_batch(pending)
                pending = []

        loaded += drain_batch(pending)

        LOGGER.info("%s lignes insérées dans %s", loaded, table_name)
        return loaded
