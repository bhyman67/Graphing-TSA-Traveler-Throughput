import os
import sys
import numpy as np
import requests
import pandas as pd
import datapane as dp
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
# import chart_studio.plotly as py

def get_traveler_throughput_data(): 

    # +++++++++++++++++++++++++++++++++++++++
    # Data retrieval, formating, and sorting
    # +++++++++++++++++++++++++++++++++++++++

    # Web request for the html
    resp = requests.get("https://www.tsa.gov/coronavirus/passenger-throughput")
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Grab the data table from the html and
    # place it into a pandas dataframe
    tbl = str(soup.find("table"))
    df = pd.read_html(tbl)[0]

    # Loop through all of the dates and turn 2020s into 2021s
    for index, row in df.iterrows():
        if row["Date"][-4:] == "2021":
            df.iloc[index,0] = df.iloc[index,0].replace("2021","2022")
    
    # ...
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date",inplace=True) # does it make sense to do this??? 
    df.sort_index(ascending=True,inplace=True)

    return df    

def generate_fig_for_traveler_throughput_with_SMA():

    # ++++++++++++++++++++
    # Plotly Visualization
    # ++++++++++++++++++++

    # Get traveler throughput data by scraping the web
    df = get_traveler_throughput_data()
    
    # Instantiate fig obj
    fig = go.Figure()
    
    # Initialize some vars
    year_list = list(df.columns)
    sma_list = {
        "Daily Throughput Counts":0,
        "3 Day Moving Average (SMA)":3,
        "7 Day Moving Average (SMA)":7
    } 
    button_list = []
    trace_list = []
    visibility = True
    
    # Create a trace for each year for each SMA (0 day AKA raw count, 3 day, and 7 day)
    for i, sma in enumerate(sma_list):
            
        for year in year_list:
            
            # Calculate y values
            if sma_list[sma] == 0:
                y_vals = df[year]
            else:
                y_vals = df[year].rolling(sma_list[sma], min_periods = sma_list[sma]).mean()
            
            # Add trace to the figure
            fig.add_trace(
                go.Scatter(
                    name = year,
                    visible = visibility,
                    x = df.index,
                    y = y_vals
                )
            )
            
        # The visibitly needs to be false for the rest of the traces after  
        # all have been created for the first SMA
        visibility = False

        # Add a button to the button list
        boolean_list = list(np.repeat(False, 12))
        boolean_list[i*4:(i*4)+4] = list(np.repeat(True, 4))
        button_list.append(
            dict(
                label = sma,
                method = "update",
                args = [{"visible":boolean_list}]
            )
        )

    # Update the layout of the fig
    button_list = list(button_list)
    fig.update_layout(
        title = {"text":"TSA Checkpoint Numbers - Traveler Thoughput (2019/2020/2021)"},
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

    # Per col in the traveler throughput data, I need to create a new df.
    df_list = []
    for col_name in traveler_throughput.columns:
        
        new_df = traveler_throughput[col_name]
        new_df.dropna(inplace = True)
        new_df = new_df.to_frame()
        new_df = new_df.rename(columns = {col_name:"Traveler Throughput"})
        new_df.reset_index(inplace = True)
        new_df["Date"] = new_df["Date"].astype(str)
        
        new_df["Year"] = col_name
        
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
        title = 'TSA Checkpoint Numbers - Traveler Thoughput (2019/2020/2021/2022)'
    )
    fig.update_layout(xaxis=dict(tickformat="%b %d"),hovermode="x")

    return fig

if len(sys.argv) >  1:
    
    #dp.login(token=os.environ["DATAPANE_API_KEY"])
    
    if "SMA" in sys.argv[1]:
        
        figure = generate_fig_for_traveler_throughput_with_SMA()
        
        if sys.argv[1]=="Show_Graph_With_SMA":
            
            print("Show the fig")
            figure.show()
            print("Fig should have been shown")
            
        elif sys.argv[1] == "Publish_Graph_With_SMA_Online":
            
            # py.plot(figure,filename = 'Graph-Traveler-Throughput_With_SMA', auto_open = False)
            datapane_report = dp.Report(dp.Plot(figure))
            datapane_report.upload(name='Traveler Throughput with SMA')
            
    else:
        
        figure = generate_fig_for_traveler_throughput()
        
        if sys.argv[1]=="Show_Graph":
            
            figure.show()
            
        elif sys.argv[1] == "Publish_Graph":
            
            # py.plot(figure,filename = 'Graph-Traveler-Throughput', auto_open = False)
            datapane_report = dp.Report(dp.Plot(figure))
            datapane_report.upload(name='Traveler Throughput')
            
else:
    
    my_df = get_traveler_throughput_data()

print("Done...")
