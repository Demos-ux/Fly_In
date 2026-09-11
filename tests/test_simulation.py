from graph import Graph
from objects import Connection, RouteConfig, Zone
from simulation import Simulation


def test_drones_move_without_colliding():
    config = RouteConfig(
        nb_drones=2,
        zones={
            "start": Zone(role="start_hub", name="start", x=0, y=0),
            "middle": Zone(
                role="hub",
                name="middle",
                x=1,
                y=0,
                max_drones=1,
            ),
            "goal": Zone(role="end_hub", name="goal", x=2, y=0),
        },
        connections=[
            Connection(z1="start", z2="middle"),
            Connection(z1="middle", z2="goal"),
        ],
    )

    output = Simulation(Graph(config)).run("start", "goal")

    assert output == [
        "D1-middle",
        "D1-goal D2-middle",
        "D2-goal",
    ]


def test_drone_uses_alternative_path_when_zone_is_full():
    config = RouteConfig(
        nb_drones=2,
        zones={
            "start": Zone(role="start_hub", name="start", x=0, y=0),
            "short": Zone(
                role="hub",
                name="short",
                x=1,
                y=0,
                max_drones=1,
            ),
            "long": Zone(
                role="hub",
                name="long",
                x=1,
                y=1,
                max_drones=1,
            ),
            "goal": Zone(role="end_hub", name="goal", x=2, y=0),
        },
        connections=[
            Connection(z1="start", z2="short"),
            Connection(z1="short", z2="goal"),
            Connection(z1="start", z2="long"),
            Connection(z1="long", z2="goal"),
        ],
    )

    output = Simulation(Graph(config)).run("start", "goal")

    assert output[0] == "D1-short D2-long"
    assert output[-2:] == ["D1-goal", "D2-goal"]


def test_restricted_arrival_consumes_the_turn():
    config = RouteConfig(
        nb_drones=1,
        zones={
            "start": Zone(role="start_hub", name="start", x=0, y=0),
            "restricted": Zone(
                role="hub",
                name="restricted",
                x=1,
                y=0,
                zone_type="restricted",
            ),
            "goal": Zone(role="end_hub", name="goal", x=2, y=0),
        },
        connections=[
            Connection(z1="start", z2="restricted"),
            Connection(z1="restricted", z2="goal"),
        ],
    )

    output = Simulation(Graph(config)).run("start", "goal")

    assert output == [
        "D1-start-restricted",
        "D1-restricted",
        "D1-goal",
    ]


def test_unlimited_zone_still_rejects_same_turn_collision():
    config = RouteConfig(
        nb_drones=2,
        zones={
            "start": Zone(role="start_hub", name="start", x=0, y=0),
            "middle": Zone(role="hub", name="middle", x=1, y=0),
            "goal": Zone(role="end_hub", name="goal", x=2, y=0),
        },
        connections=[
            Connection(z1="start", z2="middle"),
            Connection(z1="middle", z2="goal"),
        ],
    )

    output = Simulation(Graph(config)).run("start", "goal")

    assert output[0] == "D1-middle"
