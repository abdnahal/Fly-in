from typing import Dict, Any


class Hub:
    def __init__(self, name: str, hub: Dict[str, Any]):
        self.hub = hub
        self.name = name
        self.coord = hub['coord']
        metadata = hub.get('metadata', {})
        if 'zone' in metadata.keys():
            if metadata['zone'] == 'blocked':
                self.cost = float('inf')
            elif metadata['zone'] == 'primary':
                self.cost = 0.9
            else:
                self.cost = 2 if metadata['zone'] == 'restricted' else 1
        else:
            self.cost = 1
        if metadata.get('color'):
            self.color = metadata['color']
        else:
            self.color = None
