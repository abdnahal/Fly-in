from typing import Dict, List


class ConfigParser():
    def __init__(self, path: str, data: Dict[str, dict]):
        self.config = path
        self.data = {}
        self.parse()
    
    def parse(self) -> Dict[str, dict]:
        try:
            with open(self.config, 'r') as f:
                for line in f:
                    if not line.strip() or line.startswith('#'):
                        continue
                    else:
                        parts = line.split(':')
                        if len(parts) > 2:
                            raise ValueError(f"Invalid format: {line}")
