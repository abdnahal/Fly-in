from typing import Dict, Tuple
from .hub import Hub
import sys


class ConfigParser:
    def __init__(self, path: str, data: Dict[str, dict]):
        self.config = path
        self.data = data if data else {}
        self.parse()

    def _parse_metadata(self, text: str) -> Dict[str, object]:
        metadata: Dict[str, object] = {}
        parts = text.strip("[]").split()
        for part in parts:
            key, value = part.split("=")
            metadata[key] = int(value) if value.isdigit() else value
        return metadata

    def parse(self) -> Dict[str, dict]:
        try:
            with open(self.config, "r") as f:
                self.data["hubs"] = {}
                self.data["connections"] = {}
                counter = 0
                for line in f:
                    if not line.strip() or line.startswith("#"):
                        continue
                    else:
                        parts = line.split(":", maxsplit=1)
                        if len(parts) != 2:
                            raise ValueError(f"Invalid format: {line}")
                        if counter == 0:
                            if parts[0] != "nb_drones" or len(parts) != 2:
                                raise ValueError(
                                    "First line must be: \
nb_drones: <positive_integer>"
                                )
                            self.data[parts[0]] = int(parts[1])
                            counter += 1
                            continue
                        if parts[0].lower() != "connection":
                            data = parts[1].strip().split(maxsplit=3)
                            if len(data) < 3:
                                raise ValueError(f"Invalid hub format: {line}")

                            hub_name = data[0]
                            if len(data) == 4:
                                metadata = self._parse_metadata(data[3])
                                self.data["hubs"][hub_name] = Hub(
                                    hub_name,
                                    {
                                        "coord": (int(data[1]), int(data[2])),
                                        "metadata": metadata,
                                    },
                                    True if parts[0].lower() == "start_hub"
                                    else False,
                                    True if parts[0].lower() == "end_hub"
                                    else False,
                                )
                            else:
                                self.data["hubs"][hub_name] = Hub(
                                    hub_name,
                                    {"coord": (int(data[1]), int(data[2]))},
                                    True if parts[0].lower() == "start_hub"
                                    else False,
                                    True if parts[0].lower() == "end_hub"
                                    else False,
                                )
                        else:
                            data = parts[1].strip().split(maxsplit=1)
                            if not data:
                                raise ValueError(
                                    f"Invalid connection\
                                                 format: {line}"
                                )

                            conn_name = data[0]
                            self.data["connections"][conn_name] = {}
                            if len(data) == 2:
                                metadata = self._parse_metadata(data[1])
                                self.data["connections"][conn_name][
                                    "metadata"
                                ] = metadata
                        counter += 1
        except ValueError as e:
            print(e)
            sys.exit(1)
        self.validate()
        return self.data

    def validate(self) -> None:
        try:
            for hub in self.data['hubs'].values():
                if hub.metadata:
                    if 'max_drones' in hub.metadata.keys():
                        if hub.metadata['max_drones'] <= 0:
                            e = "max_drones should be a positive integer"
                            raise ValueError(e)
            start = sum([1 for hub in self.data['hubs'].values() if hub.start])
            if start != 1:
                raise ValueError("One start_hub needed!")
            end = sum([1 for hub in self.data['hubs'].values() if hub.end])
            if end != 1:
                raise ValueError("One end_hub needed!")
            if self.data["nb_drones"] <= 0:
                raise ValueError("Number of drones can't be negative!")
            for hub in self.data["hubs"].keys():
                if "-" in hub:
                    raise ValueError(f"Invalid hub name: {hub}")
            err = "Invalid connection: "
            for conn in self.data["connections"].keys():
                tmp = conn.split("-")
                if tmp[0] not in self.data["hubs"].keys():
                    raise ValueError(f"{err}{conn}")
                elif tmp[1] not in self.data["hubs"].keys():
                    raise ValueError(f"{err}{conn}")
                if f"{tmp[1]}-{tmp[0]}" in self.data["connections"].keys():
                    e = "The same connection cannot appear more than once"
                    raise ValueError(e)
            zones = ["normal", "blocked", "restricted", "priority"]
            for value in self.data["hubs"].values():
                if "zone" in value.metadata.keys():
                    if value.metadata["zone"] not in zones:
                        raise ValueError(
                            "Zone types must be one of: normal, blocked, \
    restricted, priority"
                        )
        except ValueError as e:
            print(e)
            sys.exit(1)

    def build_adjacency(self) -> Dict[str, Tuple[str, int]]:
        adjacency: dict[str, list[tuple[str, int]]] = {}

        for connection in self.data["connections"].keys():
            parts = connection.split("-")
            zone_a: str = parts[0]
            zone_b: str = parts[1]
            if "metadata" in self.data["connections"][connection].keys():
                tmp = self.data["connections"][connection]
                capacity: int = tmp["metadata"]["max_link_capacity"]
            else:
                capacity = float("inf")
            if zone_a in adjacency.keys():
                adjacency[zone_a].append((zone_b, capacity))
            else:
                adjacency[zone_a] = [(zone_b, capacity)]
            if zone_b in adjacency.keys():
                adjacency[zone_b].append((zone_a, capacity))
            else:
                adjacency[zone_b] = [(zone_a, capacity)]

        return adjacency

    def get_connections(self) -> Dict[str, int]:
        connections = {}
        for key, value in self.data["connections"].items():
            if "metadata" in value:
                cap = value["metadata"]["max_link_capacity"]
            else:
                cap = float("inf")
            connections[key] = (cap, 0)
        return connections
