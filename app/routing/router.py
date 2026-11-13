import pandas as pd

from app.routing.registry import TRANSFORM_REGISTRY


def transform_for_table(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    transform = TRANSFORM_REGISTRY.get(table_name)
    if transform is None:
        raise KeyError("Aucune transformation enregistrée pour '{}'".format(table_name))
    return transform(df)
