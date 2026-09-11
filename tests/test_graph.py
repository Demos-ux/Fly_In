import pytest

from graph import Graph
from parser import Connection, RouteConfig, Zone


def make_config(
    zones: dict[str, Zone] | None = None,
    connections: list[Connection] | None = None,
) -> RouteConfig:
    if zones is None:
        zones = {
            "start": Zone(role="start_hub", name="start", x=0, y=0),
            "middle": Zone(role="hub", name="middle", x=1, y=0),
            "goal": Zone(role="end_hub", name="goal", x=2, y=0),
        }

    if connections is None:
        connections = [
            Connection(z1="start", z2="middle"),
            Connection(
                z1="middle",
                z2="goal",
                max_link_capacity=2,
            ),
        ]

    return RouteConfig(
        nb_drones=2,
        zones=zones,
        connections=connections,
    )


def test_graph_builds_undirected_adjacency():
    graph = Graph(make_config())

    assert graph.all_vertices() == {"start", "middle", "goal"}
    assert graph.neighbors("start") == ["middle"]
    assert graph.neighbors("middle") == ["start", "goal"]
    assert graph.neighbors("goal") == ["middle"]


def test_graph_returns_connections_and_capacity():
    graph = Graph(make_config())

    connection = graph.connection_between("goal", "middle")

    assert connection is not None
    assert connection.max_link_capacity == 2
    assert graph.edges("middle") == graph.all_edges()
    assert graph.connection_between("start", "goal") is None


def test_graph_rejects_missing_start_zone():
    zones = {
        "middle": Zone(role="hub", name="middle", x=1, y=0),
        "goal": Zone(role="end_hub", name="goal", x=2, y=0),
    }

    with pytest.raises(ValueError, match="exactly one start zone"):
        Graph(make_config(zones=zones))


def test_graph_rejects_missing_end_zone():
    zones = {
        "start": Zone(role="start_hub", name="start", x=0, y=0),
        "middle": Zone(role="hub", name="middle", x=1, y=0),
    }

    with pytest.raises(ValueError, match="exactly one end zone"):
        Graph(make_config(zones=zones))


@pytest.mark.parametrize("role", ["start_hub", "end_hub"])
def test_graph_rejects_blocked_start_or_end(role):
    zones = {
        "start": Zone(
            role="start_hub",
            name="start",
            x=0,
            y=0,
            zone_type="blocked" if role == "start_hub" else "normal",
        ),
        "goal": Zone(
            role="end_hub",
            name="goal",
            x=2,
            y=0,
            zone_type="blocked" if role == "end_hub" else "normal",
        ),
    }

    with pytest.raises(ValueError, match="cannot be blocked"):
        Graph(make_config(zones=zones, connections=[]))


def test_graph_rejects_self_connection():
    connection = Connection(z1="start", z2="start")

    with pytest.raises(ValueError, match="Self-connections"):
        Graph(make_config(connections=[connection]))


def test_graph_rejects_unknown_connection_zone():
    connection = Connection(z1="start", z2="missing")

    with pytest.raises(ValueError, match="Unknown zone"):
        Graph(make_config(connections=[connection]))


def test_graph_rejects_duplicate_connection_in_reverse_order():
    connections = [
        Connection(z1="start", z2="middle"),
        Connection(z1="middle", z2="start"),
    ]

    with pytest.raises(ValueError, match="Duplicate connection"):
        Graph(make_config(connections=connections))


def test_graph_rejects_unknown_zone_queries():
    graph = Graph(make_config())

    with pytest.raises(KeyError, match="Unknown zone"):
        graph.neighbors("missing")

    with pytest.raises(KeyError):
        graph.edges("missing")
