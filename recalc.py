from somiti_detector.score import *
from somiti_detector.graph import *


users = get_users()

calc_edge_scores(users)

G = find_graph(users)
communities = find_communities(G)

update_somiti_scores(users, G, communities)
