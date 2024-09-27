from somiti_detector.score import *
from somiti_detector.graph import *

users = get_users()

# uncomment to update all the scores, takes about 10 minutes
# do if you update config
# calc_edge_scores(users)

G = find_graph(users)
communities = find_communities(G)
fig = draw_graph(G, communities)

# also uncomment to update all the scores
# update_somiti_scores(users, G, communities)

fig.show()
