#####Step 1: start by importing all of the necessary packages#####
import requests #requesting URLs
import urllib.request #requesting URLs
import os
import time #setting the speed at which the requests run
import re #regexp string manipulation
import pandas as pd #for simplifying data operations (e.g. creating dataframe objects)
import matplotlib.pyplot as plt #for plotting the scraped data
from bs4 import BeautifulSoup #for web-scraping operations
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




# get inbound tourism per country dataframe
# input: receives the years for which the data is needed
# returns a dataframe with a dataframe to be read by function plot_incoming_tourism_per_country
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
        return ''.join(x for x in file if x.isalpha())

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


# global function for plotting incoming tourism to different regions in Greece from different countries
def plot_incoming_tourism_per_country(data, year=2020):
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
    fig.update_layout(font_size=12, width=800, height=600)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    
    # fig.show()
    return fig



# function to read a dataframe with the shares of inbound tourism per Grece region
def get_regions_df():
    # auxiliary function to find the links of the excel files containing the regional data
    def get_links(url='https://insete.gr/perifereies/'):
        response = requests.get(url)  # Connect to the URL using the "requests" package
        soup = BeautifulSoup(response.text, 'html.parser')
        return [link.get('href') for link in soup.find_all('a') if ('xlsx' in link.get('href'))]

    def extract_region_name(url):
        file_w_extension = os.path.basename(url)
        file = os.path.splitext(file_w_extension)[0]
        return ''.join(x for x in file if x.isalpha())

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

def plot_share_of_inbound_tourism(data, years = [2010,2020]):
    data = data.loc[years[0]: years[1]]
    fig = px.bar(data,x = data.index, y =data.columns,
               labels=dict(value="Inbound tourism share (%)"))
    width = 200 + (years[1] - years[0]) * 60
    fig.update_layout( font_size=12, width=width,height=600,
                    legend_title = 'Region')
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    #fig.show()
    return fig


 # -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 08:52:02 2022

@author: bales
"""



# Bale's code

#IMPORT LIBRARIES/PACKAGES REQUIRED


#*********************************************FUNCTION DEFINITIONS *******************************

def web_scraping():
    #WEB SCRAPING
    #CONNECT TO URL FOR WEB SCRAPING
    url = 'https://insete.gr/perifereies/' 
    response = requests.get(url) 
    soup = BeautifulSoup(response.text, 'html.parser')

    #FIND ALL LINK OBJECTS
    link_objs = soup.find_all('a',href=re.compile('/wp-content/uploads/'))
    
    #WEB SCRAPING EXCEL FILES FROM WEBSITE
    file_names = []
    region_names = []
    for i in range(len(link_objs)):
        str_link = str(link_objs[i])
        start_index = re.search(r"wp-content",str_link)
        end_index = re.search(r"\"",str_link[start_index.span()[0]:len(str_link)])
        end_url = str_link[start_index.span()[0]:start_index.span()[0]+end_index.span()[0]]
        sub_url = 'https://insete.gr/'+end_url
        
        #FIND ALL STRINGS THAT CONTAIN AN EXCEL FILE EXTENSION
        if ".xlsx" in sub_url:
            file_names.append(sub_url)
            region_start_index = re.search(r"uploads",sub_url)
            region_end_index = re.search(r".xlsx",sub_url[region_start_index.span()[0]:len(sub_url)])
            region_end_url = sub_url[region_start_index.span()[0]+22:region_start_index.span()[0]+region_end_index.span()[0]-2]
            #CLEAN STRINGS
            region_end_url = re.sub("_", " ", region_end_url)
            region_end_url = re.sub("  ", " ", region_end_url)
            region_names.append(region_end_url)
    
    #RETURN REGION NAMES AND FILE NAMES
    return region_names, file_names

def employment_data(file_names):
    
    #EMPLOYMENT DATA ANALYSIS
    #EMPLOYMENT TAB PARSING
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    tab_name = "Employment"
    list_of_df = list()
    
    #MANUALLY INPUT NAMES IN ENGLISH (TRANSLATED FROM GREEK)
    names = ["Year", "Accommodation and Catering Services Activities", "Other Industries", 
             "Total Employment", "Country Total", "% Services in Relation to the Whole Region", "% Other Branches in Relation to the Whole Region"]
    
    #OBTAIN ALL EMPLOYMENT DATA FROM EACH EXCEL FILE
    for i in range(len(file_names)):
        x = requests.get(file_names[i]).content
        file = pd.ExcelFile(x)
        #GET DATA FROM EMPLOYMENT TAB
        df = file.parse(tab_name, header = 3, skipfooter = 14, index_col = 0)
        
        #CLEAN DATA
        df.reset_index(inplace=True, drop=True)
        df = df.T
        df.reset_index(inplace=True)
        df.columns = names
        
        #MULTIPLY CERTAIN ROWS BY 1000 (TABLE INDICATED THAT DATA WAS IN THOUSANDS)
        for i in range(1, 5):
            df.iloc[:,i] = df.iloc[:,i]*1000
        
        #MULTIPLY CERTAIN ROWS BY 100 (TABLE INDICATED THAT DATA WAS IN HUNDREDS)
        for i in range(5, 7):
            df.iloc[:,i] = df.iloc[:,i]*100
        
        list_of_df.append(df)
    
    #RETURN A LIST OF DATAFRAMES WITH EACH DATAFRAME BEING THE DATA FOUND IN THE EMPLOYMENT FILE
    #IN DIFFERENT EXCEL FILES (REGIONS)
    return list_of_df

def employment_per_region(list_of_df, region_names):

    #EMPLOYMENT PER REGION DATA
    employ_data = pd.DataFrame(list_of_df[0]["Year"])

    for i in range(0, 13):
        employ_data = employ_data.join(pd.DataFrame(list_of_df[i].iloc[:,3]))
        employ_data = employ_data.rename(columns={employ_data.columns[i+1]: region_names[i]})
        
    return employ_data

def employment_data_graph(employ_data, year, region_names):

    #EMPLOYMENT PER REGION GRAPH   
    fig1 = go.Figure()
    #DEFINE RANGE OF YEARS TO BE PLOTTED BASED ON INPUT YEARS
    years = [*range(year[0], year[1] + 1, 1)]
    fig1.add_trace(go.Scatter(name = region_names[0], x = years, y = employ_data.iloc[:,0], fill='tozeroy', 
                              mode = "none", stackgroup='one'))
    for i in range(1, 13):
        fig1.add_trace(go.Scatter(name = region_names[i], x = years, y = employ_data.iloc[:,i], fill='tonexty', 
                                  mode = "none", stackgroup='one'))           
    fig1.update_layout( xaxis_title='Year', yaxis_title='Employment')
    fig1.update_layout(font_size=12, width=800, height=600)
    fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10))

    #RETURN GRAPH
    return fig1

#GRAPH 3 ------------------------------------------------------------
def arrivals_per_country():

    #ARRIVALS PER COUNTRY ANALYSIS
    #WEBSCRAPING EXCEL FILE FOR ARRIVALS PER COUNTRY
    #url = 'https://insete.gr/statistika-eiserxomenou-tourismou/' 
    #response = requests.get(url) 
    file_name = 'https://insete.gr/wp-content/uploads/2020/06/Key_figures_of_incoming_TourismGR-1.xlsx'
    x = requests.get(file_name).content
    file = pd.ExcelFile(x)
    arr = file.parse('Αφίξεις ανά χώρα προέλευσης', header = 3, skipfooter = 7, index_col = 0)
    arr = arr.T
    #TRANSLATE COUNTRY NAMES
    column_names = ['EU', 'Austria', 'Belgium', 'France', 'Germany', 'Spain', 'Italy', 'Cyprus', 'Netherlands', 'Other EU',
                    'Non EU', 'Denmark', 'Romania', 'Sweden', 'Czech Republic', 'Other Non EU', 'Other Countries', 'Albania', 'Australia', 'Switzerland', 
                    'UK', 'USA', 'Canada', 'Russia', 'Others', 'Total']
    arr.columns = column_names
    
    arr = arr.drop(['EU', 'Non EU', 'Other Countries'], axis=1)
    arr.sort_values(by = 2010, axis = 1, ascending = False, inplace = True)
    country_names = arr.columns
    
    return arr, country_names

def get_graph_1(year, arr, country_names):
    fig1 = go.Figure()
    years = [*range(year[0], year[1] + 1, 1)]

    for i in range(1,23):
        fig1.add_trace(go.Bar(x = arr.iloc[:,i]/arr['Total']*100, y = years, name = country_names[i], 
                              marker=dict(line=dict(width=0.1)), orientation = 'h'))
    fig1.update_traces(width=0.65)
    fig1.update_layout(xaxis=dict(title_text="Share of Arrivals", titlefont=dict(size=15), 
                                  ticktext=["0%", "20%", "40%", "60%","80%","100%"], 
                                  tickvals=[0, 20, 40, 60, 80, 100], showgrid=False, showline=False, zeroline=False), 
                       yaxis=dict(title_text="Year", titlefont=dict(size=15), tickvals = years), width=800, height=1000, 
                       barmode='stack', bargap=0.0)
    fig1.update_layout(font_size=12, width=800, height=600)
    fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig1

#GRAPH 4 ------------------------------------------------------------ *NOT USED
def region_population_vs_tourism(file_names, region_names):

    #REGION POPULATION VS INCOMING TOURISM (INTERNATIONAL + DOMESTIC) ANALYSIS
    #2020 TOTAL INTERNATIONAL/DOMESTIC AIR ARRIVALS PER REGION
    #url = 'https://insete.gr/perifereies/' 
    #response = requests.get(url) 
    tab_names = ["Intern-Domestic Air Arrivals"]*13 
    tab_names[1] = "Internat-domestic air arrivals"
    tab_names[4] = "Domestic Air Arrivals"
    tab_names[6] = "Intern-Domestic air Arrivals"
    tab_names[12] = "Intern-domestic air arrivals"
    skipfooter = [144, 144, 144, 143, 143, 143, 144, 143, 144, 144, 143, 143, 143]
    data = pd.DataFrame(columns=["Region", "Total International Air Arrivals", "Total Domestic Air Arrivals"])

    for i in range(len(file_names)):
        x = requests.get(file_names[i]).content
        file = pd.ExcelFile(x)
        df = file.parse(tab_names[i], header = 3, skipfooter = skipfooter[i], index_col = 0)

        if i == 4:
            df2 = {'Region': region_names[i], 'Total International Air Arrivals': 0, 'Total Domestic Air Arrivals': df['Σύνολο']}
            data = data.append(pd.DataFrame(df2), ignore_index = True)

        elif i == 5:
            df2 = {'Region': region_names[i], 'Total International Air Arrivals': df['Σύνολο '], 'Total Domestic Air Arrivals': df['Σύνολο .1']}
            data = data.append(pd.DataFrame(df2), ignore_index = True)
  
        elif i == 12:
            df2 = {'Region': region_names[i], 'Total International Air Arrivals': df['Σκύρος'], 'Total Domestic Air Arrivals': df['Σκύρος.1']}
            data = data.append(pd.DataFrame(df2), ignore_index = True)
  
        else:
            df2 = {'Region': region_names[i], 'Total International Air Arrivals': df['Σύνολο'], 'Total Domestic Air Arrivals': df['Σύνολο.1']}
            data = data.append(pd.DataFrame(df2), ignore_index = True)

    data["Total Air Arrivals"] = data["Total International Air Arrivals"] + data["Total Domestic Air Arrivals"]
    
    return data


#GRAPH 3 ------------------------------------------------------------
def import_population_data(data):
    #IMPORT EXCEL FILE WITH POPULATION DATA PER REGION
    pop_data = pd.read_excel(r'Population_data_per_region.xlsx')
    data2 = pd.merge(data, pop_data, on='Region')
    
    return data2

def get_arrivals_vs_population_graph(data2, value):
    if value == "All":
        name = "Total Air Arrivals"
    else:
        name = "Total " + value + " Air Arrivals"

    fig3 = go.Figure(data=go.Scatter(x=data2['Population (residents)'], y=data2[name], text = data2['Region'],
                mode='markers', marker=dict(color='green')))
    fig3.update_traces(marker_size=15)
    fig3.update_layout(width = 600, height = 500, xaxis_title='Region Population', yaxis_title=name)
    fig3.update_layout(font_size=12, width=800, height=600)
    fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig3