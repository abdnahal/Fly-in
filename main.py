from parser import ConfigParser
from display import display
from hub import Hub
from Pathfinder import PathFinder


if __name__ == "__main__":
    data = ConfigParser('file.txt', {})
    display = display(data.parse()['hubs'], data.parse()['connections'])
    graph = data.get_hubs_as_graph()
    i = 0
    new_graph = []
    for lst in graph:
        adj = []
        for hub in lst:
            adj.append(hub.name if isinstance(hub, Hub) else hub)
        new_graph.append(adj)
    adjacency = data.build_adjacency(new_graph)
    print(adjacency)
    path = PathFinder(adjacency).astar()
    display.display_hubs()

