# 使用 Elastic Stack 监控新冠疫情

## 丁香园数据的处理和展示

https://github.com/BlankerL/DXY-COVID-19-Data/tree/master/csv

💻 可以用下面的命令将 repo 下载到本地做数据分析。

git clone https://github.com/BlankerL/DXY-COVID-19-Data.git

💻 也可以用下面的命令在日后做数据更新，做后续的跟踪分析。

cd DXY-COVID-19-Data/
git pull
remote: Enumerating objects: 93, done.
remote: Counting objects: 100% (93/93), done.
remote: Compressing objects: 100% (5/5), done.
remote: Total 125 (delta 88), reused 93 (delta 88), pack-reused 32
Receiving objects: 100% (125/125), 3.48 MiB | 126.00 KiB/s, done.
Resolving deltas: 100% (94/94), completed with 14 local objects.
From https://github.com/BlankerL/DXY-COVID-19-Data
   6c6d9e3..bd1759f  master     -> origin/master
Updating 6c6d9e3..bd1759f
Fast-forward
 csv/DXYArea.csv                 | 251344 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++----------------------------------------------------------------
 csv/DXYNews.csv                 |     39 +
 csv/DXYOverall.csv              |     16 +
 json/DXYArea-TimeSeries.json    |  24285 +++++++++++++
 json/DXYArea.json               |   9144 ++---
 json/DXYNews-TimeSeries.json    |    370 +
 json/DXYNews.json               |     82 +-
 json/DXYOverall-TimeSeries.json |   3611 ++
 json/DXYOverall.json            |     26 +-
 9 files changed, 159031 insertions(+), 129886 deletions(-)

也可以使用 Logstash 或者是 Filebeat 持续的同步这个目录下的时序数据，这样就可以在 Kibana 上看到每日的实时更新结果。

### 导入数据并初始化索引

我们可以选择技术门槛比较低的一种方式，使用 Kibana 自带的数据导入功能，手工导入丁香园的 csv 时序数据文件  csv/DXYArea.csv 。

💻 先用导入程序分析数据文件中的字段，然后在使用下面特定的 Mapping 重新重定义默认的数据结构。

{
  "@timestamp": {
    "type": "date"
  },
  "continentEnglishName": {
    "type": "keyword"
  },
  "continentName": {
    "type": "keyword"
  },
  "countryEnglishName": {
    "type": "keyword"
  },
  "countryName": {
    "type": "keyword"
  },
  "provinceEnglishName": {
    "type": "keyword"
  },
  "provinceName": {
    "type": "keyword"
  },
  "province_confirmedCount": {
    "type": "integer"
  },
  "province_curedCount": {
    "type": "integer"
  },
  "province_deadCount": {
    "type": "integer"
  },
  "province_suspectedCount": {
    "type": "integer"
  },
  "province_zipCode": {
    "type": "integer"
  },
  "cityEnglishName": {
    "type": "keyword"
  },
  "cityName": {
    "type": "keyword"
  },
  "city_confirmedCount": {
    "type": "integer"
  },
  "city_curedCount": {
    "type": "integer"
  },
  "city_deadCount": {
    "type": "integer"
  },
  "city_suspectedCount": {
    "type": "integer"
  },
  "city_zipCode": {
    "type": "integer"
  },
  "level":{
    "type": "keyword"
  },
  "location": {
      "type": "geo_point"
  },
  "is_china": {
      "type": "boolean"
  },
  "updateTime": {
    "type": "date",
    "format": "yyyy-MM-dd HH:mm:ss"
  }
}

以上 Mapping 的说明：

* 增加了字段 level, is_china 和 Location
* level 定义了数据记录的级别为：国家、省和城市
* is_china 定义了国内外的数据
* 在导入后，字段的批量维护可以用 /_update_by_query 的方法，也可以是使用 ingest pipline 的方法。

💻 在导入之后，我们可以使用 Kibana 的 Discovery 来对导入的数据进行分析和确认，特别是一些关键字段的数值。观察这些数据的格式和内容是否有什么变化。使用filter 功能了解数据的内容和特征。

* countryName:中国 / NOT   --- 中国的数据
* countryName: 中国  provinceName: 中国   --- 中国的全国共计数据
* countryName: 中国   NOT provinceName: 中国 cityName exists   ---- 中国的各省统计数据
* countryName: 中国   NOT provinceName: 中国 NOT cityName exists  ---- 中国的港澳台统计数据
* countryName: 中国   cityName: 境外

查看这里的省英文名称，以广西为例：provinceEnglishName	Guangxi

💻 浏览与 Elastic Map 地图服务所引用的国际编码，查看 https://maps.elastic.co/#file/china_provinces ；在导入的时候，或者之后需要修正丁香园省名称数据的不规则现象，为地图展示做准备。

💻 下图是用 Excel 分析的结果，建议使用 Python 或者其它程序语言做字段的预处理和校准。

💻 然后，需要在 Dev Tool 中运行相关的数据优化和及校准脚本。

```
#维护is_china字段
POST dxy-area-m5/_update_by_query
{
  "script":{
    "lang": "painless",
    "source": """
       if (ctx._source.countryEnglishName == "China") {
         ctx._source.is_china = true;
       } else {
         ctx._source.is_china = false;
       }
    """
  }
}

#维护 level 字段，对于中国的数据来说，如果省的名字是中国这就是国家级的统计数据
POST dxy-area-m5/_update_by_query
{
  "script":{
    "lang": "painless",
    "source": """
      if(ctx._source.provinceName == ctx._source.countryName){
        ctx._source.level = "country"
      } else {
          if (ctx._source.cityName == null) {
            ctx._source.level = "cn-hmt"
          } else {
            ctx._source.level = "province"
          }
      }
    """
  }
}

#更新省的名字为国际代码
POST dxy-area-m5/_update_by_query
{
  "script":{
    "lang": "painless",
    "source": """
          if (ctx._source.provinceEnglishName == "Guangxi") {
            ctx._source.provinceEnglishName = "Guangxi Zhuang Autonomous Region";
          }
          if (ctx._source.provinceEnglishName == "Hong Kong") {
            ctx._source.provinceEnglishName = "HongKong";
          }

          if (ctx._source.provinceEnglishName == "Macao") {
            ctx._source.provinceEnglishName = "Macau";
          }

          if (ctx._source.provinceEnglishName == "Neimenggu") {
            ctx._source.provinceEnglishName = "Inner Mongolia";
          }

          if (ctx._source.provinceEnglishName == "Ningxia") {
            ctx._source.provinceEnglishName = "Ningxia Hui Autonomous Region";
          }

          if (ctx._source.provinceEnglishName == "Taiwan") {
            ctx._source.provinceEnglishName = "Taiwan Province";
            ctx._source.provinceName = "台湾省 (中华人民共和国)";
          }

          if (ctx._source.provinceEnglishName == "Xizang") {
            ctx._source.provinceEnglishName = "Tibet";
          }
          
          if (ctx._source.cityName == "境外输入人员") {
            ctx._source.cityName = "境外输入";
          }
          
    """
  }
}
```

💻 从 Discovery 中开始数据可视化：点击左侧 fields 清单中的 provinceName，查看其中的数值，点击下面的 Visualize 按钮。进入可视化编辑模式，选择 province_confirmedCount 的最大值，增加 level ： province 过滤条件。

💻 在 New Visualization 中选择 lens，在 CHANGE INDEX PATTERN 中选择目标的索引，拖拽几个字段进入显示区：continentName countryName province_confirmedCount 这些字段，尝试点击下方的建议格式，感受图形所提供的数据分析的线索。

💻 在已有的可视化中选择已经创建的可视化控件，分析和理解这些控件的制作方法和意图。

💻 查看地图，在已有的地图上创建新的各省治愈数量图层。

💻 查看仪表板，编辑和保存更新后的结果。

## 世卫组织数据的处理和展示

浏览世卫组织的数据 https://github.com/CSSEGISandData/COVID-19

参考了一篇国外的文章： https://www.siscale.com/importing-covid-19-data-into-elasticsearch/

这篇文章分享了如何使用 logstash 导入 Github 中世卫组织发布的数据，并持续与之保持同步。这里是他们的代码：https://github.com/siscale/covid-19-elk

下面描述如何使用这份代码。首先你需要有一个安装好的切正常运行的 Elasticsearch 7.6.1 服务器，一个可以正常使用的 Kibana 7.6.1 服务器。基础之上，安装 logstash 服务器，修改并放好 logstash 的配置文件。 在 Kibana 的 Dev Tool 中导入索引的 Mapping。启动 logstash 服务器，等待和确认数据的传入。导入 Kibana 的相关对象。浏览查看和确认 siscale 的作品。理解每个可视化展示控件的设计细节。

你也可以参考一下的安装步骤。

登录 Kibana，进入 Dev Tool 中，将文件 index-template-mapping.json 中的内容复制进去并点击执行按钮。

rpm -ivh logstash-7.6.1.rpm

修改配置文件中的 /etc/logstash/covid-19-hashes.json  为 /usr/share/logstash/covid-19-hashes.json

cp logstash-github-covid-19-daily-reports-template.conf  logstash-github-covid-19-time-series-template.conf  /etc/logstash/conf.d/

systemctl start logstash

sudo tail -f /var/log/logstash/logstash-plain.log

在日志中可以看到 logstash 完全正常的启动成功，或者报错后，停止 logstash 服务，并进行调整。直到服务彻底运行成功不报错。

登录 kibana， 进入管理 - saved objeces ； 点击 import 按钮。选择 kibana-7.6.1-covid-19-dashboard.ndjson 即可浏览名为 COVID 19 的仪表板了。