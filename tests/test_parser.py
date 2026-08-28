import pytest
from route_parser import Parser, ParseError

# Hilfsfunktion, um schnell Testdateien zu generieren
def create_map(tmp_path, content: str):
    file_path = tmp_path / "test_map.txt"
    file_path.write_text(content)
    return str(file_path)

# --- 1. POSITIV-TESTS (Was funktionieren MUSS) ---

def test_valid_basic_map(tmp_path):
    content = """
    # This is a valid map
    nb_drones: 5
    
    start_hub: start_zone 0 0 [color=blue max_drones=10]
    hub: mid_zone 5 5 [zone=restricted]
    end_hub: end_zone 10 10 [color=red]
    
    connection: start_zone-mid_zone [max_link_capacity=2]
    connection: mid_zone-end_zone
    """
    parser = Parser(create_map(tmp_path, content))
    config = parser.parse()
    
    assert config.nb_drones == 5
    assert len(config.zones) == 3
    assert len(config.connections) == 2
    assert config.zones["start_zone"].max_drones == 10
    assert config.zones["mid_zone"].zone_type == "restricted"

# --- 2. DROHNEN- & HEADER-EDGE CASES ---

def test_missing_nb_drones(tmp_path):
    content = """
    start_hub: start 0 0
    end_hub: end 10 10
    """
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="First uncommented line must define 'nb_drones: <int>'"):
        parser.parse()

def test_invalid_nb_drones_value(tmp_path):
    content = "nb_drones: -5\nstart_hub: s 0 0\nend_hub: e 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="nb_drones must be positive"):
        parser.parse()

# --- 3. HUB- & ZONEN-EDGE CASES ---

def test_missing_start_hub(tmp_path):
    content = "nb_drones: 1\nhub: mid 0 0\nend_hub: end 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Expected exactly 1 start_hub"):
        parser.parse()

def test_multiple_start_hubs(tmp_path):
    content = "nb_drones: 1\nstart_hub: s1 0 0\nstart_hub: s2 1 1\nend_hub: e 2 2"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Expected exactly 1 start_hub"):
        parser.parse()

def test_invalid_zone_name_dash(tmp_path):
    content = "nb_drones: 1\nstart_hub: invalid-name 0 0\nend_hub: e 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="contains invalid character '-'"):
        parser.parse()

def test_duplicate_zone_name(tmp_path):
    content = "nb_drones: 1\nstart_hub: zone1 0 0\nhub: zone1 1 1\nend_hub: e 2 2"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Duplicate zone 'zone1'"):
        parser.parse()

def test_invalid_zone_type(tmp_path):
    content = "nb_drones: 1\nstart_hub: s 0 0 [zone=magical]\nend_hub: e 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Invalid zone type 'magical'"):
        parser.parse()

# --- 4. VERBINDUNGS-EDGE CASES ---

def test_connection_undefined_zones(tmp_path):
    content = """
    nb_drones: 1
    start_hub: s 0 0
    end_hub: e 1 1
    connection: s-ghost_zone
    """
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Connection uses undefined zones"):
        parser.parse()

def test_duplicate_connections_reversed(tmp_path):
    content = """
    nb_drones: 1
    start_hub: a 0 0
    end_hub: b 1 1
    connection: a-b
    connection: b-a
    """
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Duplicate connection"):
        parser.parse()

# --- 5. METADATEN- & SYNTAX-EDGE CASES ---

def test_invalid_metadata_syntax(tmp_path):
    content = "nb_drones: 1\nstart_hub: s 0 0 [color red]\nend_hub: e 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Invalid metadata syntax 'color'"):
        parser.parse()

def test_invalid_general_syntax(tmp_path):
    content = "nb_drones: 1\nstart_hub: s 0 0\njust some random garbage\nend_hub: e 1 1"
    parser = Parser(create_map(tmp_path, content))
    with pytest.raises(ParseError, match="Invalid syntax -> 'just some random garbage'"):
        parser.parse()