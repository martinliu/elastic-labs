
# Elastic Stack 系统搭建并使用 Filebeat 做系统日志管理

本文描述如何搭建一套具备用户名和密码安全认证的 Elastic Stack 系统，并开始使用 Filebeat 的基础模块实现分布式日志收集。

* 安装单节点 Elasticsearch 服务器，启用用户名和密码安全认证，并创建 TLS 数字证书备用
* 安装 Kibana 服务器，并配置与 Elasticsearch 服务的连接
* 安装和配置 Filebeat 代理程序，并配置 system 和 auditd 模块
* 使用 Kibana 监控Filebeat 的系统日志监控状态

## 试验环境概述和启动

本文所使用相关软件以及版本。

* macOS Catalina version 10.15.3
* Vagrant 2.2.4
* VirtalBox 6.0
* 操作系统镜像: bento/centos-8  (virtualbox, 202002.04.0)
* Elastic Stack 安装包（RPM）
  * Elasticsearch 7.6.1
  * Kibana 7.6.1
  * Filebeat 7.6.1
* 使用 Vagrant 的目录共享功能，分享安装包到测试机的 /vagrant/rpm 目录下

注意事项：

1. 你也可以使用任何一台 CentOS 8 虚拟机或者云主机，则后续的安装命令和 rpm 安装包的路径需要有所变化。
2. Vagrant 文件中定义的虚拟机配置为 4 GB 内存，建议你的操作系统最低为 8GB 内存，推荐 16GB 或者更高，
3. 本文也适用于 Linux 或 Windows 操作系统的 Vagrant 测试环境，需要提前下载并且准备好 bento/centos-8 的基础操作系统镜像。

启动测试环境。


```
vagrant up
vagrant status
```

## 安装 Elasticsearch 服务器

SSH 登录测试虚拟机。

`vagrant ssh`

执行 RPM 安装命令，安装 elasticsearch 服务器。

```
cd /vagrant/rpm
sudo rpm -ivh  ./elasticsearch-7.6.1-x86_64.rpm
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch.service
sudo systemctl start elasticsearch.service
sudo systemctl status elasticsearch.service
```


测试 Elasticsearch 服务是否功能正常 【 Dry run 】

curl localhost:9200

期待的输出类似下面。

```
{
  "name" : "elk-master",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "X4V2Yvc-SJ6ccjWbXQ5OmQ",
  "version" : {
    "number" : "7.6.1",
    "build_flavor" : "default",
    "build_type" : "rpm",
    "build_hash" : "aa751e09be0a5072e8570670309b1f12348f023b",
    "build_date" : "2020-02-29T00:15:25.529771Z",
    "build_snapshot" : false,
    "lucene_version" : "8.4.0",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}

```
浏览和学习 Elasticsearch 默认的配置文件。

`sudo cat /etc/elasticsearch/elasticsearch.yml`

使用 Elasticsearch 的精简版目标测试配置文件。

```
sudo cp /vagrant/elasticsearch/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml
sudo systemctl restart  elasticsearch.service
sudo systemctl status   elasticsearch.service

```
手工查看 Elasticsearch 服务器的日志，并确认服务启动正常。

`sudo tail -f /var/log/elasticsearch/my-elk.log`

Ctl + c 终止以上日志查看，再次测试 Elasticsearch 服务。

`curl localhost:9200`

替换为 IP 地址测试。

`curl http://192.168.50.10:9200/`

## 配置 Elasticsearch 服务的 TLS 数字证书和身份验证

停止 Elasticsearch 服务。

`sudo systemctl stop  elasticsearch.service`

### 创建 TLS 数字证书

```
cd /usr/share/elasticsearch
sudo bin/elasticsearch-certutil cert -out /etc/elasticsearch/elastic-certificates.p12 -pass ""
sudo chmod 660 /etc/elasticsearch/elastic-certificates.p12
```

### 更新 Elasticsearch 配置文件

手工打开 Elasticsearch 配置文件。

`sudo vi /etc/elasticsearch/elasticsearch.yml`

在配置文件的末端增加下面的配置段落。

```bash
# ------------------------------- TLS and Cert ---------------------------------
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
```

重新启动配置 Elasticsearch 服务。

```
sudo systemctl restart  elasticsearch.service
sudo systemctl status  elasticsearch.service

```
确认服务已经正常启动。

`sudo tail -f /var/log/elasticsearch/my-elk.log`

### 创建 Elasticsearch 服务的用户密码

运行 Elasticsearch 的密码配置工具，为各种内置用户生成随机的密码。

```
sudo cd /usr/share/elasticsearch
sudo bin/elasticsearch-setup-passwords auto
```

将生成的密码信息妥善保存备用。

```bash
Changed password for user apm_system
PASSWORD apm_system = AHyg5HzJRZg8Fiva0buW

Changed password for user kibana
PASSWORD kibana = Kt72IXkiarlGr7do02Yp

Changed password for user logstash_system
PASSWORD logstash_system = Q9nnlOdf6V9kyPbbhqN7

Changed password for user beats_system
PASSWORD beats_system = bLNrZDggPKRSKc35EG32

Changed password for user remote_monitoring_user
PASSWORD remote_monitoring_user = o1pi2yTDnhrKBGcS6xqP

Changed password for user elastic
PASSWORD elastic = RO11xymgXTCD16ivTP33
```

在浏览器中访问http://192.168.50.10:9200/ ，测试并确认上面的 elastic 用户的密码。

## 安装和配置 Kibana 服务器

执行 Kibana 安装命令

```
cd /vagrant/rpm/
sudo rpm -ivh  kibana-7.6.1-x86_64.rpm
```
查看并学习 Kibana 默认配置文件

`sudo cat /etc/kibana/kibana.yml`

更新默认配置文件，准备好 elastic 用户的密码，将其更新到 Kibana 配置文件中。

```
sudo cp /vagrant/kibana/kibna.yml /etc/kibana/kibana.yml
sudo systemctl start  kibana.service
sudo systemctl status   kibana.service
```

查看重启的服务是否工作正常。

`sudo tail -f /var/log/messages`

在浏览器里测试登录 Kibana  http://192.168.50.10:5601 ，使用 elastic 的用户名和密码。

## 安装 filebeat 并配置 2 个模块

执行 Filebeat 安装包。

```
cd /vagrant/rpm
sudo rpm -ivh ./filebeat-7.6.1-x86_64.rpm
```

查看默认的 Filebeat 配置文件。

`sudo cat  /etc/filebeat/filebeat.yml`

更新默认配置文件，准备好 elastic 用户的密码，将其更新到 Kibana 配置文件中。

`sudo cp /vagrant/filebeat/filebeat.yml /etc/filebeat/filebeat.yml`

查看 Filebeat 的默认日志监控模块。

`sudo filebeat modules list`

启用 Filebeat 的 System 和 Auditd 模块，监控系统日志和基础的操作系统安全信息。

`sudo filebeat modules enable system auditd`

查看 Filebeat 监控模块的配置文件。

```
sudo cd /etc/filebeat
sudo ls -l modules.d/
```

建议查看以上启用的 System 和 Auditd 模块的配置文件。

运行 Filebeat 在后台的初始化命令，在后台创建 Filebeat 所需要的索引 filebeat-* ，并导入所有模块相关的 Dashboard 等 Kibana 日志可视化分析工具。下面这条命令只需要在第一个 Filebeat 的第一次运行前，执行一次，在这之后，其它所有 Filebeat 的配置文件里都不需要与 Kibana 相关的配置参数了。在后续的多节点安装中，会体现出来这个差异。

`sudo filebeat setup`

在浏览器中登录 http://192.168.50.10:5601 Kibana 后，点击左侧的 Dashboard 图标，查看所有刚才导入的内容，搜索并打开 System 关键字的 Dasboard。

在启动日志收集代理 Filebeat 服务前，运行一下命令测试 Filebeat 配置文件的正确性。

`sudo filebeat test config`

启动 Filebeat 服务，开始对这台操作系统的日志进行监控。


```
sudo systemctl start filebeat
sudo systemctl status filebeat
```

## 建议的测试


1. 点击左侧的 Dicovery 图标，选中 Filebeat-* 索引，打开并一条日志数据，并查看所有字段；用 KQL 进行全文搜索。
2. 点击左侧的 Dashboard 图标，搜索 system 关键字，查看一个仪表板的日志展示；搜索 audit 关键字，并查打开一个仪表板，在命令行中尝试 ssh localhost，多尝试几次，刷新 Audit 仪表板，观察数据是否发生了变化。
3. 点击左侧的 Logs 图标，用鼠标上下滚动日志信息流， 点击右上角的开始 Live Stream 查看模式，观察日志信息流的自动滚动效果，在 KQL 搜素框中输入 tags : demo-service ，体验它的搜索建议功能，在 Highlight 中输入 http://192.168.50.10:5601/app/infra ，观察日志信息流显示的变化。
4. 点击左侧的 SIEM 图标，看看这里都有什么内容。


## 后续

* 用启用 Filebeat 的 Elasticsearch, Kibana 日志监控模块
* 安装 Apache, MySQL 等软件，并开启 Filebeat 的日志监控模块

参考文档：
https://www.elastic.co/guide/en/elasticsearch/reference/current/setting-system-settings.html

