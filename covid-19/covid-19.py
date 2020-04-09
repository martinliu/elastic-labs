import requests
import json
import time
import hashlib
import os
from elasticsearch import Elasticsearch

def make_id(dict):
    # use date ad part of id to make sure one record per day which is easy to analyze
    time_local = time.localtime(dict['updateTime']/1000)
    dt = time.strftime("%Y-%m-%d",time_local)
    text='-'.join([dt,dict['continentName'] if 'continentName' in dict else '',dict['countryName'],dict['provinceName'],dict['cityName'] if 'cityName' in dict else '']).encode()
    return str(hashlib.md5(text).hexdigest()).lower()

# Init ES
es_url = os.environ.get('ES_URL') if 'ES_URL' in os.environ else 'http://192.168.50.10'
es_username = os.environ.get('ES_USERNAME') if 'ES_USERNAME' in os.environ else 'elastic'
es_passwd = os.environ.get('ES_PASSWD') if 'ES_PASSWD' in os.environ else ''
es = Elasticsearch(hosts=[es_url],http_auth=(es_username, es_passwd))
index_name = "covid-19-data"

# Check if need to import all data
need_all_data = not es.indices.exists(index=index_name)

# create index
if need_all_data:
    es.indices.create(index=index_name,body={
        "settings": {
    "index.refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "level": {
        "type": "keyword"
      },
        "continentEnglishName" : {
          "type" : "keyword",
        },
        "continentName" : {
          "type" : "keyword"
        },
        "countryEnglishName" : {
          "type" : "keyword"
        },
        "countryName" : {
          "type" : "keyword"
        },
        "countryShortCode" : {
          "type" : "keyword"
        },
      "cityEnglishName": {
        "type": "keyword"
      },
      "cityName": {
        "type": "keyword"
      },
      "comment": {
        "type": "text"
      },
      "confirmedCount": {
        "type": "long"
      },
      "curedCount": {
        "type": "long"
      },
      "currentConfirmedCount": {
        "type": "long"
      },
      "deadCount": {
        "type": "long"
      },
      "locationId": {
        "type": "keyword"
      },
      "provinceEnglishName" : {
          "type" : "keyword"
       },
      "provinceName": {
        "type": "keyword"
      },
      "provinceShortName": {
        "type": "keyword"
      },
      "statisticsData": {
        "type": "object",
        "enabled": False
      },
      "suspectedCount": {
        "type": "long"
      },
      "updateTime":{
        "type":"date"
      }
    }
  }
    })


# request to covid-19 api
all_url='https://lab.isaaclin.cn/nCoV/api/area?latest=0'
update_url='https://lab.isaaclin.cn/nCoV/api/area?latest=1'
debug_url='https://lab.isaaclin.cn/nCoV/api/area?latest=1&province=%E6%96%B0%E8%A5%BF%E5%85%B0'

url=update_url
if need_all_data :
    url = all_url
    print("All historical data will be crawled and this will take some time. Be Patient!")
else:
    print('Just try to crawl latest data')

print("Start to request %s"%(url))
response = requests.get(url)
print("Finish request! Time %d s" %(response.elapsed.total_seconds()))
# print(response.text)

print("Decode to json......")
response_json = json.loads(response.text)

#print(response_json)

data_ids=[]
duplicate_data=[]
data_array=[]
current_time = int(round(time.time() * 1000))
for result in response_json['results']:
    #print(result.get('provinceName'))
    province_data={'level': 'province'}
    city_data_prep={'level': 'city'}
    for k,v in result.items():
        if k not in ['cities','comment']:
            province_data[k] = v
            city_data_prep[k] = v

    # use current time
    if not need_all_data:
        province_data['updateTime'] = current_time

    province_data['id'] = make_id(province_data)

    if province_data['id'] in data_ids:
        duplicate_data.append(province_data)
    else:
        data_ids.append(province_data['id'])
        data_array.append(province_data)

    # update time
    time_local = time.localtime(province_data['updateTime']/1000)
    dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)

    print('%d - UpdateTime %s, Add province %s, Id %s ' % (len(data_array),dt,province_data['provinceName'],province_data['id']))

    if 'cities' in result and result['cities'] != None:
        for city in result['cities']:
            city_data=city_data_prep.copy()
            for k,v in city.items():
                city_data[k] = v
            #print(city_data)
            # use current time
            if not need_all_data:
                city_data['updateTime'] = current_time

            city_data['id'] = make_id(city_data)

            if city_data['id'] in data_ids:
                duplicate_data.append(city_data)
            else:
                data_ids.append(city_data['id'])
                data_array.append(city_data)

            print('%d - UpdateTime %s, Add province %s, city %s, Id %s ' % (len(data_array),dt,province_data['provinceName'],city_data['cityName'],city_data['id']))

print('Crawl total ',len(data_array),' items!')
print('Start to import to es !')

print('es url is %s' % es_url)

bulk_actions = []

for data in data_array:
    bulk_actions.append({
        'update': {
            '_index': index_name,
            #'_type': 'doc',
            '_id': data['id'],

        }
    })
    bulk_actions.append({
        'doc': data,
        'doc_as_upsert': True
    })

    if len(bulk_actions) >= 5000:
        # print(bulk_actions)
        res = es.bulk(body=bulk_actions)
        # print(total_count)
        print(".")
        bulk_actions = []

if len(bulk_actions) > 0:
    res = es.bulk(body=bulk_actions)
    print(".")
    # print(res)
    # print(total_count)

print('=========================END==========================')
print('Import total ',len(data_array),' records!')
print("With %d duplicate records!"%(len(duplicate_data)))
