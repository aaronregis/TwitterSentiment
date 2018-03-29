CREATE KEYSPACE cassandratweet WITH replication = {'class': 'NetworkTopologyStrategy', 'dc1': '1'}  AND durable_writes = true;


CREATE TABLE cassandratweet.tweets_by_sentence_graph (
    user_id text,
    sentiment float,
    datetime timestamp,
    tweet_id text,
    sentence_line int,
    location text,
    reply_to text,
    mentions text,
    retweet text,
    sentence text,
    PRIMARY KEY (user_id, tweet_id, datetime, sentence_line)
) WITH CLUSTERING ORDER BY (tweet_id desc, datetime desc,  sentence_line ASC);

CREATE TABLE cassandratweet.tag_sentiment_graph (
    tag text,    
    tweetid text,
    sentence_line int,
    datetime timestamp,
    userid text,
    location text,
    sentiment float,
    PRIMARY KEY (tag, datetime, userid,tweetid, sentence_line)
) WITH CLUSTERING ORDER BY (datetime DESC, userid ASC, tweetid asc, sentence_line asc);

CREATE SEARCH INDEX ON cassandratweet.tag_sentiment_graph  WITH COLUMNS * { docValues:true };

CREATE KEYSPACE banana WITH replication = { 'class': 'NetworkTopologyStrategy', 'dc1': 1};
CREATE TABLE banana.dashboards (
id text PRIMARY KEY,
"_version_" bigint,
dashboard text,
group text,
solr_query text,
title text,
user text
);

CREATE SEARCH INDEX ON banana.dashboards  WITH COLUMNS * { docValues:true };
