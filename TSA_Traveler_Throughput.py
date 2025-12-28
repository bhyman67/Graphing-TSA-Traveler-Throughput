import os, sys
import requests
import numpy as np
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
# import chart_studio.plotly as py
import plotly.graph_objects as go
from datetime import date, datetime
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Note, used to be able to push this to plotly chart studio, but it has shut down.
# and before chart studio, I used datapane which also has shut down.

def get_traveler_throughput_data(): 

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Gets traveler throughput data from the TSA's website
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++

    # Web request for the html (use BeautifulSoup to parse it)
    resp = requests.get("https://www.tsa.gov/travel/passenger-volumes")
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find the table and manually parse it
    table = soup.find("table")
    
    # Extract headers from the table
    headers = []
    header_row = table.find("thead").find("tr") if table.find("thead") else table.find("tr")
    for th in header_row.find_all(["th", "td"]):
        headers.append(th.text.strip())
    
    # Extract data rows
    rows_data = []
    tbody = table.find("tbody") if table.find("tbody") else table
    for row in tbody.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) > 0 and cells[0].text.strip():  # Skip empty rows
            row_data = [cell.text.strip() for cell in cells]
            # Only add if it's not the header row
            if row_data[0] not in headers:
                rows_data.append(row_data)
    
    # Create DataFrame from parsed data
    df = pd.DataFrame(rows_data, columns=headers)
    
    # Set the date col as an index 
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    
    # Convert numeric columns to proper numeric types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
    
    df.sort_index(ascending=True, inplace=True)

    return df    

def generate_fig_for_traveler_throughput_with_SMA():

    # Get traveler throughput data by scraping the web
    df = get_traveler_throughput_data()
    
    # Instantiate fig obj
    fig = go.Figure()
    
    # Initialize some vars
    button_list = []
    trace_list = []
    visibility = True
    years = list(df.columns) 
    sma_periods = {
        "Daily Throughput Counts":0, # 0 day SMA...
        "3 Day SMA":3,
        "7 Day SMA":7
    }
    
    # Create a graph object trace for each year and SMA period 
    for i, sma_period in enumerate(sma_periods):
            
        for year in years:
            
            # Calculate y values (which will be the SMA unless we're just showing daily throughput)
            if sma_periods[sma_period] == 0:
                sma_or_raw_throughputs = df[year] # raw throughputs for current year in the loop
            else:
                # SMA throughputs for current year in the loop
                sma_or_raw_throughputs = df[year].rolling( sma_periods[sma_period] ).mean()
            
            # Add trace to the graph object figure
            fig.add_trace(
                go.Scatter(
                    name = year,
                    visible = visibility,
                    x = df.index,
                    y = sma_or_raw_throughputs
                )
            )
            
        # The visibitly needs to be false for the rest of the traces after  
        # all have been created for the first SMA
        visibility = False

        # Add a button to the button list
        boolean_list = list(np.repeat(False, 6))
        boolean_list[i*2:(i*2)+2] = list(np.repeat(True, 2))
        button_list.append(
            dict(
                label = sma_period,
                method = "update",
                args = [{"visible":boolean_list}]
            )
        )

    # Update the layout of the fig
    button_list = list(button_list)
    fig.update_layout(
        title = {"text":'TSA Simple Moving Average Throughputs'},
        hovermode="x",
        xaxis=dict(tickformat="%b %d"),
        updatemenus = [
            dict(
                active = 0,
                buttons = button_list,
                direction="up",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1,
                xanchor="right",
                y=-0.05,
                yanchor="top"
            )
        ]
    )

    return fig

def generate_fig_for_traveler_throughput():

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Need to TRANSFORM the data table. Traveler Throughput for each year
    # needs to be in the same col. And a year column needs to be added.  
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    traveler_throughput = get_traveler_throughput_data()

    # For each col in the traveler throughput data (for each year), I need to create a new df.
    df_list = []
    for crnt_col in traveler_throughput.columns:
        
        new_df = traveler_throughput[crnt_col]
        new_df.dropna(inplace = True)
        new_df = new_df.to_frame()
        new_df = new_df.rename(columns = {crnt_col:"Traveler Throughput"})
        new_df.reset_index(inplace = True)
        new_df["Date"] = new_df["Date"].astype(str)
        
        new_df["Year"] = crnt_col
        
        df_list.append(new_df)

    # Combine each of the tables by stacking them on top of each other
    traveler_throughput = pd.concat(df_list)

    # ++++++++++++++++++++
    # Plotly Visualization
    # ++++++++++++++++++++

    # Generate the graph
    fig = px.line(
        traveler_throughput,
        x="Date",
        y="Traveler Throughput",
        color = "Year",
        title = 'TSA Daily Throughputs'
    )
    fig.update_layout(xaxis=dict(tickformat="%b %d"),hovermode="x")

    return fig

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    html.H1("TSA Traveler Throughput Dashboard", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
    
    html.Div([
        html.Label("Select Visualization Type:", 
                   style={'fontSize': 18, 'fontWeight': 'bold', 'marginBottom': 10}),
        dcc.RadioItems(
            id='graph-type',
            options=[
                {'label': ' Daily Throughput', 'value': 'daily'},
                {'label': ' Simple Moving Average', 'value': 'sma'}
            ],
            value='daily',
            labelStyle={'display': 'block', 'marginBottom': 10},
            style={'marginBottom': 20}
        )
    ], style={'width': '30%', 'margin': '0 auto', 'padding': 20}),
    
    dcc.Loading(
        id="loading",
        type="default",
        children=[
            dcc.Graph(id='throughput-graph')
        ]
    ),
    
    html.Div([
        html.P("Data source: TSA (Transportation Security Administration)", 
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': 20})
    ])
], style={'fontFamily': 'Arial, sans-serif', 'padding': 20})

# Define callback to update graph
@app.callback(
    Output('throughput-graph', 'figure'),
    Input('graph-type', 'value')
)
def update_graph(graph_type):
    if graph_type == 'sma':
        return generate_fig_for_traveler_throughput_with_SMA()
    else:
        return generate_fig_for_traveler_throughput()

# Run the app or handle command line arguments
if __name__ == '__main__':
    if len(sys.argv) > 1:
        
        if "SMA" in sys.argv[1]:
            
            # Plotly graph with SMA
            figure = generate_fig_for_traveler_throughput_with_SMA()
            
            if sys.argv[1]=="Show_Graph_With_SMA":
                
                print("Show the fig")
                figure.show()
                print("Fig should have been shown")
                
            # elif sys.argv[1] == "Publish_Graph_With_SMA_Online":
                
            #     py.plot(figure,filename = 'Graph-Traveler-Throughput_With_SMA', auto_open = False)
                
        else:
            
            # Plotly graph w/out SMA
            figure = generate_fig_for_traveler_throughput()
            
            if sys.argv[1]=="Show_Graph":
                
                figure.show()
                
            # elif sys.argv[1] == "Publish_Graph":
                
            #     py.plot(figure,filename = 'Graph-Traveler-Throughput', auto_open = False)
                
        print("Done...")
    else:
        # No command line args - run the Dash web app
        app.run(debug=True)
