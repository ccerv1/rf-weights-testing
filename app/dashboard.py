import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import numpy as np

# Read the data
df = pd.read_csv('data/dev_tool_relationships.csv')

# Create the app
app = Dash(__name__)

# Define available metrics for weighting
METRICS = {
    'Num Project Devs Engaging with Dev Tool': 'Project Devs',
    'Num Smart Contract Devs Engaging with Dev Tool': 'Smart Contract Devs',
    'Project Total Txns': 'Total Transactions',
    'Project Total Gas Fees': 'Total Gas Fees'
}

# Add these constants
DEFAULT_TOP_PROJECTS = 50
DEFAULT_TOP_DEVTOOLS = 30
MAX_PROJECTS = 100
MAX_DEVTOOLS = 50

# Layout
app.layout = html.Div([
    html.H1("Project-DevTool Dependencies Sankey Diagram", 
            style={'marginBottom': '20px', 'fontSize': '24px'}),
    
    # Control panel container
    html.Div([
        # Left column - filters
        html.Div([
            # Relationship filter
            html.Div([
                html.Label("Filter Relationship Types:", 
                          style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='relationship-filter',
                    options=[{'label': rt, 'value': rt} 
                            for rt in df['Relationship Type'].unique()],
                    value=df['Relationship Type'].unique(),
                    multi=True,
                    style={'width': '100%'}
                )
            ], style={'marginBottom': '10px'}),
            
            # Top N selectors
            html.Div([
                html.Div([
                    html.Label("Top Projects (by gas fees):", 
                             style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '12px'}),
                    dcc.Slider(
                        id='top-projects-slider',
                        min=5,
                        max=MAX_PROJECTS,
                        step=5,
                        value=DEFAULT_TOP_PROJECTS,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='custom-slider'
                    )
                ], style={'flex': '1', 'minWidth': '150px'}),
                
                html.Div([
                    html.Label("Top Dev Tools (by users):", 
                             style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '12px'}),
                    dcc.Slider(
                        id='top-devtools-slider',
                        min=5,
                        max=MAX_DEVTOOLS,
                        step=5,
                        value=DEFAULT_TOP_DEVTOOLS,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='custom-slider'
                    )
                ], style={'flex': '1', 'minWidth': '150px'})
            ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '10px'})
        ], style={'flex': '1', 'marginRight': '20px', 'minWidth': '200px'}),
        
        # Right column - metric weights
        html.Div([
            html.Label("Metric Weights:", 
                      style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
            html.Div([
                html.Div([
                    html.Label(label, 
                             style={'fontSize': '12px', 'marginBottom': '2px'}),
                    dcc.Slider(
                        id=f'weight-{metric}',
                        min=0,
                        max=1,
                        step=0.1,
                        value=0.25,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='custom-slider'
                    )
                ], style={
                    'flex': '1 1 45%',
                    'margin': '5px',
                    'minWidth': '200px'
                }) for metric, label in METRICS.items()
            ], style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'gap': '10px',
                'alignItems': 'center'
            })
        ], style={'flex': '2'})
    ], style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '20px',
        'padding': '15px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '8px',
        'marginBottom': '20px'
    }),
    
    # Sankey diagram
    dcc.Graph(id='sankey-diagram', style={'height': '80vh'})
], style={'padding': '20px', 'maxWidth': '1400px', 'margin': 'auto'})

# Add this CSS to your app
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .custom-slider .rc-slider-track {
                background-color: #1f77b4;
            }
            .custom-slider .rc-slider-handle {
                border-color: #1f77b4;
            }
            .custom-slider .rc-slider-handle:hover {
                border-color: #1f77b4;
            }
            .custom-slider .rc-slider-handle:active {
                border-color: #1f77b4;
                box-shadow: 0 0 5px #1f77b4;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def normalize_column(series):
    """Min-max normalize a series to range [0,1]"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return series * 0  # Return zeros if all values are the same
    return (series - min_val) / (max_val - min_val)

@app.callback(
    Output('sankey-diagram', 'figure'),
    [Input('relationship-filter', 'value'),
     Input('top-projects-slider', 'value'),
     Input('top-devtools-slider', 'value')] +
    [Input(f'weight-{metric}', 'value') for metric in METRICS.keys()]
)
def update_sankey(rel_types, top_n_projects, top_n_devtools, *weights):
    # Filter by relationship types
    filtered_df = df[df['Relationship Type'].isin(rel_types)]
    
    # Get top N projects by gas fees
    top_projects = (filtered_df.groupby('Project Name')['Project Total Gas Fees']
                   .mean()
                   .sort_values(ascending=False)
                   .head(top_n_projects)
                   .index)
    
    # Get top N dev tools by number of project devs
    top_devtools = (filtered_df.groupby('Dev Tool Name')['Num Project Devs Engaging with Dev Tool']
                   .mean()
                   .sort_values(ascending=False)
                   .head(top_n_devtools)
                   .index)
    
    # Find overlapping names and filter
    overlapping = set(top_projects) & set(top_devtools)
    filtered_devtools = [tool for tool in top_devtools if tool not in overlapping]
    
    # Filter dataframe
    filtered_df = filtered_df[
        (filtered_df['Project Name'].isin(top_projects)) & 
        (filtered_df['Dev Tool Name'].isin(filtered_devtools))
    ]
    
    # Normalize each metric
    normalized_df = filtered_df.copy()
    for metric in METRICS.keys():
        normalized_df[f'normalized_{metric}'] = normalize_column(filtered_df[metric])
    
    # Calculate weighted values using normalized metrics
    weight_dict = dict(zip(METRICS.keys(), weights))
    normalized_df['weighted_value'] = sum(
        normalized_df[f'normalized_{metric}'] * weight
        for metric, weight in weight_dict.items()
    )
    
    # Normalize the final weighted value to make it more visually appealing
    normalized_df['weighted_value'] = normalize_column(normalized_df['weighted_value'])
    
    # Scale the values to make them visible in the Sankey diagram
    normalized_df['weighted_value'] = normalized_df['weighted_value'] * 100
    
    # Create nodes lists
    projects = normalized_df['Project Name'].unique()
    devtools = normalized_df['Dev Tool Name'].unique()
    
    # Create node labels and mapping
    node_labels = list(projects) + list(devtools)
    node_mapping = {node: idx for idx, node in enumerate(node_labels)}
    
    # Get project metrics for hover info
    project_metrics = {}
    for project in projects:
        project_data = filtered_df[filtered_df['Project Name'] == project].iloc[0]
        project_metrics[project] = [
            int(project_data['Num Project Devs Engaging with Dev Tool']),
            int(project_data['Num Smart Contract Devs Engaging with Dev Tool']),
            int(project_data['Project Total Txns']),
            float(project_data['Project Total Gas Fees'])
        ]
    
    # Get dev tool dependency counts
    tool_deps = {
        tool: [len(filtered_df[filtered_df['Dev Tool Name'] == tool]['Project Name'].unique())]
        for tool in devtools
    }
    
    # Prepare customdata for nodes
    node_customdata = []
    for node in node_labels:
        if node in projects:
            node_customdata.append(project_metrics[node])
        else:
            node_customdata.append(tool_deps[node])
    
    # Create Sankey data
    sankey_data = {
        'node': {
            'label': node_labels,
            'pad': 15,
            'thickness': 20,
            'color': ['#1f77b4'] * len(projects) + ['#ff7f0e'] * len(devtools),
            'customdata': node_customdata,
            'hoverinfo': 'all',
            'hovertemplate': [
                '<b>Project:</b> %{label}<br>' +
                '<b>Project Devs:</b> %{customdata[0]:,}<br>' +
                '<b>Smart Contract Devs:</b> %{customdata[1]:,}<br>' +
                '<b>Total Transactions:</b> %{customdata[2]:,}<br>' +
                '<b>Total Gas Fees:</b> %{customdata[3]:,.2f}<extra></extra>'
                if i < len(projects) else
                '<b>Dev Tool:</b> %{label}<br>' +
                '<b>Dependent Projects:</b> %{customdata[0]}<extra></extra>'
                for i in range(len(node_labels))
            ]
        },
        'link': {
            'source': [node_mapping[proj] for proj in normalized_df['Project Name']],
            'target': [node_mapping[tool] for tool in normalized_df['Dev Tool Name']],
            'value': normalized_df['weighted_value'],
            'hoverinfo': 'all',
            'hovertemplate': 'Source: %{source.label}<br>' +
                            'Target: %{target.label}<br>' +
                            'Weight: %{value:.2f}<extra></extra>'
        }
    }
    
    # Create figure
    fig = go.Figure(data=[go.Sankey(**sankey_data)])
    
    fig.update_layout(
        title_text="Project-DevTool Dependencies",
        font_size=10,
        height=800,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
