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


def copy_files_and_dependencies_to_proxy():
    """
    Setting up all the dependecies (like sshtunner and pymysql)
    Compying the necessay files to the proxy: cluster_node_ids and the proxy_pattern.py
    """
    ip = ""
    dns = ""
    with open("proxy_ids.json", "r") as file:
        data = file.read()
        obj = json.loads(data)
        ip = obj["cluster_0"].get("ip")
        dns = obj["cluster_0"].get("dns")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 0)
    print(f"Connected through SSH! {ip}")
    _, stdout, _ = ssh.exec_command(
        "sudo apt update && sudo apt -y install python3-pip")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo pip3 install PyMySQL")
    print(stdout.read())
    _, stdout, _ = ssh.exec_command(
        "sudo pip3 install sshtunnel")
    print(stdout.read())
    ftp_client = ssh.open_sftp()
    ftp_client.put("proxy_pattern.py", "proxy_pattern.py")
    ftp_client.put("cluster_node_ids.json", "cluster_node_ids.json")
    ftp_client.put("labsuser.pem", "labsuser.pem")
    ftp_client.close()
    ssh.close()


def run_proxy():
    """
    The client (aka my computer) sends one write and one read request to the proxy
    """
    ip = ""
    with open("proxy_ids.json", "r") as file:
        data = file.read()
        obj = json.loads(data)
        ip = obj["cluster_0"].get("ip")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_connect_with_retry(ssh, ip, 0)
    print(f"Connected through SSH! {ip}")
    # read request ---> scroll to the right to check the parmeters 1. Query 2. Query type
    _, stdout, _ = ssh.exec_command(
        "sudo python3 proxy_pattern.py 'select last_name from actor group by last_name having count(*) = 1;' read")
    file = open(f"proxy-output/read_{ip}.txt", 'wb')
    file.write(stdout.read())
    # write request
    _, stdout, _ = ssh.exec_command(
        "sudo python3 proxy_pattern.py 'insert into rental (rental_date, inventory_id, customer_id, staff_id) values (NOW(), 2, 2, 2);' write")
    file = open(f"proxy-output/write_{ip}.txt", 'wb')
    file.write(stdout.read())
    ssh.close()


# Compying the files and adding the pip dependencies
copy_files_and_dependencies_to_proxy()
# Run the proxy with on read and one write request
run_proxy()
