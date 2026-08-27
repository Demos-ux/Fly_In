import re
import pydantic


class DroneConfig(pydantic.BaseModel):
    nb_drones: int = pydantic.Field(
        gt=0, description="Must be a positive integer")


class Parser():
    def __init__(self, file_path):
        self.file_path = file_path

    class ParseError(Exception):
        pass

    def parse(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            for index, item in enumerate(content.splitlines(), start=1):
                if item.strip():
                    match = re.match(r'^\s*nb_drones\s*:\s*(.+)\s*$', item)
                    if match:
                        if match.group(1).strip().isdigit():
                            self.nb_drones = int(match.group(1).strip())
                        else:
                            raise self.ParseError(
                                f"Invalid value for nb_drones at line "
                                f"{index}: {match.group(1).strip()}")
