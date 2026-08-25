from fly_in.engine import SimulationEngine
from fly_in.parser import parse_map_file
from fly_in.parser import parse_map


def test_easy_linear_map_simulation() -> None:
    graph = parse_map_file("maps/easy/01_linear_path.txt")
    sim = SimulationEngine(graph)
    result = sim.run()

    assert result["delivered"] == 2
    assert result["turns"] <= 5
    assert len(result["log"]) > 0


def test_simple_fork_map_simulation() -> None:
    graph = parse_map_file("maps/easy/02_simple_fork.txt")
    sim = SimulationEngine(graph)
    result = sim.run()

    assert result["delivered"] == 3
    assert result["turns"] <= 7
    assert all(turn for turn in result["log"])


def test_capacity_is_respected() -> None:
    graph = parse_map_file("maps/easy/03_basic_capacity.txt")
    sim = SimulationEngine(graph)
    result = sim.run()

    assert result["peak_occupancy"]["bottleneck"] <= 2
    assert result["peak_occupancy"]["wide_area"] <= 3


def test_restricted_zone_increases_turn_count() -> None:
    graph = parse_map_file("maps/medium/02_circular_loop.txt")
    sim = SimulationEngine(graph)
    result = sim.run()

    assert result["turns"] >= 4
    assert result["delivered"] == 6


def test_priority_puzzle_stays_within_tight_turn_budget() -> None:
    graph = parse_map_file("maps/medium/03_priority_puzzle.txt")
    sim = SimulationEngine(graph)
    result = sim.run()

    assert result["delivered"] == 4
    assert result["turns"] <= 12


def test_departure_frees_capacity_for_same_turn_entry() -> None:
    graph = parse_map(
        """
        nb_drones: 2
        start_hub: start 0 0 [max_drones=2]
        end_hub: goal 2 0 [max_drones=2]
        hub: middle 1 0 [max_drones=1]
        connection: start-middle
        connection: middle-goal
        """
    )
    sim = SimulationEngine(graph)
    sim.drones[1].current_zone = "middle"
    result = sim.run()

    assert result["delivered"] == 2
    assert result["turns"] == 2


def test_restricted_transit_reserves_destination_capacity() -> None:
    graph = parse_map(
        """
        nb_drones: 2
        start_hub: start 0 0 [max_drones=2]
        end_hub: goal 2 0 [max_drones=2]
        hub: tunnel 1 0 [zone=restricted max_drones=1]
        connection: start-tunnel [max_link_capacity=2]
        connection: tunnel-goal [max_link_capacity=2]
        """
    )
    result = SimulationEngine(graph).run()

    assert result["delivered"] == 2
    assert result["turns"] == 3


def test_opposing_moves_do_not_swap_on_one_connection() -> None:
    graph = parse_map(
        """
        nb_drones: 2
        start_hub: start 0 0 [max_drones=2]
        end_hub: goal 3 0 [max_drones=2]
        hub: left 1 0 [max_drones=1]
        hub: right 2 0 [max_drones=1]
        connection: start-left
        connection: left-right
        connection: right-goal
        """
    )
    sim = SimulationEngine(graph)
    sim.drones[1].current_zone = "right"
    sim.drones[2].current_zone = "left"
    result = sim.run()

    assert result["delivered"] == 2
    assert all(
        not ("D1-left" in turn and "D2-right" in turn)
        for turn in result["log"]
    )


def test_challenger_pathfinding_improves_baseline() -> None:
    graph = parse_map_file("maps/challenger/01_the_impossible_dream.txt")
    result = SimulationEngine(graph).run()

    assert result["delivered"] == 25
    assert result["turns"] <= 45
