from somiti_detector.score import *
from somiti_detector.graph import *

users = get_users()

entries = cal_edge_scores_local(users)

G = find_graph_local(entries)
communities = find_communities(G)
fig = draw_graph(G, communities)


fig.show()
