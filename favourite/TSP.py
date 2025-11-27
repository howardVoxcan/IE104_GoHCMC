import requests
import itertools 

class Graph:
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.edges = [[0] * num_vertices for _ in range(num_vertices)]

    def add_edge(self, u, v, weight):
        self.edges[u][v] = weight

    def find_hamiltonian_path(self, fixed_position=None, precedence_constraints=None, start=None, end=None):
        vertices = list(range(self.num_vertices))
        min_path = None
        min_cost = float("inf")

        if fixed_position is None:
            fixed_position = [False] * (self.num_vertices + 1)
        if precedence_constraints is None:
            precedence_constraints = []

        fixed_position_map = {i: None for i, fixed in enumerate(fixed_position) if fixed}

        inner_vertices = vertices.copy()
        if start is not None:
            inner_vertices.remove(start)
        if end is not None and end in inner_vertices:
            inner_vertices.remove(end)

        for perm in itertools.permutations(inner_vertices):
            path = list(perm)

            # Thêm start và end
            if start is not None:
                path.insert(0, start)
            else:
                path.insert(0, 0)

            if end is not None:
                path.append(end)
            else:
                path.append(path[0])

            # ===== CHECK fixed_position =====
            valid = True
            for idx in fixed_position_map:
                if idx >= len(path):
                    valid = False
                    break
                if fixed_position_map[idx] is not None and path[idx] != fixed_position_map[idx]:
                    valid = False
                    break

            if not valid:
                continue

            # ===== CHECK precedence_constraints =====
            for u, v in precedence_constraints:
                try:
                    if path.index(u) >= path.index(v):
                        valid = False
                        break
                except ValueError:
                    valid = False
                    break

            if not valid:
                continue

            # ===== Chỉ tính cost nếu valid =====
            cost = 0
            for i in range(len(path) - 1):
                cost += self.edges[path[i]][path[i+1]]

            if cost < min_cost:
                min_cost = cost
                min_path = path

        return min_path, min_cost

def distance(origins, destinations):
    api_key = "w6YHI8MoaxcNVp4wPBP7WbanJ5KI6EEx3QtIFtV1Y0VBOWLMc85ZL399y9FUVqHk"
    url = "https://api-v2.distancematrix.ai/maps/api/distancematrix/json"

    params = {
        "origins": origins,
        "destinations": destinations,
        "key": api_key
    }

    response = requests.get(url, params=params)
    
    result = response.json()
    distance = result["rows"][0]["elements"][0]["distance"]["value"]
    duration = result["rows"][0]["elements"][0]["duration"]["value"]
    return distance, duration
