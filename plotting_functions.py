#####Step 1: start by importing all of the necessary packages#####
import requests  # requesting URLs
import urllib.request  # requesting URLs
import os
import time  # setting the speed at which the requests run
import re  # regexp string manipulation
import pandas as pd  # for simplifying data operations (e.g. creating dataframe objects)
import matplotlib.pyplot as plt  # for plotting the scraped data
from bs4 import BeautifulSoup  # for web-scraping operations
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State


def get_countries_df(years):
    # auxiliary function to find the links of the excel files containing the regional data
    def web_scrapper(url='https://insete.gr/perifereies/'):
        response = requests.get(url)  # Connect to the URL using the "requests" package
        soup = BeautifulSoup(response.text, 'html.parser')
        return [link.get('href') for link in soup.find_all('a') if ('xlsx' in link.get('href'))]

        # auxiliary function to extract the region name from the url

    def extract_region_name(url):
        file_w_extension = os.path.basename(url)
        file = os.path.splitext(file_w_extension)[0]
        name = ''.join(x for x in file if x.isalpha())
        name = name.replace("Macedonia", "Mac.")
        return name

    # auxiliary function for reading data from a particular region
    def read_region(region_url, key_figure=0, year=2020):
        data = requests.get(region_url).content
        xl = pd.ExcelFile(data)
        parameters = {'sheet_name': 2, 'header': [1], 'index_col': [0, 1]}
        # localise those rows corresponding to the first multindex
        df = xl.parse(**parameters)
        region_name = extract_region_name(region_url)
        # find the indices that correspond to the data for the corresponding year
        try:
            year_index = [s for s in df.index.get_level_values(0) if str(year) in s][0]
            first_idx = df.index.get_level_values(level=0).get_loc(year_index)
            first_idx = first_idx + 2  # correction for the known table format
            list_of_final_idx = df.index.get_level_values(level=0).get_loc(
                'Πηγή: Έρευνα Συνόρων της ΤτΕ, Επεξεργασία INSETE Intelligence'
            )
            final_idx = [i for i, x in enumerate(list_of_final_idx) if (x and (i > first_idx))][0]
            final_idx = final_idx - 2
            df = df.iloc[first_idx:final_idx, key_figure].droplevel(level=0)
            df.name = region_name
            return (df)
        except:
            return (None)

    excel_links = web_scrapper('https://insete.gr/perifereies/')
    key_figure = 0
    data = {}
    for year in years:
        list_of_df = [read_region(url, key_figure, year) for url in excel_links]
        list_of_df = [df for df in list_of_df if not (df is None)]
        data[year] = pd.concat(list_of_df, axis=1)
        data[year] = data[year].rename(index=dict(zip(

            ['Λοιπές', 'Γερμανία', 'Ην. Βασίλειο', 'Γαλλία', 'Βουλγαρία', 'Ιταλία',
             'Κύπρος', 'Βόρεια Μακεδονία', 'Τουρκία', 'Ολλανδία', 'Πολωνία',
             'Αλβανία', 'Ρουμανία', 'ΗΠΑ ', 'Ελβετία', 'Σερβία', 'Βέλγιο', 'Αυστρία',
             'ΗΠΑ']

            , ['Other Countries', 'Germany', 'Un. Kingdom ', 'France ', 'Bulgaria ',
               'Italy', 'Cyprus', 'Northern Macedonia', 'Turkey', 'Netherlands',
               'Poland', 'Albania', 'Romania', 'USA', 'Switzerland', 'Serbia',
               'Belgium', 'Austria', 'USA'])))
    return data


# global function for plotting incoming tourism to different regions in Greece
def incoming_tourism(data, year=2020):
    # auxiliary function to construct the nodes of the shankey diagram
    def nodes_df(df):
        regions = list(df.columns)
        countries = list(df.index)
        nodes = pd.DataFrame(data=regions + countries, columns=['Label'])
        nodes.index.name = 'ID'
        cm = plt.get_cmap('tab20')
        n = len(regions + countries)
        colors = [matplotlib.colors.rgb2hex(rgba) for rgba in cm(range(n))]
        nodes['Color'] = colors
        return nodes

        # auxiliary function to construct the links of the shankey diagram

    def links_df(nodes, input_df):
        links = input_df.stack().reset_index()
        links = links.rename(columns={
            links.columns[0]: 'Origin',
            links.columns[1]: 'Destination',
            links.columns[2]: 'Value',
        })
        links['Origin_id'] = links.apply(lambda row: nodes.index[nodes.Label == row['Origin']].to_list()[0], axis=1)
        links['Destination_id'] = links.apply(lambda row: nodes.index[nodes.Label == row['Destination']].to_list()[0],
                                              axis=1)
        links['Color'] = links.apply(lambda row: nodes.Color[nodes.Label == row['Destination']].values[0], axis=1)
        return links

    nodes = nodes_df(data[year])
    links = links_df(nodes, data[year])
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes['Label'],
            color=list(nodes['Color']),
            hovertemplate='%{value} (thousands of tourists.<extra></extra>)'

        ),
        link=dict(
            source=links['Origin_id'],  # indices correspond to labels, eg A1, A2, A1, B1, ...
            target=links['Destination_id'],
            value=links['Value'],
            color=[f'rgba{tuple(matplotlib.colors.to_rgba(c)[:3] + (0.2,))}' for c in links['Color']]

        ))])
    fig.update_layout(font_size=12, width=800, height=600, margin=dict(l=10, r=10, t=10, b=10))

    # fig.show()
    return fig


def get_regions_df():
    # auxiliary function to find the links of the excel files containing the regional data
    def get_links(url='https://insete.gr/perifereies/'):
        response = requests.get(url)  # Connect to the URL using the "requests" package
        soup = BeautifulSoup(response.text, 'html.parser')
        return [link.get('href') for link in soup.find_all('a') if ('xlsx' in link.get('href'))]

    def extract_region_name(url):
        file_w_extension = os.path.basename(url)
        file = os.path.splitext(file_w_extension)[0]
        name = ''.join(x for x in file if x.isalpha())
        name = name.replace("Macedonia", "Mac.")
        return name

    def read_inbound_tourism(url):
        data = requests.get(url).content
        xl = pd.ExcelFile(data)
        parameters = {'sheet_name': 6, 'header': [3], 'index_col': [0, 1]}
        df = xl.parse(**parameters)
        series = df.loc['Σύνολο'].iloc[0]
        series.name = extract_region_name(url)
        return series

    excel_links = get_links('https://insete.gr/perifereies/')
    inbound_tourism_df = pd.concat([read_inbound_tourism(url) for url in excel_links], axis=1)
    inbound_tourism_df.index.name = 'Year'
    inbound_tourism_df.sort_values(axis=1, by=2020, ascending=False, inplace=True)
    inbound_tourism_shares = inbound_tourism_df.div(inbound_tourism_df.sum(axis=1), axis=0) * 100
    # visualisation based on https://towardsdatascience.com/create-effective-data-visualizations-of-proportions-94b69ad34410
    # ideas of visualisation https://www.politico.eu/article/europe-tourism-boom-time-overtourism-top-destinations/
    return inbound_tourism_shares


def share_of_inbound_tourism(data, years=[2010, 2020]):
    data = data.loc[years[0]: years[1]]
    fig = px.bar(data, x=data.index, y=data.columns,
                 labels=dict(value="Inbound tourism share (%)"))
    width = 200 + (years[1] - years[0]) * 60
    fig.update_layout(font_size=12, width=width, height=600,
                      legend_title='Region', margin=dict(l=10, r=10, t=10, b=10))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    # fig.show()
    return fig
