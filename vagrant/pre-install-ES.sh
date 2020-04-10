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