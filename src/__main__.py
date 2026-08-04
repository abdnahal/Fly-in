import sys
from .parser import ConfigParser
from .display import display
# from hub import Hub
from .Pathfinder import PathFinder
from .drone import Drone
from .simulator import Simulator


if __name__ == "__main__":
    data = ConfigParser("file.txt", {})
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <map_file>")
        sys.exit(1)
    
    adjacency = data.build_adjacency()
    hubs = data.parse()["hubs"]
    connections = data.get_connections()
    path_finder = PathFinder(adjacency, hubs, data.data['nb_drones'])
    path = path_finder.get_paths(data.data['hubs']['start'],
                                 data.data['hubs']['impossible_goal'])
    if len(path) == 0:
        print("No path found!")
        sys.exit(1)
    drones = [Drone(i, path) for i in range(data.data['nb_drones'])]
    displayer = display(hubs, connections, drones, path)
    paths = path_finder.get_paths(hubs['start'],
                                  hubs['impossible_goal'])

    drones = [Drone(i, paths) for i in range(data.data['nb_drones'])]
    displayer = display(hubs, connections, drones, paths)
    displayer._display()
    print(Simulator(hubs, connections, drones).calculate_turns())

# {
#     "hub": [("roof1", inf), ("corridorA", inf)],
#     "roof1": [("hub", inf), ("roof2", inf)],
#     "corridorA": [("hub", inf), ("tunnelB", 2)],
#     "roof2": [("roof1", inf), ("goal", inf)],
#     "goal": [("roof2", inf), ("tunnelB", inf)],
#     "tunnelB": [("corridorA", 2), ("goal", inf)],
# }
