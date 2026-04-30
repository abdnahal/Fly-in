from typing import Dict
import sys
import re


class ConfigParser:
    def __init__(self, path: str, data: Dict[str, dict]):
        self.config = path
        self.data = data if data else {}
        self.parse()

    def _parse_metadata(self, text: str) -> Dict[str, object]:
        metadata: Dict[str, object] = {}
        match = re.search(r"\[(.*?)\]", text)
        if not match:
            return metadata

        for key, value in re.findall(
            r"([A-Za-z_][A-Za-z0-9_]*)=([^\s\]]+)", match.group(1)
        ):
            metadata[key] = int(value) if value.isdigit() else value
        return metadata

    def parse(self) -> Dict[str, dict]:
        try:
            with open(self.config, "r") as f:
                self.data["hubs"] = {}
                self.data["connections"] = {}
                for line in f:
                    if not line.strip() or line.startswith("#"):
                        continue
                    else:
                        parts = line.split(":", maxsplit=1)
                        if len(parts) != 2:
                            raise ValueError(f"Invalid format: {line}")
                        if parts[0].lower() != "connection":
                            data = parts[1].strip().split(maxsplit=3)
                            if len(data) < 3:
                                raise ValueError(f"Invalid hub format: {line}")

                            hub_name = data[0]
                            self.data["hubs"][hub_name] = {
                                "coord": (int(data[1]), int(data[2]))
                            }
                            metadata = self._parse_metadata(parts[1])
                            if metadata:
                                self.data["hubs"][hub_name]["metadata"] = metadata

                        else:
                            data = parts[1].strip().split(maxsplit=1)
                            if not data:
                                raise ValueError(f"Invalid connection format: {line}")

                            conn_name = data[0]
                            self.data["connections"][conn_name] = {}
                            metadata = self._parse_metadata(parts[1])
                            if metadata:
                                self.data["connections"][conn_name][
                                    "metadata"
                                ] = metadata
        except ValueError as e:
            print(e)
            sys.exit(1)
        print(self.data)


{
    "hubs": {
        "hub": {"coord": (0, 0), "metadata": {"color": "green"}},
        "goal": {"coord": (10, 10), "metadata": {"color": "yellow"}},
        "roof1": {"coord": (3, 4), "metadata": {"zone": "restricted", "color": "red"}},
        "roof2": {"coord": (6, 2), "metadata": {"zone": "normal", "color": "blue"}},
        "corridorA": {
            "coord": (4, 3),
            "metadata": {"zone": "priority", "color": "green", "max_drones": 2},
        },
        "tunnelB": {"coord": (7, 4), "metadata": {"zone": "normal", "color": "red"}},
        "obstacleX": {
            "coord": (5, 5),
            "metadata": {"zone": "blocked", "color": "gray"},
        },
    },
    "connections": {
        "hub-roof1": {},
        "hub-corridorA": {},
        "roof1-roof2": {},
        "roof2-goal": {},
        "corridorA-tunnelB": {"metadata": {"max_link_capacity": 2}},
        "tunnelB-goal": {},
    },
}
