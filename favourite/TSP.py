from itertools import permutations

import requests


def _check_fixed_positions(perm, fixed_position):
    """Check if permutation satisfies fixed position constraints"""
    return all(
        node is None or perm[pos] == node
        for pos, node in enumerate(fixed_position)
    )


def _check_start_end(perm, start, end):
    """Check if permutation satisfies start/end constraints"""
    if start is not None and perm[0] != start:
        return False
    if end is not None and perm[-1] != end:
        return False
    return True


def _check_precedence(perm, precedence_constraints):
    """Check if permutation satisfies precedence constraints"""
    pos_map = {node: idx for idx, node in enumerate(perm)}
    return all(
        pos_map[before] < pos_map[after]
        for before, after in precedence_constraints
    )


def is_valid_permutation(perm, fixed_position, precedence_constraints, start, end):
    """Validate all constraints for a permutation"""
    return (
            _check_fixed_positions(perm, fixed_position) and
            _check_start_end(perm, start, end) and
            _check_precedence(perm, precedence_constraints)
    )


def _build_candidate_path(fixed_position, perm_free):
    """Build candidate path from fixed positions and free nodes"""
    candidate = []
    free_idx = 0

    for node in fixed_position:
        if node is None:
            candidate.append(perm_free[free_idx])
            free_idx += 1
        else:
            candidate.append(node)

    return candidate


def _get_free_nodes(vertices, fixed_position, start, end):
    """Get list of nodes that can be freely permuted"""
    excluded = set(fixed_position) | {start, end}
    return [i for i in vertices if i not in excluded]


def _reconstruct_path(dp, nodes, start_node, end_node, best_last):
    """Reconstruct optimal path from DP table"""
    n = len(nodes)
    full_mask = (1 << n) - 1
    path = [end_node]
    mask = full_mask
    current = best_last

    while mask:
        path.append(nodes[current])
        prev_mask = mask ^ (1 << current)
        if prev_mask == 0:
            break
        current = dp[(mask, current)][1]
        mask = prev_mask

    path.append(start_node)
    path.reverse()
    return path


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.adjacency_matrix = [[0 for _ in range(vertices)] for _ in range(vertices)]

    def add_edge(self, u, v, w):
        self.adjacency_matrix[u][v] = w

    def _calculate_path_cost(self, path):
        """Calculate total cost of a path"""
        return sum(self.adjacency_matrix[path[i]][path[i + 1]] for i in range(self.V - 1))

    def _initialize_base_cases(self, start_node, nodes):
        """Initialize DP table with base cases"""
        dp = {}
        for i, node in enumerate(nodes):
            mask = 1 << i
            dp[(mask, i)] = (self.adjacency_matrix[start_node][node], start_node)
        return dp

    def _update_dp_state(self, dp, mask, last, nodes, n):
        """Update DP state for given mask and last node"""
        prev_mask = mask ^ (1 << last)
        if prev_mask == 0:
            return

        min_cost = float('inf')
        best_prev = None

        for prev in range(n):
            if not (prev_mask & (1 << prev)):
                continue
            if (prev_mask, prev) not in dp:
                continue

            cost = dp[(prev_mask, prev)][0] + self.adjacency_matrix[nodes[prev]][nodes[last]]
            if cost < min_cost:
                min_cost = cost
                best_prev = prev

        if best_prev is not None:
            dp[(mask, last)] = (min_cost, best_prev)

    def _fill_dp_table(self, dp, nodes, n):
        """Fill DP table for all masks"""
        for mask in range(1, 1 << n):
            for last in range(n):
                if not (mask & (1 << last)):
                    continue
                self._update_dp_state(dp, mask, last, nodes, n)

    def _find_optimal_last_node(self, dp, nodes, end_node, n):
        """Find the optimal last node and minimum cost"""
        full_mask = (1 << n) - 1
        min_total = float('inf')
        best_last = None

        for last in range(n):
            if (full_mask, last) not in dp:
                continue
            cost = dp[(full_mask, last)][0] + self.adjacency_matrix[nodes[last]][end_node]
            if cost < min_total:
                min_total = cost
                best_last = last

        return min_total, best_last

    def _held_karp(self, start_node, end_node, nodes):
        """
        Held-Karp algorithm for TSP path problem.
        Returns (min_cost, path) or (None, None) if no solution.
        """
        n = len(nodes)
        if n == 0:
            cost = 0 if start_node == end_node else self.adjacency_matrix[start_node][end_node]
            return cost, [start_node, end_node]

        dp = self._initialize_base_cases(start_node, nodes)
        self._fill_dp_table(dp, nodes, n)
        min_total, best_last = self._find_optimal_last_node(dp, nodes, end_node, n)

        if best_last is None:
            return None, None

        path = _reconstruct_path(dp, nodes, start_node, end_node, best_last)
        return min_total, path

    def find_hamiltonian_path(self, fixed_position=None, precedence_constraints=None, start=None, end=None):
        """Find minimum cost Hamiltonian path with constraints"""
        fixed_position = fixed_position or [None] * self.V
        precedence_constraints = precedence_constraints or []
        vertices = list(range(self.V))

        if (all(x is None for x in fixed_position) and
                not precedence_constraints and
                start is not None and end is not None):
            free_nodes = [i for i in vertices if i not in {start, end}]
            return self._held_karp(start, end, free_nodes)

        min_cost = float('inf')
        min_path = None
        free_nodes = _get_free_nodes(vertices, fixed_position, start, end)

        for perm_free in permutations(free_nodes):
            candidate = _build_candidate_path(fixed_position, perm_free)

            if not is_valid_permutation(candidate, fixed_position, precedence_constraints, start, end):
                continue

            cost = self._calculate_path_cost(candidate)

            if cost < min_cost:
                min_cost = cost
                min_path = candidate

        return (min_path, min_cost) if min_path else (None, None)


def distance(origins, destinations):
    api_key = "nV8MX9Jxszg9MyjUJv5yfTUK4OzKhTGtG0z2E779ZGtdhd2TenzBA1QgOzOf6H2T"
    url = "https://api-v2.distancematrix.ai/maps/api/distancematrix/json"

    params = {
        "origins": origins,
        "destinations": destinations,
        "key": api_key
    }

    response = requests.get(url, params=params)
    result = response.json()

    distance_value = result["rows"][0]["elements"][0]["distance"]["value"]
    duration_value = result["rows"][0]["elements"][0]["duration"]["value"]

    return distance_value, duration_value
