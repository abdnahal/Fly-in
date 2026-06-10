from typing import Dict, Tuple
from hub import Hub
import sys


class ConfigParser:
    def __init__(self, path: str, data: Dict[str, dict]):
        self.config = path
        self.data = data if data else {}
        self.parse()

    def _parse_metadata(self, text: str) -> Dict[str, object]:
        metadata: Dict[str, object] = {}
        parts = text.strip('[]').split()
        for part in parts:
            key, value = part.split('=')
            metadata[key] = int(value) if value.isdigit() else value
        return metadata

    def parse(self) -> Dict[str, dict]:
        try:
            with open(self.config, "r") as f:
                self.data["hubs"] = {}
                self.data["connections"] = {}
                for i, line in enumerate(f):
                    if not line.strip() or line.startswith("#"):
                        continue
                    else:
                        parts = line.split(":", maxsplit=1)
                        if len(parts) != 2:
                            raise ValueError(f"Invalid format: {line}")
                        if i == 0:
                            if parts[0] != 'nb_drones' or len(parts) != 2:
                                raise ValueError("First line must be: \
nb_drones: <positive_integer>")
                            self.data[parts[0]] = int(parts[1])
                            continue
                        if parts[0].lower() != "connection":
                            data = parts[1].strip().split(maxsplit=3)
                            if len(data) <= 3:
                                raise ValueError(f"Invalid hub format: {line}")

                            hub_name = data[0]
                            metadata = self._parse_metadata(data[3])
                            if metadata:
                                self.data['hubs'][
                                    hub_name] = Hub(hub_name,
                                                    {"coord": (int(data[1]),
                                                               int(data[2])),
                                                     "metadata": metadata})
                            else:
                                self.data['hubs'][
                                    hub_name] = Hub(hub_name,
                                                    {"coord": (int(data[1]),
                                                               int(data[2]))})

                        else:
                            data = parts[1].strip().split(maxsplit=1)
                            if not data:
                                raise ValueError(f"Invalid connection\
                                                 format: {line}")

                            conn_name = data[0]
                            self.data["connections"][conn_name] = {}
                            if len(data) == 2:
                                metadata = self._parse_metadata(data[1])
                                self.data["connections"][conn_name][
                                    "metadata"
                                ] = metadata
        except ValueError as e:
            print(e)
            sys.exit(1)
        self.validate()
        return self.data

    def validate(self) -> None:
        for hub in self.data['hubs'].keys():
            if '-' in hub:
                print(f"Invalid hub name: {hub}")
                sys.exit(1)
        err = "Invalid connection: "
        for conn in self.data['connections'].keys():
            tmp = conn.split('-')
            if tmp[0] not in self.data['hubs'].keys():
                print(f"{err}{conn}")
                sys.exit(1)
            elif tmp[1] not in self.data['hubs'].keys():
                print(f"{err}{conn}")
                sys.exit(1)
            if f"{tmp[1]}-{tmp[0]}" in self.data['connections'].keys():
                print("The same connection cannot appear more than once")
                sys.exit(1)
        zones = ["normal", "blocked", "restricted", "priority"]
        for value in self.data['hubs'].values():
            if 'zone' in value.metadata.keys():
                if value.metadata['zone'] not in zones:
                    print("Zone types must be one of: normal, blocked, \
restricted, priority")
                    sys.exit(1)

    def build_adjacency(self) -> Dict[
                            str, Tuple[str, int]]:

        adjacency: dict[str, list[tuple[str, int]]] = {}

        for connection in self.data['connections'].keys():
            parts = connection.split('-')
            zone_a: str = parts[0]
            zone_b: str = parts[1]
            if 'metadata' in self.data['connections'][connection].keys():
                tmp = self.data['connections'][connection]
                capacity: int = tmp['metadata']['max_link_capacity']
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
        for key, value in self.data['connections'].items():
            if 'metadata' in value:
                cap = value['metadata']['max_link_capacity']
            else:
                cap = float("inf")
            connections[key] = (cap, 0)
        return connections
