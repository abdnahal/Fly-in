from parser import ConfigParser
from display import display
# from hub import Hub
from Pathfinder import PathFinder
from drone import Drone


if __name__ == "__main__":
    data = ConfigParser("file.txt", {})
    adjacency = data.build_adjacency()
    hubs = data.parse()["hubs"]
    connections = data.get_connections()
    path_finder = PathFinder(adjacency, hubs, data.data['nb_drones'])
    path = path_finder.get_paths(data.data['hubs']['start'],
                                 data.data['hubs']['goal'])
    drones = [Drone(i, path) for i in range(data.data['nb_drones'])]
    displayer = display(hubs, connections, drones, path)
    displayer._display()

# {
#     "hub": [("roof1", inf), ("corridorA", inf)],
#     "roof1": [("hub", inf), ("roof2", inf)],
#     "corridorA": [("hub", inf), ("tunnelB", 2)],
#     "roof2": [("roof1", inf), ("goal", inf)],
#     "goal": [("roof2", inf), ("tunnelB", inf)],
#     "tunnelB": [("corridorA", 2), ("goal", inf)],
# }
