from typing import Dict, List, Tuple


class Hub:
    def __init__(self, hub: Dict[str, Dict]):
        self.hub = hub
        self.coord = hub['coord']
        if 'zone' in hub['metadata'].keys():
            if hub['metadata']['zone'] == 'blocked':
                self.cost = -float('inf')
            else:
                self.cost = 2 if hub['metadata']['zone'] == 'restricted' else 1
        if hub['metadata']['color']:
            self.color = hub['metadata']['color']
        else:
            self.color = None