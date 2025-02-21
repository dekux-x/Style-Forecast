import heapq
import random
from collections import defaultdict
from typing import List

from back_fastapi.subcategory_weights import subcategory_weights
from .clothes_repository import ClothingsResponse


def weather_fun(temperature: float, weight: int) -> str:
    """
    Calculate the minimum warmness class based on temperature and body weight.
    Ensures only the right branches of the parabolas are considered.

    Args:
    - temperature (float): The temperature in °C.
    - weight (int): The body weight in kg.

    Returns:
    - str: The minimum warmness class ("Extra Warm", "Warm", "Medium", "Light").
    """

    # Define the parabola parameters (a, h) for each boundary
    def extra_warm_curve(x):
        return 3 * (x + 10) ** 2  # a=10, h=10

    def warm_curve(x):
        return 4 * (x) ** 2  # a=8, h=14

    def medium_curve(x):
        return 4 * (x - 10) ** 2  # a=6, h=18

    def light_curve(x):
        return 4 * (x - 20) ** 2  # a=4, h=22

    # Check against each parabola (right branch only)
    if temperature <= -10 and weight < extra_warm_curve(temperature):
        return "Extra warm"
    elif temperature <= 0 and weight < warm_curve(temperature):
        return "Warm"
    elif temperature <= 10 and weight < medium_curve(temperature):
        return "Medium"
    elif temperature <= 20 and weight < light_curve(temperature):
        return "Light"
    else:
        # If the temperature doesn't meet any branch conditions, default to "Light"
        return "Extra light"



class Graph:
    def __init__(self):
        self.adj_list = defaultdict(list)

    def add_edge(self, u, v, weight):
        """
        Add an edge between nodes u and v with a given weight.
        """
        self.adj_list[tuple(u)].append((v, weight))
        self.adj_list[tuple(v)].append((u, weight))


def build_graph(clothing_items: List[ClothingsResponse]) -> Graph:
    g = Graph()
    for item1 in clothing_items:
        for item2 in clothing_items:
            if item1.category != item2.category:  # Only connect different categories
                sub1, sub2 = item1.subcategory, item2.subcategory
                if (sub1, sub2) in subcategory_weights:
                    weight = subcategory_weights[(sub1, sub2)] + random.randint(0, 20)
                    if item1.color == item2.color:
                        weight -= random.randint(0,2)  # Favor matching colors
                    g.add_edge(item1, item2, weight)
    return g


def find_top_n_paths(graph: Graph, wardrobe: List[ClothingsResponse], required_categories, n):

    """
    Find the top N shortest paths covering all required categories,
    starting from any node in the wardrobe.

    Args:
    - graph (Graph): The clothing compatibility graph.
    - wardrobe (list of Cloth): List of clothing items (nodes).
    - required_categories (list of str): List of required clothing categories.
    - n (int): Number of shortest paths to return.

    Returns:
    - list of tuples: Each tuple contains (total weight, path as list of node IDs).
    """
    # Min-heap for path searching
    pq = []
    # Shortest paths
    paths = []

    max_total_weight = 99999999
    c = 0

    # Initialize the priority queue with all wardrobe items
    for cloth in wardrobe:
        heapq.heappush(pq, (0, [cloth]))  # Start from every node
        while pq:  # Choose every path
            total_weight, path = heapq.heappop(pq)


            # Check if the path covers all required categories
            path_categories = {cloth.category for cloth in path}
            if set(required_categories).issubset(path_categories):  # Subset check
                # print(path)
                heapq.heappush(paths, (-total_weight, path))
                if len(paths) > n:
                    heapq.heappop(paths)
                    max_total_weight = min(max_total_weight, -paths[0][0] - 1)

            # continue

            # Expand the path
        if total_weight < max_total_weight:
            last_node = path[-1]
            used_categories = {item.category for item in path}  # Track used categories
            k = 0
            for neighbor, weight in graph.adj_list[tuple(last_node)]:
                k+=1
                if(k > 50000):
                    k = 0
                    break
                c += 1
                # depth limit
                if(c > 10000000): return [(abs(weight), path) for weight, path in sorted(paths)]
                # print(max_total_weight)
                if neighbor not in path:  # Avoid cycles
                    if neighbor.category not in used_categories:
                        if total_weight + weight < max_total_weight:
                            heapq.heappush(pq, (total_weight + weight, path + [neighbor]))
    # print(c)
    return [(abs(weight), path) for weight, path in sorted(paths)]

# Example usage
# temperature = 12  # °C
# weight = 75  # kg
# warmness_class = weather_fun(temperature, weight)
# print(f"For temperature {temperature}°C and weight {weight} kg, the warmness class is: {warmness_class}")