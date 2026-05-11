from typing import Dict
from hub import Hub
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
                for i, line in enumerate(f):
                    if not line.strip() or line.startswith("#"):
                        continue
                    else:
                        parts = line.split(":", maxsplit=1)
                        if len(parts) != 2:
                            raise ValueError(f"Invalid format: {line}")
                        if i == 0:
                            self.data[parts[0]] = int(parts[1])
                            continue
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
                                self.data["hubs"][hub_name
                                                  ]["metadata"] = metadata

                        else:
                            data = parts[1].strip().split(maxsplit=1)
                            if not data:
                                raise ValueError(f"Invalid connection\
                                                 format: {line}")

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
        return self.data

    def get_hubs_as_graph(self):
        graph = []
        for key in self.data["connections"].keys():
            parts = key.split("-")
            if "metadata" in self.data["connections"][key].keys():
                graph.append(
                    [
                        Hub(parts[0], self.data["hubs"][parts[0]]),
                        Hub(parts[1], self.data["hubs"][parts[1]]),
                        self.data["connections"][
                            key]["metadata"]["max_link_capacity"],
                    ]
                )
            else:
                graph.append(
                    [
                        Hub(parts[0], self.data["hubs"][parts[0]]),
                        Hub(parts[1], self.data["hubs"][parts[1]]),
                    ]
                )
        return graph

    @staticmethod
    def build_adjacency(connections: list[list]) -> dict[
                            str, list[tuple[str, int]]]:

        adjacency: dict[str, list[tuple[str, int]]] = {}

        for connection in connections:
            zone_a: str = connection[0]
            zone_b: str = connection[1]
            capacity: int = connection[2] if len(connection) == 3 else 1
            if zone_a in adjacency.keys():
                adjacency[zone_a].append((zone_b, capacity))
            else:
                adjacency[zone_a] = [(zone_b, capacity)]
            if zone_b in adjacency.keys():
                adjacency[zone_b].append((zone_a, capacity))
            else:
                adjacency[zone_b] = [(zone_a, capacity)]

        return adjacency

    def get_objects(self):
        objects = []
        for key, value in self.data['hubs'].items():
            objects.append(Hub(key, value))
        return objects
