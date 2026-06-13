from typing import Dict, Any


class Hub:
    def __init__(self, name: str, hub: Dict[str, Any]):
        self.hub = hub
        self.name = name
        self.coord = hub['coord']
        self.metadata = hub.get('metadata', {})
        if name == 'start' or name == 'goal':
            self.cost = 0
        elif 'zone' in self.metadata.keys():
            if self.metadata['zone'] == 'blocked':
                self.cost = float('inf')
            elif self.metadata['zone'] == 'primary':
                self.cost = 0.9
            else:
                self.cost = 2 if self.metadata['zone'] == 'restricted' else 1
        else:
            self.cost = 1
        if self.metadata.get('color'):
            self.color = self.metadata['color']
        else:
            self.color = 'White'
