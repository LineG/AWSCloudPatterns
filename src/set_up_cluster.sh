#Common
sudo mkdir -p /opt/mysqlcluster/home
sudo apt-get update
sudo apt-get -y install libncurses5
cd /opt/mysqlcluster/home
sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc
sudo sh -c "echo export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc >> /etc/profile.d/mysqlc.sh"
sudo sh -c "echo export PATH=$MYSQLC_HOME/bin/./:$PATH >> /etc/profile.d/mysqlc.sh"
source /etc/profile.d/mysqlc.sh


#MANAGER
sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
cd conf
sudo nano my.cnf
"""
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306
"""

sudo nano config.ini
"""
[ndb_mgmd]
hostname=ip-172-31-88-180.ec2.internal
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=2
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname=ip-172-31-82-153.ec2.internal
nodeid=3

[ndbd]
hostname=ip-172-31-85-243.ec2.internal
nodeid=4

[mysqld]
nodeid=50
"""

cd /opt/mysqlcluster/home/mysqlc
sudo scripts/mysql_install_db --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data/
sudo /opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd  -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf
sudo /opt/mysqlcluster/home/mysqlc/bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root &



#NODES
sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data
sudo /opt/mysqlcluster/home/mysqlc/bin/ndbd -c ip-172-31-83-143.ec2.internal

