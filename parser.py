from typing import Dict, List
import sys


class ConfigParser():
    def __init__(self, path: str, data: Dict[str, dict]):
        self.config = path
        self.data = {}
        self.parse()

    def parse(self) -> Dict[str, dict]:
        try:
            with open(self.config, 'r') as f:
                self.data['hubs'] = {}
                self.data['connections'] = {}
                for line in f:
                    if not line.strip() or line.startswith('#'):
                        continue
                    else:
                        parts = line.split(':')
                        if len(parts) != 2:
                            raise ValueError(f"Invalid format: {line}")
                        if parts[0].lower() != 'connection':
                            data = parts[1].split(maxsplit=3)
                            self.data['hubs'][data[0]] = {}
                            self.data['hubs'][data[0]]['coord'] = (int(data[1]), int(data[2]))
                            self.data['hubs'][data[0]]['metadata'] = data[3]
                        else:
                            data = parts[1].split()
                            self.data['connections'][data[0]] = {}
                            if len(data) == 2:
                                self.data['connections'][data[0]]['metadata'] = data[1]
        except ValueError as e:
            print(e)
            sys.exit(1)
        print(self.data['hubs'])
