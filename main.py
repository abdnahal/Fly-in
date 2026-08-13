try:
    import sys
    from parser import ConfigParser
    from display import display

    # from hub import Hub
    from Pathfinder import PathFinder
    from drone import Drone
    from allocator import Allocator
    from simulator import Simulator
except (KeyboardInterrupt, ImportError):
    print("\n\nStop interrupting my imports :(\n\n")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print(f"Usage: python3 {sys.argv[0]} <map_file>")
            sys.exit(1)

        filename = sys.argv[1]
        data = ConfigParser(filename, {})
        adjacency = data.build_adjacency()
        hubs = data.data["hubs"]
        connections = data.get_connections()
        path_finder = PathFinder(adjacency, hubs, data.data["nb_drones"])
        start = [hub for hub in data.data['hubs'].values() if hub.start]
        end = [hub for hub in data.data['hubs'].values() if hub.end]
        paths = path_finder.get_paths(start[0], end[0])
        if len(paths) == 0:
            print("No path found!")
            sys.exit(1)

        # Distribute drones over the paths for the fewest simulation turns.
        allocator = Allocator(hubs, connections, paths, data.data["nb_drones"])
        assignment = allocator.allocate()
        drones = [
            Drone(i, paths, assigned=assignment[i])
            for i in range(data.data["nb_drones"])
        ]

        sim = Simulator(hubs, connections, drones)
        turns = sim.calculate_turns()          # builds sim.schedule FIRST

        displayer = display(hubs, connections, drones, paths, sim)
        displayer._display()

        for line in sim.schedule:
            print(line)
        print(f"Simulation turns: {turns}")
    except KeyboardInterrupt:
        print("\nStop interrupting me :(\n")
# {
#     "hub": [("roof1", inf), ("corridorA", inf)],
#     "roof1": [("hub", inf), ("roof2", inf)],
#     "corridorA": [("hub", inf), ("tunnelB", 2)],
#     "roof2": [("roof1", inf), ("goal", inf)],
#     "goal": [("roof2", inf), ("tunnelB", inf)],
#     "tunnelB": [("corridorA", 2), ("goal", inf)],
# }
