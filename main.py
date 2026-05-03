from parser import ConfigParser
from display import display
from collections import defaultdict

if __name__ == "__main__":
    data = ConfigParser('file.txt', {})
    display = display(data.parse()['hubs'], data.parse()['connections'])
    graph = data.get_hubs_as_graph()
    print(graph)
    print(defaultdict(graph))
    display.display_hubs()

