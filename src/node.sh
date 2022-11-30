wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb
sudo dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb
sudo apt-get update -y
sudo apt-get install -y libclass-methodmaker-perl
sudo apt-get install -y libjson-perl

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb
sudo dpkg -i mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb
sudo nano nano /etc/my.cnf

mkdir -p /usr/local/mysql/data