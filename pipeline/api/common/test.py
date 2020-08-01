from dynamodb import map_keys

items = map_keys([{
    "rqrmntsTxt": "amazon.ion==0.5.0\nboto3==1.14.28\nbotocore==1.17.28\ndocutils==0.15.2\nionhash==1.1.0\njmespath==0.10.0\npyqldb==2.0.2\npython-dateutil==2.8.1\ns3transfer==0.3.3\nsix==1.15.0\nurllib3==1.25.10"
}])

print(items)