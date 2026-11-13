from typing import Callable, Dict

import pandas as pd

from app.transform.player import transform_player_events
from app.transform.event_type import transform_events_by_type


Transform = Callable[[pd.DataFrame], pd.DataFrame]

# Une fonction par projection Cassandra.
TRANSFORM_REGISTRY: Dict[str, Transform] = {
    "events_by_player_day": transform_player_events,
    "events_by_type_day": transform_events_by_type,
}
