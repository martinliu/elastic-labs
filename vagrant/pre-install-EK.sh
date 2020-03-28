echo I am provisioning a ELK stack...
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
sudo rpm -ivh /vagrant/rpm/kibana-7.6.1-x86_64.rpm
sudo systemctl daemon-reload
sudo systemctl start elasticsearch.service
sudo sh -c "echo 'server.host: 192.168.50.10' >> /etc/kibana/kibana.yml"
sudo systemctl start kibana.service
sudo systemctl status elasticsearch
sudo systemctl status kibana
echo Provisioning script works good!
echo Please go to http://192.168.50.10:5601/ 