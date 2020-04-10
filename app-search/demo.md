开发搜索功能从此再也不用犯愁了，有了 App Search ，为应用增加搜索功能一下子变得简单了很多。
本文描述了如何轻松上手这套搜索系统平台的所有步骤。

什么是 App Search? 这是一套强大的 API 和开发者工具集，以构建功能强大的面向用户的搜索应用为目标。

丰富的开箱即用功能:

* 为相关性搜索应用场景而优化
* 拼写错误容忍
* 相关度调整
* 支持第三方 API 客户端，且具备强大的 API
* 独立的 API 日志和搜索分析
* 自动化扩展&运维支持
* Search UI library


## 环境准备

测试环境现需要一台 Elasticsearch 服务器。

本文的环境描述如下：

* macOS 10.15.4
* vagrant 2.2.7
* virtualbox 6.0.15
* 虚拟机模板 bento/centos-8
* elasticsearch 7.6.1
* app-search 7.6.1
* jdk-11.06

本文的测试环境基于 Vagrant + VirtualBox 的组合环境搭建而成，基础安装工作可以一键完成。主要脚本如下。

Vagrantfile

# -*- mode: ruby -*-
# vi: set ft=ruby :
IMAGE_NAME = 'bento/centos-8'

Vagrant.configure("2") do |config|
  config.vm.define "master1" do |master1|
    config.vm.box = IMAGE_NAME    #操作系统镜像
    config.ssh.insert_key = false
    config.vm.hostname = 'master1'  #主机名
    config.vm.network :private_network, ip: "192.168.50.10"  #私有网络 Ip 地址
    config.vm.network 'forwarded_port', guest: 9200, host: 9200
    config.vm.network 'forwarded_port', guest: 5601, host: 5601
    config.vm.provision :shell, path: 'pre-install-ES.sh' #操作系统初始化脚本
    config.vm.provider :virtualbox do |vb|
      vb.memory = 6000 #内存
      vb.cpus = 1 #CPU
    end
  end
end

pre-install-ES.sh

echo I am provisioning a Elasticsearch Server...
date > /etc/vagrant_provisioned_at
sudo swapoff -a
sudo sysctl -w vm.max_map_count=262144
sysctl -p
sudo sh -c "echo 'elasticsearch  -  nofile  65535' >> /etc/security/limits.conf"
sudo sh -c "echo '**** --  --  --  --  --  --  --  -- ****' > /etc/motd"
sudo sh -c "echo '**** Welcome to Elastic Stack Labs' >> /etc/motd"
sudo sh -c "echo '**** --  --  --  --  --  --  --  -- ****' >> /etc/motd"
sudo sh -c "echo '*' >> /etc/motd"
sudo rpm -ivh /vagrant/rpm/elasticsearch-7.6.1-x86_64.rpm 
sudo /usr/share/elasticsearch/bin/elasticsearch-certutil cert -out /etc/elasticsearch/elastic-certificates.p12 -pass ""
sudo chmod 660 /etc/elasticsearch/elastic-certificates.p12
sudo cp /vagrant/elasticsearch/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml
sudo systemctl daemon-reload
sudo systemctl start elasticsearch.service
sudo systemctl status elasticsearch
sudo /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto -b
echo Provisioning script works good!
echo Please go to http://192.168.50.10:9200/  using above passwords

开启并登陆这套安装环境的命令如下。

vagrant up
vagrant ssh

在以上命令的启动信息里找到如下的 elastic 用户密码部分备用。



## 安装 App Search 

先浏览 App Search 的安装文档： https://swiftype.com/documentation/app-search/self-managed/installation

sudo rpm -ivh /vagrant/rpm/jdk-11.0.6_linux-x64_bin.rpm

sudo rpm -ivh /vagrant/rpm/app-search-7.6.1.rpm 

sudo more /usr/share/app-search/config/app-search.yml 

sudo cp /vagrant/appsearch/app-search.yml /usr/share/app-search/config/app-search.yml

sudo /usr/share/app-search/bin/app-search


*** Default user credentials have been setup. These are only printed once, so please ensure they are recorded. ***
      username: app_search
      password: 37ky3zjidrpkkyx7



[root@master-1 config]# more app-search.yml | grep ^[^#]

elasticsearch.host: http://127.0.0.1:9200
elasticsearch.username: elastic
app_search.external_url: http://192.168.50.10:3002
app_search.listen_host: 192.168.50.10
app_search.listen_port: 3002
log_directory: /var/log/app-search
filebeat_log_directory: /var/log/app-search
