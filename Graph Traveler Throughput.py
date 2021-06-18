
import sys
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import chart_studio.plotly as py

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
        if row["Date"][-4:] == "2020":
            df.iloc[index,0] = df.iloc[index,0].replace("2020","2021")
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date",inplace=True)
    df.sort_index(ascending=True,inplace=True)

    return df    

def generate_fig_for_traveler_throughput_with_SMA():

    # ++++++++++++++++++++
    # Plotly Visualization
    # ++++++++++++++++++++

    df = get_traveler_throughput_data()

    # Generate the figure and update the layout
    fig = go.Figure()
    fig.update_layout(
        title = {"text":"TSA Checkpoint Numbers - Traveler Thoughput (2019/2020/2021)"},
        hovermode="x",
        xaxis=dict(tickformat="%b %d"),
        updatemenus = [
            dict(
                active = 0,
                buttons = list([ # are we sure that we need the square brackets...? 
                    # Button 1
                    dict(
                        label = "Daily Throughput Counts",
                        method = "update",
                        args = [{"visible":[True,True,True,False,False,False,False,False,False]}]
                    ),
                    # Button 2
                    dict(
                        label = "3 Day Moving Average (SMA)",
                        method = "update",
                        args = [{"visible":[False,False,True,True,True,False,False,False,False]}]
                    ),
                    # Button 3
                    dict(
                        label = "7 Day Moving Average (SMA)",
                        method = "update",
                        args = [{"visible":[False,False,False,False,False,False,True,True,True]}]
                    )
                ]),
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

    # Raw time series (set this to be visible from the start)
    fig.add_trace(go.Scatter(name = "2021", visible = True, x = df.index, y = df["2021 Traveler Throughput"])) 
    fig.add_trace(go.Scatter(name = "2020", visible = True, x = df.index, y = df["2020 Traveler Throughput"]))
    fig.add_trace(go.Scatter(name = "2019", visible = True, x = df.index, y = df["2019 Traveler Throughput"]))

    # SMA 3
    fig.add_trace(go.Scatter(name = "2021", visible = False, x = df.index, y = df["2021 Traveler Throughput"].rolling(3, min_periods=3).mean()))
    fig.add_trace(go.Scatter(name = "2020", visible = False, x = df.index, y = df["2020 Traveler Throughput"].rolling(3, min_periods=3).mean()))
    fig.add_trace(go.Scatter(name = "2019", visible = False, x = df.index, y = df["2019 Traveler Throughput"].rolling(3, min_periods=3).mean()))

    # SMA 7
    fig.add_trace(go.Scatter(name = "2021", visible = False, x = df.index, y = df["2021 Traveler Throughput"].rolling(7, min_periods=7).mean())) 
    fig.add_trace(go.Scatter(name = "2020", visible = False, x = df.index, y = df["2020 Traveler Throughput"].rolling(7, min_periods=7).mean()))
    fig.add_trace(go.Scatter(name = "2019", visible = False, x = df.index, y = df["2019 Traveler Throughput"].rolling(7, min_periods=7).mean()))

    return fig

def generate_fig_for_traveler_throughput():

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Need to transform the data table. Traveler Throughput for each year
    # needs to be in the same col. And a year column needs to be added.  
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    df = get_traveler_throughput_data()

    # Build a 2021 DF
    df_2021 = df["2021 Traveler Throughput"]
    df_2021.dropna(inplace=True)
    df_2021 = df_2021.to_frame()
    df_2021 = df_2021.rename(columns={"2021 Traveler Throughput":"Traveler Throughput"})
    df_2021["Year"] = "2021"

    # Build a 2020 DF
    df_2020 = df["2020 Traveler Throughput"]
    df_2020 = df_2020.to_frame()
    df_2020 = df_2020.rename(columns={"2020 Traveler Throughput":"Traveler Throughput"})
    df_2020["Year"] = "2020"

    # Build a 2019 DF
    df_2019 = df["2019 Traveler Throughput"]
    df_2019 = df_2019.to_frame()
    df_2019 = df_2019.rename(columns={"2019 Traveler Throughput":"Traveler Throughput"})
    df_2019["Year"] = "2019"

    # Combine each of the tables by stacking them on top of each other
    new_df = pd.concat([
        df_2021,
        df_2020,
        df_2019
    ])

    # ++++++++++++++++++++
    # Plotly Visualization
    # ++++++++++++++++++++

    # Generate the graph
    fig = px.line(
        new_df, 
        x=new_df.index, 
        y="Traveler Throughput", 
        color = "Year", 
        title = 'TSA Checkpoint Numbers - Traveler Thoughput (2019/2020/2021)'
    )
    fig.update_layout(xaxis=dict(tickformat="%b %d"),hovermode="x")

    return fig

if len(sys.argv) >  1:
    if "SMA" in sys.argv[1]:
        figure = generate_fig_for_traveler_throughput_with_SMA()
        if sys.argv[1]=="Show_Graph_With_SMA":
            figure.show()
        elif sys.argv[1] == "Publish_Graph_With_SMA_Online":
            py.plot(figure,filename = 'Graph-Traveler-Throughput_With_SMA')
    else:
        figure = generate_fig_for_traveler_throughput()
        if sys.argv[1]=="Show_Graph":
            figure.show()
        elif sys.argv[1] == "Publish_Graph":
            py.plot(figure,filename = 'Graph-Traveler-Throughput')

print("Done...")