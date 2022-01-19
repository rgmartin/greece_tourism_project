# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 08:52:02 2022

@author: bales
"""

#IMPORT LIBRARIES/PACKAGES REQUIRED
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc
#!pip install dash-bootstrap-components
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import requests
import urllib
import urllib.request
import time 
import re 
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import seaborn as sns
import numpy as np
import plotly.express as px

def web_scraping():
    
    #WEB SCRAPING
    #CONNECT TO URL FOR WEB SCRAPING
    url = 'https://insete.gr/perifereies/' 
    response = requests.get(url) 
    soup = BeautifulSoup(response.text, 'html.parser')

    #FIND ALL LINK OBJECTS
    link_objs = soup.find_all('a',href=re.compile('/wp-content/uploads/'))
    
    #WEB SCRAPING EXCEL FILE FROM WEBSITE
    file_names = []
    region_names = []
    for i in range(len(link_objs)):
        str_link = str(link_objs[i])
        start_index = re.search(r"wp-content",str_link)
        end_index = re.search(r"\"",str_link[start_index.span()[0]:len(str_link)])
        end_url = str_link[start_index.span()[0]:start_index.span()[0]+end_index.span()[0]]
        sub_url = 'https://insete.gr/'+end_url

        if ".xlsx" in sub_url:
            file_names.append(sub_url)
            region_start_index = re.search(r"uploads",sub_url)
            region_end_index = re.search(r".xlsx",sub_url[region_start_index.span()[0]:len(sub_url)])
            region_end_url = sub_url[region_start_index.span()[0]+22:region_start_index.span()[0]+region_end_index.span()[0]-2]
            region_end_url = re.sub("_", " ", region_end_url)
            region_end_url = re.sub("  ", " ", region_end_url)
            region_names.append(region_end_url)

    return region_names, file_names

#GRAPH 1 ------------------------------------------------------------ *NOT USED
def employment_data(file_names):
    
    #EMPLOYMENT DATA ANALYSIS
    #EMPLOYMENT TAB PARSING
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    tab_name = "Employment"
    list_of_df = list()

    names = ["Year", "Accommodation and Catering Services Activities", "Other Industries", 
             "Total Employment", "Country Total", "% Services in Relation to the Whole Region", "% Other Branches in Relation to the Whole Region"]

    for i in range(len(file_names)):
        x = requests.get(file_names[i]).content
        file = pd.ExcelFile(x)
        df = file.parse(tab_name, header = 3, skipfooter = 14, index_col = 0)

        df.reset_index(inplace=True, drop=True)
        df = df.T
        df.reset_index(inplace=True)
        df.columns = names
        
        for i in range(1, 5):
            df.iloc[:,i] = df.iloc[:,i]*1000
        
        for i in range(5, 7):
            df.iloc[:,i] = df.iloc[:,i]*100
        
        list_of_df.append(df)
    
    return list_of_df

def graph_employment_per_year(list_of_df, year):

    #TOTAL COUNTRY EMPLOYMENT GRAPH
    #*************TODO : labels X and Y
    i = year[0] - 2010
    j = year[1] - 2010 + 1
    fig = px.line(list_of_df[0], x=list_of_df[0]["Year"][i:j], y=list_of_df[0]["Country Total"][i:j], width=800, height=600)
    
    return fig

#GRAPH 2 ------------------------------------------------------------
def employment_per_region(list_of_df, region_names):

    #EMPLOYMENT PER REGION DATA
    tot = pd.DataFrame(list_of_df[0]["Year"])

    for i in range(0, 13):
        tot = tot.join(pd.DataFrame(list_of_df[i].iloc[:,3]))
        tot = tot.rename(columns={tot.columns[i+1]: region_names[i]})
        
    return tot

def employment_data_graph(tot, year, region_names):

    #EMPLOYMENT PER REGION GRAPH   
    fig2 = go.Figure()
    years = [*range(year[0], year[1] + 1, 1)]
    fig2.add_trace(go.Scatter(name = region_names[0], x = years, y = tot.iloc[:,0], fill='tozeroy', 
                              mode = "none", stackgroup='one'))
    for i in range(1, 13):
        fig2.add_trace(go.Scatter(name = region_names[i], x = years, y = tot.iloc[:,i], fill='tonexty', 
                                  mode = "none", stackgroup='one'))           
    fig2.update_layout(width = 800, height = 600, xaxis_title='Year', yaxis_title='Employment')
    return fig2

#GRAPH 3 ------------------------------------------------------------
def arrivals_per_country():

    #ARRIVALS PER COUNTRY ANALYSIS
    #WEBSCRAPING EXCEL FILE FOR ARRIVALS PER COUNTRY
    url = 'https://insete.gr/statistika-eiserxomenou-tourismou/' 
    response = requests.get(url) 
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
    return fig1

#GRAPH 4 ------------------------------------------------------------ *NOT USED
def region_population_vs_tourism(file_names, region_names):

    #REGION POPULATION VS INCOMING TOURISM (INTERNATIONAL + DOMESTIC) ANALYSIS
    #2020 TOTAL INTERNATIONAL/DOMESTIC AIR ARRIVALS PER REGION
    url = 'https://insete.gr/perifereies/' 
    response = requests.get(url) 
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

def arrivals_per_region_graph(data):

    #GRAPH ARRIVALS DATA
    data.sort_values(by = "Total Domestic Air Arrivals", axis = 0, ascending = True, inplace = True)

    fig3 = go.Figure()                                                           
    fig3.add_trace(go.Bar(x = data["Total International Air Arrivals"], y = data["Region"], name = "International Arrivals", 
                          marker=dict(line=dict(width=0.1)), orientation = 'h'))
    fig3.add_trace(go.Bar(x = data["Total Domestic Air Arrivals"], y = data["Region"], name = "Domestic Arrivals",
                          marker=dict(line=dict(width=0.1)), orientation = 'h'))
    fig3.update_traces(width=0.65)
    fig3.update_layout(xaxis=dict(title_text="Total Arrivals", titlefont=dict(size=15), zeroline=False),
                       yaxis=dict(titlefont=dict(size=15)), width=800, height=600,
                       title={'text': "Total Air Arrivals in 2020 per Region", 'y':0.92, 'x':0.5, 
                              'xanchor': 'center','yanchor': 'top'}, barmode='stack', bargap=0.0)
    fig3.show()
    
    return fig3

#GRAPH 5 ------------------------------------------------------------
def import_population_data(data):
    #IMPORT EXCEL FILE WITH POPULATION DATA PER REGION
    #TODO***WEBSCRAPE POPULATION DATA INSTEAD OF IMPORT EXCEL FILE***
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
    return fig3