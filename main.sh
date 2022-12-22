echo "please make sure you have the labsuser.pem file in the folder src/."
cd src
echo "setp one: creating all 6 instances"
python3 set_up.py
echo "setp two: setting up the sql cluster and stand alone mysql"
python3 mysql_set_up.py
echo "setup three: sending requests to the proxy"
python3 proxy_server.py
echo "don't forget to stop the instances and delete the scurity groupe"