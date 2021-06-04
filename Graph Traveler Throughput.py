
import sys
import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import chart_studio.plotly as py

def generate_fig_for_traveler_throughput():

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

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Need to transform the data table. Traveler Throughput for each year
    # needs to be in the same col. And a year column needs to be added.  
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
    figure = generate_fig_for_traveler_throughput()
    if sys.argv[1] == "Graph":
        figure.show()
    elif sys.argv[1] == "Publish_Online":
        py.plot(figure,filename = 'Graph-Traveler-Throughput')

print("Done...")