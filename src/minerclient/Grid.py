import heapq


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class Grid:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.walls = []
        self.weights = {}

    def in_range(self, pos):
        (row, col) = pos
        return 0 <= row <= self.grid_size and 0 <= col <= self.grid_size

    def walkable(self, pos):
        return pos not in self.walls

    def neighbors(self, pos):
        (row, col) = pos
        results = [ (row+1, col), (row-1, col), (row, col+1), (row, col-1)]
        if (row + col) % 2 == 0:
            results.reverse()

        results = filter(self.in_range, results)
        results = filter(self.walkable, results)
        return results

    def cost(self, from_node, to_node):
        return self.weights.get(to_node, 1)


def dijkstra_search(grid, start_pos, end_pos):
    frontier = PriorityQueue()
    frontier.put(start_pos, 0)

    came_from = {start_pos: None}
    cost_so_far = {start_pos: 0}

    while not frontier.empty():
        current = frontier.get()

        if current == end_pos:
            break

        for next in grid.neighbors(current):
            new_cost = cost_so_far[current] + grid.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far


def reconstruct_path(came_from, start_pos, end_pos):
    current = end_pos
    path = [current]

    while current != start_pos:
        current = came_from[current]
        path.append(current)

    path.append(start_pos)
    path.reverse()

    fixed_path = []

    for coord in path:
        if len(fixed_path) == 0:
            fixed_path.append(coord)
        else:
            if fixed_path[-1] != coord:
                fixed_path.append(coord)

    return fixed_path