import pytest

from fly_in.parser import parse_map


def test_parse_simple_map() -> None:
    content = """
    nb_drones: 2
    start_hub: start 0 0 [color=green]
    end_hub: end 2 2 [color=yellow]
    hub: mid 1 1 [zone=priority max_drones=2]
    connection: start-mid
    connection: mid-end
    """

    graph = parse_map(content)

    assert graph.nb_drones == 2
    assert graph.start_name == "start"
    assert graph.end_name == "end"
    assert graph.get_zone("mid").zone_type == "priority"
    assert graph.get_zone("mid").max_drones == 2
    assert "start" in graph.zones
    assert "end" in graph.zones


def test_invalid_zone_type_raises_error() -> None:
    content = """
    nb_drones: 1
    start_hub: start 0 0
    end_hub: end 2 2
    hub: bad 1 1 [zone=unknown]
    connection: start-bad
    connection: bad-end
    """

    with pytest.raises(ValueError, match="zone type"):
        parse_map(content)


def test_duplicate_connection_raises_error() -> None:
    content = """
    nb_drones: 1
    start_hub: start 0 0
    end_hub: end 2 2
    hub: a 1 1
    hub: b 2 2
    connection: start-a
    connection: a-start
    """

    with pytest.raises(ValueError, match="duplicate connection"):
        parse_map(content)
