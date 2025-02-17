from time import sleep

import openai
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, udf
from pyspark.sql.types import StructType, StructField, StringType, FloatType
from config.config import config

def sentiment_analysis(comment) -> str:
    if comment:
        openai.api_key = config['openai']['api_key']
        completion = openai.chat.completions.create(
            model=config['openai']['model_name'],
            messages=[
                {
                    "role": config['openai']['role'],
                    "content": """
                        {context}
                        
                        {comment}
                    """.format(context=config['openai']['context'],comment=comment)
                }
            ]
            #,
            # max_tokens=250, # Maximum number of tokens for the response.
            # temperature=0.7  # Adjust for more or less creative responses
        )
        return completion.choices[0].message.content
    return "Empty"

def start_streaming(spark):
    topic = 'customers_review'
   
    while True:
        try:
            # Streaming source
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
            
            sentiment_analysis_udf = udf(sentiment_analysis, StringType())

            stream_df = stream_df.withColumn('sentiment',
                                                when(col('text').isNotNull(), sentiment_analysis_udf(col('text')))
                                                .otherwise(None)
                                                )
            
            # query = stream_df.writeStream.outputMode("append").format("console").options(truncate=False).start()
            # query.awaitTermination()

            # Transform for Kafka (kafka_df)
            # Kafka requires the data to be in the form of key and value.
            # Both key and value must be of type STRING.
            kafka_df = stream_df.selectExpr("CAST(review_id AS STRING) AS key", "to_json(struct(*)) AS value")

            query = (kafka_df.writeStream.format("kafka") # writeStream.format("kafka") writes the DataFrame stream to the Kafka topic
                    .option("kafka.bootstrap.servers", config['kafka']['bootstrap.servers'])
                    #    .option("kafka.security.protocol", config['kafka']['security.protocol'])
                    #    .option('kafka.sasl.mechanism', config['kafka']['sasl.mechanisms'])
                    #    .option('kafka.sasl.jaas.config',
                    #            'org.apache.kafka.common.security.plain.PlainLoginModule required username="{username}" '
                    #            'password="{password}";'.format(
                    #                username=config['kafka']['sasl.username'],
                    #                password=config['kafka']['sasl.password']
                    #            ))
                    .option('checkpointLocation', '/tmp/checkpoint') # A directory for storing checkpoint data to ensure fault tolerance and exactly-once processing.
                    .option('topic', topic)
                    # .option("value.serializer", "org.apache.kafka.common.serialization.StringSerializer") \
                    # .option("key.serializer", "org.apache.kafka.common.serialization.StringSerializer") \
                    .option("kafka.metadata.fetch.timeout.ms", "120000")   # Increase metadata fetch timeout
                    .option("kafka.request.timeout.ms", "120000")         # Increase request timeout
                    .start() # method begins the streaming process
                    .awaitTermination() # method keeps the application running to continuously process the stream
                    )

        except Exception as e:
            print(f'Exception encountered: {e}. Retrying in 10 seconds')
            sleep(10)

if __name__ == "__main__":
    spark_conn = SparkSession.builder \
    .appName("SocketStreamConsumer") \
    .getOrCreate()
    # .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
    # .config("spark.sql.streaming.kafka.consumer.cache.enabled", "false") \
    # .getOrCreate()

    # spark_conn.sparkContext.setLogLevel("DEBUG")

    start_streaming(spark_conn)