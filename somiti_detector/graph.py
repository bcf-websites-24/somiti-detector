from .db import *
import networkx as nx
from networkx.algorithms import community as nx_comm
from .config import config
import math
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def find_graph(users):
    users_dict = {user.id: user for user in users}

    G = nx.Graph()
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id1, user_id2, weight FROM somiti_graph")
            rows = cursor.fetchall()
            for row in rows:
                if row[2] > config.threshold:
                    G.add_edge(
                        str(users_dict[str(row[0])]),
                        str(users_dict[str(row[1])]),
                        weight=-math.log(row[2]),
                    )

    return G


def find_communities(G):
    communities_generator = nx_comm.girvan_newman(G)
    top_level_communities = next(communities_generator)
    communities = [list(community) for community in top_level_communities]
    return communities


def draw_graph(G, communities):
    pos = nx.spring_layout(G, k=0.1, iterations=100)

    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    colors = [
        "#FF5733",
        "#33FF57",
        "#3357FF",
        "#F3FF33",
        "#FF33F6",
        "#33FFF6",
        "#FFBD33",
        "#91FF33",
    ]
    node_traces = []

    for idx, community in enumerate(communities):
        node_x = []
        node_y = []
        node_text = []

        for node in community:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}")

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            text=node_text,
            mode="markers",
            hoverinfo="text",
            marker=dict(
                size=10,
                color=colors[idx % len(colors)],
                line_width=2,
            ),
        )

        node_traces.append(node_trace)

    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            title="Somiti Graph",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            annotations=[
                dict(showarrow=False, xref="paper", yref="paper", x=0.005, y=-0.002)
            ],
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        ),
    )

    return fig


def user_somiti_score(u, G, communities):
    """
    Geometric mean of cluster edges
    """
    score = 0.0
    n = 0
    for idx, community in enumerate(communities):
        if str(u) in community:
            for v1 in community:
                for v2 in community:
                    if v1 != v2 and G.has_edge(v1, v2):
                        score += G[v1][v2]["weight"]
                        n += 1
            break
    if n == 0:
        return 0.0
    return math.exp(-score / n)


def update_somiti_scores(users, G, communities):
    def worker(u):
        score = user_somiti_score(u, G, communities)
        update_user_somiti_score(u, score)

    with ThreadPoolExecutor(max_workers=24) as executor:
        tasks = []
        for u in users:
            task = executor.submit(worker, u)
            tasks.append(task)

        for task in tqdm(tasks):
            task.result()
