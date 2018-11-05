from pyspark.sql import Row
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql.types import *
from pyspark.sql.functions import sum
from pyspark.sql.functions import col, asc
import datetime

Schema = StructType([
 	StructField("user_id", StringType()),
	StructField("sentiment", FloatType()),
	StructField("datetime", StringType()), 
	StructField("tweet_id", StringType()),
	StructField("sentence_line", IntegerType()), 
	StructField("sentence", StringType()),
	StructField("reply_to", StringType()), 
	StructField("location", StringType()),
	StructField("mentions", StringType()),
	StructField("retweet", StringType())])

SchemaTag = StructType([
 	StructField("tag", StringType()),
	StructField("datetime", StringType()),
	StructField("location", StringType()), 
	StructField("sentiment", FloatType()),
	StructField("userid", StringType()),
	StructField("tweetid", StringType()),
	StructField("sentence_line", StringType())])

def getSqlContextInstance(sparkContext):
    if ('sqlContextSingletonInstance' not in globals()):
        globals()['sqlContextSingletonInstance'] = SQLContext(sparkContext)
    return globals()['sqlContextSingletonInstance']

ssc = StreamingContext(sc, 10)
words = ssc.socketTextStream("172.31.7.237", 10000)

sqlContext.sql("""CREATE TEMPORARY TABLE tweets_by_sentence USING org.apache.spark.sql.cassandra OPTIONS (table "tweets_by_sentence",keyspace "cassandratweet", cluster "DSE Cluster",pushdown "true")""") 

sqlContext.sql("""CREATE TEMPORARY TABLE tag_sentiment USING org.apache.spark.sql.cassandra OPTIONS (table "tag_sentiment", keyspace "cassandratweet", cluster "DSE Cluster",pushdown "true")""")

def process(time, rdd):
	print "========= %s =========" % str(time)
    	try:
        		sqlContext2 = getSqlContextInstance(rdd.context)
        		words = rdd.map(lambda line: line.encode("ascii","ignore").split("~|,~"))
			words2 = words.flatMap( lambda line: [[x,line[0],line[1],line[2].split("@@^%").index(x),line[3],line[4],line[5],line[6],line[7]] for x in line[2].split("@@^%")] )
			words4 = words2.map(lambda line : [line[0].split("@@^^"),line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8]])
			words5 = words4.map(lambda l : (l[2],float(l[0][1]),l[5],l[1],int(l[3]),l[0][0],l[6],l[4],l[7],l[8]))
			wordsDataFrame = sqlContext2.createDataFrame(words5,Schema)
			wordsDataFrame.collect()
			wordsDataFrame.show()
			
			if (wordsDataFrame.count() != 0):
				print("Attempting Main Tweets DataFrame write")
				wordsDataFrame.write.format("org.apache.spark.sql.cassandra").options(table="tweets_by_sentence", keyspace = "cassandratweet").save(mode ="append")
				print("Succeeded.")
			
				words6 = words5.flatMap( lambda line: [[x.rstrip('?:!.,;'),line[2],line[7],line[1],line[0],line[3],line[4]] for x in line[5].split(" ")]).filter(lambda line : (len(line[0]) > 3) & (line[3] != 0) & (line[0][:4] != "http") & (line[0] != "this") & (line[0] != "that") & (line[0] != "than") & (line[0] != "about") & (line[0] != "from"))
				tagsDataFrame = sqlContext2.createDataFrame(words6,SchemaTag)
			
				if (tagsDataFrame.count() != 0):
					print("Attempting tags DataFrame write")
					tagsDataFrame.write.format("org.apache.spark.sql.cassandra").options(table="tag_sentiment", keyspace = "cassandratweet").save(mode ="append")
					print("Succeeded.")
			
   	except Exception, e:
       		print(str(e))
		pass

words.foreachRDD(process)
ssc.start()
ssc.awaitTermination() 
