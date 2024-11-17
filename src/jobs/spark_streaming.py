from time import sleep

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, FloatType


def start_streaming(spark):
   
    try:
        stream_df = (spark.readStream.format("socket")
                        .option("host", "localhost")
                        .option("port", 9999)
                        .load()
                    )
        
        schema = StructType([
                StructField("review_id", StringType()),
                StructField("user_id", StringType()),
                StructField("business_id", StringType()),
                StructField("stars", FloatType()),
                StructField("date", StringType()),
                StructField("text", StringType())
            ])

        # when the data comes in thru the stream, it has the JSON data under the column 'value'
        # get the JSON data from 'value' column and map it to the schema
        # put the JSON data in the alias 'data' (similar to SQL)
        # select all the records from the alias 'data'
        stream_df = stream_df.select(from_json(col('value'), schema)
                                    .alias("data")
                                    ).select(("data.*"))
        
        query = stream_df.writeStream.outputMode("append").format("console").options(truncate=False).start()
        query.awaitTermination()



    except Exception as e:
        print(f'Exception encountered: {e}. Retrying in 10 seconds')
        sleep(10)

if __name__ == "__main__":
    spark_conn = SparkSession.builder.appName("SocketStreamConsumer").getOrCreate()

    start_streaming(spark_conn)