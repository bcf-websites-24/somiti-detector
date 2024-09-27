import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from somiti_detector.graph import *
from datetime import datetime
import pytz
from somiti_detector.graph import *
from somiti_detector.score import *
from somiti_detector.config import config

app = Dash(__name__)

fig = None
timezone = pytz.timezone("Asia/Dhaka")
last_update_time = datetime.now()


app.layout = html.Div(
    [
        dcc.Graph(id="network-graph", style={"width": "100%", "height": "100vh"}),
        dcc.Interval(
            id="interval-component",
            interval=10 * 60 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ],
    style={"width": "100%", "height": "100vh", "margin": "0"},
)


@app.callback(
    Output("network-graph", "figure"), Input("interval-component", "n_intervals")
)
def get_graph(n_intervals):
    global fig

    users = get_users()

    G = find_graph(users)
    communities = find_communities(G)

    fig = draw_graph(G, communities)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)

server = app.server
