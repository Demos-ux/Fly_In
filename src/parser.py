import re
import pydantic


class RouteConfig(pydantic.BaseModel):
    nb_drones: int = pydantic.Field(
        gt=0, description="Must be a positive integer")
    waypoints: list[Waypoint] = pydantic.Field(
        default_factory=list
    )
    connections:list[str] = pydantic.Field(
        default_factory=list
    )

class Waypoint(pydantic.BaseModel):
    role: str
    name: str
    x: str
    y: str
    color: str


class Parser():
    def __init__(self, file_path):
        self.file_path = file_path


    def parse(self) -> RouteConfig:

        raw_data = {
            "waypoints":[],
            "connections": []
            }
        with open(self.file_path, 'r') as file:
            for index, line in enumerate(file, start=1):
                line = line.strip():
                if not line:
                    continue
                match_drones = re.match(r'^\s*nb_drones\s*:\s*(.+)\s*$', item)
                if match_drones:
                    if match_drones:
                        raw_data["nb_drones"].append(match_drones.group(1).strip())
                        continue
                match_hub = re.match(r'^(start_hub|hub|end_hub)\s*:\s*([a-zA-Z0-9_]+)\s+(\d+)\s+(\d+)\s+\[color=([^\]]+)\]', line)
                if match_hub:
                    raw_data["waypoints"].append({
                        "role": match_hub.group(1),
                        "name": match_hub.group(2),
                        "x": match_hub.group(3),
                        "y": match_hub.group(4),
                        "color": match_hub.group(5)
                    })
                    continue 
                match_conn = re.match(r'^connection\s*:\s*(.+)$',line)
                if match_conn:
                    raw_data["connections"].append(match_conn.group(1).strip())
                    continue

                try:
                    return(RouteConfig.model_validation(raw_data))
                except pydantic.ValidationError as e:
                    print(f"Fehler beim Validieren der Datei {self.file_path}:")
                    print(e)
                    raise