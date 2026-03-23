import matplotlib.pyplot as plt
import networkx as nx
from graph_builder import G   # IMPORTANT

def extract_bfs_subgraph(G, center_node, depth=2):
    nodes = nx.single_source_shortest_path_length(G.to_undirected(), center_node, cutoff=depth).keys()
    return G.subgraph(nodes).copy()

def _node_label(node_id):
    return str(node_id).split(":", 1)[1] if ":" in str(node_id) else str(node_id)

def visualize_subgraph(G_sub):
    color_map = {
        "Customer": "blue",
        "Order": "orange",
        "Delivery": "green",
        "Invoice": "red",
        "Payment": "teal",
    }

    node_colors = [color_map.get(attrs.get("type", ""), "gray") for _, attrs in G_sub.nodes(data=True)]
    labels = {node: _node_label(node) for node in G_sub.nodes()}

    pos = nx.spring_layout(G_sub, seed=42)

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G_sub, pos, node_color=node_colors, node_size=1400, alpha=0.9)
    nx.draw_networkx_edges(G_sub, pos, arrows=True, arrowstyle="->", arrowsize=18)
    nx.draw_networkx_labels(G_sub, pos, labels=labels, font_size=9, font_color="white")

    plt.axis("off")
    plt.show()


# PICK ONE ORDER NODE
order_node = next((n for n, attrs in G.nodes(data=True) if attrs.get("type") == "Order"), None)

subG = extract_bfs_subgraph(G, order_node, depth=2)

visualize_subgraph(subG)