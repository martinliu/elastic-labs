import csv
import sys
from os import listdir
from os.path import isfile, join
from elasticsearch import Elasticsearch
import json
import certifi
import datetime
from elasticsearch.helpers import bulk


PATH = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"
USER = "elastic"
PASSWORD = "PWD"
URL = "CLOUD_URL"

ES = Elasticsearch(
        [URL],
        port=9243,
        http_auth=USER + ":" + PASSWORD,
        use_ssl=True,
        verify_certs=True,
        ca_certs=certifi.where()
    )

ES.ping()

def mk_date(date):
    date = date.replace("/20 ", "/2020 ")
    try:
        return datetime.datetime.strptime(date, "%m/%d/%Y %H:%M").isoformat()
    except:
        return date
    
def generate_timestamp(file_name):
    file_name = file_name.replace('.csv', '')
    return datetime.datetime.strptime(file_name, "%m-%d-%Y").isoformat()

def mk_int(s):
    s = s.strip()
    return int(s) if s else 0

def read_csv(path, file_name):
    with open(path + "/" + file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        corona_country_reports = []
        for row in csv_reader:
            corona_country_report = {}
            if line_count == 0:
                line_count += 1
            else:
                corona_country_report["@timestamp"] = generate_timestamp(file_name)
                corona_country_report["Province/State"] = row[0]
                corona_country_report["Country/Region"] = row[1]
                corona_country_report["Last Update"] = mk_date(row[2])
                corona_country_report["Confirmed"] = mk_int(row[3])
                corona_country_report["Deaths"] = mk_int(row[4])
                corona_country_report["Recovered"] = mk_int(row[5])
                if len(row) > 6:
                    corona_country_report["coordinates"] = {"lat": float(row[6]), "lon": float(row[7])}
                corona_country_reports.append(corona_country_report)
                line_count += 1
    return corona_country_reports

def get_csv(path):
    only_files = [f for f in listdir(path) if isfile(join(path, f))]
    only_csv = [f for f in only_files if "csv" in f]
    return only_csv

def index_daily_report(file_name, corona_country_reports, elasticsearch, index_name = "coronavirus-"):
    if index_name == "coronavirus-":
        index_name = index_name + extract_date(file_name)
    bulk_list = [{"_source": corona_country_report, "_op_type": "index", "_index": index_name, "_type": "_doc"} for corona_country_report in corona_country_reports]
    response = bulk(ES, bulk_list)
    print(response)
    
def extract_date(file_name):
    date_components = file_name.split('-')
    return '.'.join([date_components[1], date_components[0], date_components[2]]).replace(".csv", '')

csvs = get_csv(PATH)
for file_name in csvs:
    print(file_name)
    corona_country_reports = read_csv(PATH, file_name)
    index_daily_report(file_name, corona_country_reports, ES)




