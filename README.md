# TWITTER SENTIMENT

This project is a simple yet powerful illustration of several components of the DataStax Enterprise Database.

You will connect in to a real time Twitter API feed and using **DSE Real-Time Streaming Analytics** ingest tweets and do some simple transformations before saving to 2 tables in DSE. Then Banana Dashboard will take advantage of **DSE Search** capabilities to provide a view into the real time data flowing into DSE; Facilitating adhoc searches to explore and 'slice & dice' this data. Finally, using **DSE Analytics for batch processing** via DSE GraphFrames, this data will be transformed into a Graph structure and loaded into **DSE Graph** - where **DSE Studio** can be used to visualize the Twitter Sentiment data.

The steps that follow assume you have an up and running DSE Node / Cluster (v5.1.3+), Python is installed and banana dashboard has been cloned to a node (https://github.com/lucidworks/banana)

Steps
=====

1. Using cqlsh, run the **schema.cql** file to create the TwitterSentiment Data Model as well as the Data Model to store data for the Banana Dashboard.

2. Upload or clone banana directory to a node in the cluster and unzip if required,

> tar -xvf banana.demo.tar.gz

3. Copy default.json file to \<download location\>/banana/src/app/dashboards/ overwriting any existing file.

4. Copy "**banana**" folder to **$DSE_HOME/resources/banana** (tarball install) or **/etc/dse/banana** (repo install) and then restart Node.

5. Update **$DSE_HOME/resources/tomcat/conf/server.xml** (tarball install) or **/etc/dse/tomcat/conf/server.xml** (repo install), adding the following inside the \<Host\> tags and put the absolute path to banana/src in the docBase value,
  
>  \<Context docBase="/etc/dse/banana/src" path="/banana" /\>

6. Once the node is back up and running, go to the URL: 

>  \<node ip address\>:8983/banana 
  
7. In the top right of the dashboard click the cog icon (configure), select the "Solr" tab and then in global settings enter,

>  &useFieldCache=true 

8. At the command line execute the following command,

```
sudo pip install -U textblob
sudo pip install -U tweepy
```

9. Using python, execute the following commands,

```
import nltk
nltk.download('punkt')
```

10. Execute the Twitter API (which will startup and go into a waiting mode ready to accept an incoming connection),

```
python stream_tweets_server.py
```
 
11. Using another terminal, go into the DSE PySpark REPL by issuing this command,

```
dse pyspark
```

12. Update the ip address & port as required and copy and paste the text from the **pyspark_script.py** script to execute in the repl.

13. Check that DSE Analytics has connected into the stream_tweets_server and that tweets are streaming in real time and that in the pyspark repl dataframes with twitter data are being created and saved to DSE.

14. Goto the Banana dashboard and view the data flowing into DSE in real time.


Loading Twitter data into DSE Graph
===================================

Once you have collected a sufficient amount of data it would now be usefull to load some of this into DSE Graph so that it can be visualized and Gremlin Traversals can be executed against the graph data.

Using DSE Studio, create a new connection to your cluster and create a new Graph. Inside the notebook create the necessary schema,

```
schema.propertyKey('userid').Text().ifNotExists().create()
schema.propertyKey('theuserid').Text().ifNotExists().create()
schema.propertyKey('thetweetid').Text().ifNotExists().create()
schema.propertyKey('language').Text().ifNotExists().create()
schema.propertyKey('location').Text().ifNotExists().create()
schema.propertyKey('tweetid').Text().ifNotExists().create()

schema.propertyKey('createdtime').Timestamp().ifNotExists().create()
schema.propertyKey('createdtimelong').Bigint().ifNotExists().create()
schema.propertyKey('sentenceline').Int().ifNotExists().create()
schema.propertyKey('thesentenceline').Int().ifNotExists().create()
schema.propertyKey('sentence').Text().ifNotExists().create()
schema.propertyKey('sentiment').Double().ifNotExists().create()
schema.propertyKey('tagword').Text().ifNotExists().create()
schema.propertyKey('thetagword').Text().ifNotExists().create()
schema.propertyKey('countryname').Text().ifNotExists().create()
schema.propertyKey('thecountryname').Text().ifNotExists().create()

// Vertex labels
schema.vertexLabel('user').partitionKey('userid').properties('theuserid','location').ifNotExists().create()
schema.vertexLabel('country').partitionKey('countryname').properties('thecountryname').ifNotExists().create()
schema.vertexLabel('tweet').partitionKey('tweetid').create()
schema.vertexLabel('tweet').properties('thetweetid','createdtime').add()
schema.vertexLabel('sentence').partitionKey('tweetid').clusteringKey('sentenceline').properties('thetweetid','thesentenceline','sentence','sentiment').ifNotExists().create()
schema.vertexLabel('tag').partitionKey('tagword').properties('thetagword').ifNotExists().create()

// Edge labels
schema.edgeLabel('tweeted').connection('user', 'tweet').ifNotExists().create()
schema.edgeLabel('mentions').connection('tweet', 'user').ifNotExists().create()
schema.edgeLabel('repliedto').connection('tweet', 'user').ifNotExists().create()
schema.edgeLabel('retweeted').connection('tweet', 'user').ifNotExists().create()
schema.edgeLabel('containstag').properties('sentiment').connection('sentence', 'tag').ifNotExists().create()
schema.edgeLabel('containssentence').connection('tweet', 'sentence').ifNotExists().create()
schema.edgeLabel('residesin').connection('user', 'country').ifNotExists().create()

// Indexes
schema.vertexLabel('tweet').index('tweetCreatedTime').materialized().by('createdtime').ifNotExists().add()
schema.vertexLabel('tweet').index("toSentenceBySentiment").outE("containssentence").by("sentiment").ifNotExists().add();
schema.vertexLabel('sentence').index("toTagBySentiment").outE("containstag").by("sentiment").ifNotExists().add();
```

To batch load the Twitter data into graph go into the Spark Scala REPL,

```
dse spark
```

Then copy paste the contents of **scala_loadgraph_script.txt** (amend the graph name accordingly) into the REPL. This will take a few minutes to execute.

Once complete you can use DSE Studio to execute traversals and visualize the Twitter Sentiment Data!
