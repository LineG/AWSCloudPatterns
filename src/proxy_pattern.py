from sshtunnel import SSHTunnelForwarder
import pymysql
import json
import random
import os
import time
import sys


# Reading the node ids and dns from the file cluster_node_ids
# The file was transfered to the proxy during the set up
node_ids = []
node_dns = []
with open("cluster_node_ids.json", "r") as file:
    data = file.read()
    obj = json.loads(data)
    node_ids = [obj["cluster_1"].get("ip"), obj["cluster_2"].get("ip"),
                obj["cluster_3"].get("ip"), obj["cluster_4"].get("ip")]
    node_dns = [obj["cluster_1"].get("dns"), obj["cluster_2"].get("dns"),
                obj["cluster_3"].get("dns"), obj["cluster_4"].get("dns")]


def direct_hit_master(query):
    """
    Directly uses pymysql to hit master
    query: the quesry to perform on the master mysql
    """
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
            sql = query
            cursor.execute(sql)
            result = cursor.fetchone()
            print(result)

        connection.commit()


def random_hit(query):
    """
    Choses a random integer that will be thw index of the server to hit
    From Global var node_ids
    query: the query to perform on the cluster
    """
    print("Hitting servers in the cluster at random")
    to_hit = random.randint(0, 3)
    # Direct hit to master
    print(f"We are hitting {to_hit}")
    with SSHTunnelForwarder(
        # sets the id to hit to the id of the random hit
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
                sql = query
                cursor.execute(sql)
                result = cursor.fetchone()
                print(result)

            connection.commit()


def get_fastest_ping():
    """
    measures the ping time of all the servers in the cluster
    return: fastest ping time
    """
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


def ping_time_request(query):
    """
    Measures the ping time of each server (master and 3 nodes)
    Choses the fastest one 
    query: the query to perform on the cluster
    """
    fastest_ping = get_fastest_ping()
    print(
        f"We are hitting the the server with the fastest ping response: {fastest_ping}")
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
                sql = query
                cursor.execute(sql)
                result = cursor.fetchone()
                print(result)

            connection.commit()


# Global var for read and write
READ_REQUEST = "read"
WRITE_REQUEST = "write"


def dispatch_request(request, query):
    """
    method that dispatches the query request based on the request type and the query
    request: read or write
    query: the SQL query
    """
    if WRITE_REQUEST == request:
        print("This is a write request so we hit the master directly.")
        direct_hit_master(query)
    elif READ_REQUEST == request:
        print("This is a read request so we can hit the slaves too.")
        random_hit(query)
        direct_hit_master(query)
        ping_time_request(query)


# DEFAULT values just in case nothing is sent through the command
# (look at the file proxy_server line 75 and 78 to see query examples)
query = 'SELECT COUNT(*) FROM film_text;'
wr = WRITE_REQUEST
# Taking the first two agrument sent by the client
# We assume that the client and the server have a convention set
query = sys.argv[1]
wr = sys.argv[2]

# Proxy dispatches the request based on the type
# if write --> to master direct hit
# if read --> direct hit or random hit or fastest ping time
# (For the context of the lab when we have a read we are calling all three methods)
dispatch_request(wr, query)
