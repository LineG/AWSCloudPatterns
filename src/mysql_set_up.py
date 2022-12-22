import paramiko
import time
import json


def ssh_connect_with_retry(ssh, ip_address, retries):
    """
    This function connects via ssh on the instance.
    ssh : the id of the instance
    ip_address : the ip addres sof the instance
    retries : the number of tries before it fails.
    """
    if retries > 3:
        return False
    privkey = paramiko.RSAKey.from_private_key_file(
        'labsuser.pem')
    interval = 2
    try:
        retries += 1
        print('SSH into the instance: {}'.format(ip_address))
        ssh.connect(hostname=ip_address,
                    username="ubuntu", pkey=privkey)
        return True
    except Exception as e:
        print(e)
        time.sleep(interval)
        print('Retrying SSH connection to {}'.format(ip_address))
        ssh_connect_with_retry(ssh, ip_address, retries)


def install_mysql_stand_alone(ip):
    """
    This function installs mysql on a ec2 instance.
    Installs sakila on the stand alone node. 
    ip : the ip of the instance
    """
    # Setting Up SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 0)
    print(f"Connected through SSH! {ip}")
    _, stdout, _ = ssh.exec_command(
        "sudo apt-get update")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command("sudo apt-get -y install mysql-server")
    print(stdout.read())
    time.sleep(20)
    _, stdout, _ = ssh.exec_command(
        "cd /tmp/ && wget https://downloads.mysql.com/docs/sakila-db.tar.gz")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "cd /tmp/ && sudo tar xvf /tmp/sakila-db.tar.gz")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo mysql -u root < /tmp/sakila-db/sakila-schema.sql")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo mysql -u root < /tmp/sakila-db/sakila-data.sql")
    print(stdout.read())
    ssh.close()


def benchmark_on_stand_alone(ip):
    """
    This function benchmarks the slave nodes
    ip : the ip of the instance/slave
    """
    # Setting Up SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 0)
    _, stdout, _ = ssh.exec_command(
        "sudo apt -y upgrade && sudo apt-get -y install sysbench")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        f"sudo sysbench oltp_read_write --table-size=10000 --db-driver=mysql --mysql-db=sakila --mysql-user=root prepare")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        f"sudo sysbench oltp_read_write --table-size=10000  --threads=6 --max-time=60 --db-driver=mysql --max-requests=0 --mysql-db=sakila --mysql-user=root run")
    file = open('benchmarking/benchmark_slave.txt', 'wb')
    file.write(stdout.read())
    file.close()
    ssh.close()


def write_config_ini(ip_master, ip_slave1, ip_slave2, ip_slave3):
    """
    This function generates the config ini file of the master node
    """

    config = """[ndb_mgmd]
hostname="""+ip_master+"""
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname="""+ip_slave1+"""
nodeid=3

[ndbd]
hostname="""+ip_slave2+"""
nodeid=4

[ndbd]
hostname="""+ip_slave3+"""
nodeid=5

[mysqld]
nodeid=50
"""
    f = open("config.ini", "w")
    f.write(config)
    f.close()


def install_mysql_cluster_master(ssh_ip, ip_master, ip_slave1, ip_slave2, ip_slave3):
    """
    All the steps to install and download cluster on the master node
    """
    master_steps1 = """
#!/bin/bash
sudo mkdir -p /opt/mysqlcluster/home
sudo apt-get update
sudo apt-get -y install libncurses5
cd /opt/mysqlcluster/home
sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc
sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
cd conf
sudo chmod 777 /opt/mysqlcluster/deploy/conf
"""
    master_steps2 = """
#!/bin/bash
cd /opt/mysqlcluster/home/mysqlc
sudo scripts/mysql_install_db --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data/
sudo /opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd  -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf   
"""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ssh_ip, 3)
    print(f"Connected through SSH! {ip_master}")
    write_config_ini(ip_master, ip_slave1, ip_slave2, ip_slave3)
    _, stdout, _ = ssh.exec_command(master_steps1)
    print(stdout.read())
    ftp_client = ssh.open_sftp()
    ftp_client.put("my.cnf", "/opt/mysqlcluster/deploy/conf/my.cnf")
    ftp_client.put("config.ini", "/opt/mysqlcluster/deploy/conf/config.ini")
    ftp_client.put("mysql_privilege.sh", "/tmp/mysql_privilege.sh")
    ftp_client.close()
    _, stdout, _ = ssh.exec_command(master_steps2)
    print(stdout.read())
    ssh.close()


def install_mysql_slave_nodes(ip, master_ip):
    """
    Setting up the slave nodes of the cluster
    ip: ip of the slave
    master_ip: ip of the master
    """

    slave_step1 = """
#!/bin/bash
sudo mkdir -p /opt/mysqlcluster/home
sudo apt-get update
sudo apt-get -y install libncurses5
cd /opt/mysqlcluster/home
sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc
"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 3)
    print(f"Connected through SSH! {ip}")
    _, stdout, _ = ssh.exec_command(slave_step1)
    print(stdout.read())
    ssh.exec_command('sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data')
    _, stdout, _ = ssh.exec_command(
        f'sudo /opt/mysqlcluster/home/mysqlc/bin/ndbd -c {master_ip}:1186')
    print(stdout.read())
    ssh.close()


def master_node_set_up_mysql(ip):
    """
    ip: ip of the master
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 3)
    print(f"Connected through SSH! {ip}")
    ssh.exec_command(
        "nohup sudo /opt/mysqlcluster/home/mysqlc/bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root 1>/dev/null 2>/dev/null &")
    time.sleep(20)
    _, stdout, _ = ssh.exec_command("sudo bash /tmp/mysql_privilege.sh")
    print(stdout.read())
    time.sleep(5)
    _, stdout, _ = ssh.exec_command("sudo bash /tmp/mysql_privilege.sh")
    print(stdout.read())
    ssh.close()


def master_benchmark(ip):
    """
    This function performs the bechmarking of the master node
    Result: Save the output in the benchmark folder
    ip: the ip of the node
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 3)
    print(f"Connected through SSH! {ip}")
    _, stdout, _ = ssh.exec_command(
        "sudo apt-get update && sudo apt-get -y install sysbench")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        f"sudo sysbench oltp_read_write --table-size=10000 --mysql-db=sakila --mysql-user=myapp --mysql-password=MyNewPass --mysql-host={ip} prepare")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        f"sudo sysbench oltp_read_write --table-size=10000   --threads=6 --max-time=60 --max-requests=0 --mysql-db=sakila --mysql-user=myapp --mysql-host={ip} --mysql-password=MyNewPass run")
    file = open(f"benchmarking/benchmark_master_{ip}.txt", 'wb')
    file.write(stdout.read())
    file.close()
    ssh.close()


def sakila_on_cluster(ip):
    """
    This function sets up the sakila database on the cluster 
    This is done through the master
    ip: the ip of the node
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 3)
    print(f"Connected through SSH! {ip}")
    _, stdout, _ = ssh.exec_command(
        "cd /tmp/ && wget https://downloads.mysql.com/docs/sakila-db.tar.gz")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "cd /tmp/ && sudo tar xvf sakila-db.tar.gz")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -u root --password=MyNewPass < /tmp/sakila-db/sakila-schema.sql")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -u root --password=MyNewPass < /tmp/sakila-db/sakila-data.sql")
    print(stdout.read())
    ssh.close()


def get_cluster_node_ids():
    """
    When the cluster was set up we save all the ids in a Json file
    This simply retrives the public ids and private dns
    return: node_ids(public) and node_dns(private)
    """
    with open("cluster_node_ids.json", "r") as file:
        data = file.read()
    obj = json.loads(data)
    node_ids = [obj["cluster_1"].get("ip"), obj["cluster_2"].get("ip"),
                obj["cluster_3"].get("ip"), obj["cluster_4"].get("ip")]
    node_dns = [obj["cluster_1"].get("dns"), obj["cluster_2"].get("dns"),
                obj["cluster_3"].get("dns"), obj["cluster_4"].get("dns")]
    ip_stand_alone = obj["cluster_0"].get("ip")
    return node_ids, node_dns, ip_stand_alone


def install_cluster():
    """
    This function runs all the necessary functions to install
    the MySql Cluster
    """
    node_ids, node_dns, _ = get_cluster_node_ids()

    print("Setting up master and the required config files")
    install_mysql_cluster_master(
        node_ids[0], node_dns[0], node_dns[1], node_dns[2], node_dns[3])

    print("Connecting slaves of to cluster")
    install_mysql_slave_nodes(node_ids[1], node_dns[0])
    install_mysql_slave_nodes(node_ids[2], node_dns[0])
    install_mysql_slave_nodes(node_ids[3], node_dns[0])

    print("Starting master and giving privileges to myapp user")
    master_node_set_up_mysql(node_ids[0])


def run():
    node_ids, _, ip_stand_alone = get_cluster_node_ids()
    install_cluster()
    install_mysql_stand_alone(ip_stand_alone)
    benchmark_on_stand_alone(ip_stand_alone)

    sakila_on_cluster(node_ids[0])
    master_benchmark(node_ids[0])


run()
