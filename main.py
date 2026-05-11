from parser import ConfigParser
from display import display
from hub import Hub
from Pathfinder import PathFinder


if __name__ == "__main__":
    data = ConfigParser('file.txt', {})
    graph = data.get_hubs_as_graph()
    i = 0
    new_graph = []
    for lst in graph:
        adj = []
        for hub in lst:
            adj.append(hub.name if isinstance(hub, Hub) else hub)
        new_graph.append(adj)
    adjacency = data.build_adjacency(new_graph)
    hubs = data.parse()['hubs']
    connections = data.parse()['connections']
    objects = data.get_objects()
    path_finder = PathFinder(adjacency, hubs)
    path = path_finder.astar(objects[0], objects[1])
    display = display(hubs, connections, path)
    display.display_hubs()
