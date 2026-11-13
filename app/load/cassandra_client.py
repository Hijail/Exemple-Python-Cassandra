from cassandra.cluster import Cluster, Session
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy


def connect(hosts, port, local_dc) -> tuple:
    cluster = Cluster(
        contact_points=hosts,
        port=port,
        protocol_version=5,
        load_balancing_policy=TokenAwarePolicy(
            DCAwareRoundRobinPolicy(local_dc=local_dc)
        ),
    )
    try:
        session = cluster.connect()
    except Exception:
        cluster.shutdown()
        raise
    return cluster, session
