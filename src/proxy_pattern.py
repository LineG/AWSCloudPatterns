from sshtunnel import SSHTunnelForwarder
import pymysql
import json
import random
import os
import time

node_ids = []
node_dns = []
with open("cluster_node_ids.json", "r") as file:
    data = file.read()
    obj = json.loads(data)
    node_ids = [obj["cluster_1"].get("ip"), obj["cluster_2"].get("ip"),
                obj["cluster_3"].get("ip"), obj["cluster_4"].get("ip")]
    node_dns = [obj["cluster_1"].get("dns"), obj["cluster_2"].get("dns"),
                obj["cluster_3"].get("dns"), obj["cluster_4"].get("dns")]


def direct_hit_master():
    # No need for the ssh tunner just forward the read request to master
    print("****SSH Tunnel Established****")
    print(f"We are makinf a sql request to master directrly {node_ids[0]}")
    connection = pymysql.connect(host=node_ids[0],  # public dns of master
                                 user="myapp",
                                 password='MyNewPass',
                                 port=3306)
    with connection:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "USE sakila;"
            cursor.execute(sql)
            sql = "SELECT COUNT(*) FROM film_text;"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(result)

        connection.commit()


def random_hit():

    print("Hitting servers in the cluster at random")
    to_hit = random.randint(0, 3)
    # Direct hit to master
    print(f"We are hitting {to_hit}")
    with SSHTunnelForwarder(
        (node_ids[to_hit], 22),  # public ip of slave
        ssh_username="ubuntu",
        ssh_pkey="labsuser.pem",
        remote_bind_address=(
            node_dns[0], 3306),  # private dns of the master
    ) as tunnel:
        print("****SSH Tunnel Established****")
        connection = pymysql.connect(host=node_ids[0],  # public dns of master
                                     user="myapp",
                                     password='MyNewPass',
                                     port=3306,
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "USE sakila;"
                cursor.execute(sql)
                sql = "SELECT COUNT(*) FROM film_text;"
                cursor.execute(sql)
                result = cursor.fetchone()
                print(result)

            connection.commit()


def get_fastest_ping():
    best_time = -1
    fastest = node_ids[0]
    for host in node_ids:
        start = time.time()
        os.system(f"ping {host} -c 2")
        end = time.time()
        time_to_respond = end - start
        if time_to_respond > best_time:
            best_time = time_to_respond
            fastest = host
    return fastest


def ping_time_request():
    print(
        f"We are hitting the the server with the fastest ping response: {fastest_ping}")
    fastest_ping = get_fastest_ping()
    # Direct hit to master
    with SSHTunnelForwarder(
        (fastest_ping, 22),  # public ip of slave
        ssh_username="ubuntu",
        ssh_pkey="labsuser.pem",
        remote_bind_address=(
            node_dns[0], 3306),  # private dns of the master
    ) as tunnel:
        print("****SSH Tunnel Established****")
        connection = pymysql.connect(host=node_ids[0],  # public dns of master
                                     user="myapp",
                                     password='MyNewPass',
                                     port=3306,
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "USE sakila;"
                cursor.execute(sql)
                sql = "SELECT COUNT(*) FROM film_text;"
                cursor.execute(sql)
                result = cursor.fetchone()
                print(result)

            connection.commit()


random_hit()
direct_hit_master()
ping_time_request()
