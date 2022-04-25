import plotly.graph_objects as go
import json

with open('timings.json') as f:
    data = json.load(f)


fig = go.Figure()
fig.add_trace(go.Box(y=data['login']['server']['GET'], name='Login Server GET'))
fig.add_trace(go.Box(y=data['login']['server']['POST'], name='Login Server POST'))
fig.add_trace(go.Box(y=data['user']['server']['GET'], name='User Server GET'))
fig.add_trace(go.Box(y=data['user']['server']['POST'], name='User Server POST'))

fig.update_layout(
    yaxis_title='Time (ms)',
    title='Server Response Times',
    margin=dict(l=50, r=50, t=50, b=50),
    width=800,
    height=600
)

fig.show()
