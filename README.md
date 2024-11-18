
## docker compose build and start the spark cluster
```
docker compose up --build -d
```


## run the streaming socket
```
docker exec -it spark-master /bin/bash
/opt/bitnami/spark# python jobs/streaming_socket.py 
```

## submit a job to spark master and run the spark streaming job
```
docker exec -it spark-master spark-submit \
--master spark://spark-master:7077 \
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
jobs/spark_streaming.py
```


## download the dataset from yelp and extract the JSON files into datasets directory
[Yelp.com/dataset](https://www.yelp.com/dataset/download)
