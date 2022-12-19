from sshtunnel import SSHTunnelForwarder
import pymysql
import json


node_ids = []
node_dns = []
with open("collected_data.json", "r") as file:
    data = file.read()
    obj = json.loads(data)
    node_ids = [obj["cluster_1"].get("ip"), obj["cluster_2"].get("ip"),
                obj["cluster_3"].get("ip"), obj["cluster_4"].get("ip")]
    node_dns = [obj["cluster_1"].get("dns"), obj["cluster_2"].get("dns"),
                obj["cluster_3"].get("dns"), obj["cluster_4"].get("dns")]

with SSHTunnelForwarder(
    (node_ids[0], 22),  # public ip of slave
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
