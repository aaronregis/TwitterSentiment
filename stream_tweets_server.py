#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import socket
import sys
import json
from textblob import TextBlob
from time import gmtime, strftime

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    tweet_list = []

    def on_data(self, data):
        self.tweet_list.append(data)
        if len(self.tweet_list) >= 10:
            self.process_tweet_list()
        return True

    def process_tweet_list(self):
        ImportToCassandra().process_tweet_list(self.tweet_list)
        self.tweet_list = []

    def on_error(self, status):
        print status

class ImportToCassandra:
    def process_tweet_list(self, list):

        for data in (list):
                try:
                    data = json.loads(data)
                    user_id = data['id']
                    user_name = data['user']['screen_name']
                    tweet = data['text']
		    #create_date = data['created_at']
		    create_date = strftime("%Y-%m-%d %H:%M:%S+0000", gmtime())
                   
		    mentions = ""
 
		    try:
			location = data['user']['location']
		    	in_reply_to = data['in_reply_to_screen_name'].replace('None','')

			for doc in data['entities']['user_mentions']:
				mentions = mentions + doc['screen_name'] + " "
		    except:
			location = ""
			in_reply_to = ""
			mentions = ""
 	
		    twt = "" 
		    tweet = tweet.replace('\n', '. ').replace('\r', '').replace('|', '').replace('"','')
		    blob = TextBlob(tweet)		    

	 	    for sentence in blob.sentences:

			twt = twt + str(sentence)+"@@^^"+str(sentence.sentiment.polarity)+"@@^%"  

		    if len(twt) > 4:
			tweet = twt[:-4]
			
		    textToStream = str(user_id)+"~|,~"+str(user_name)+"~|,~"+str(tweet)+"~|,~"+str(location)+"~|,~"+str(create_date)+"~|,~"+str(in_reply_to)+"~|,~"+str(mentions.strip())+"~|,~"+"\n"
		    textToStream = textToStream.lower()
		    
		    try :
    			connection.sendall(textToStream)
		    except socket.error:
    		      	print 'Send failed'
		    
                    #connection.sendall(textToStream)
                    print textToStream 
                except:
		    print "exception!"
                    pass

        #session.execute(batch)

class startStreaming:
    def letsGo(self):
	if __name__ == '__main__':

	    #Variables that contains the user credentials to access Twitter API
	    access_token = "<enter your access token here>"
	    access_token_secret = "<enter your access token secret here>"
	    consumer_key = "<enter your consumer key here>"
	    consumer_secret = "<enter your consumer secret here>"

            #This handles Twitter authetification and the connection to Twitter Streaming API
            l = StdOutListener()
            auth = OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            stream = Stream(auth, l)

            #This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
	
            print "Successfully logged into Twitter and listening.."
            #stream.filter(track=['couchbase','apache','datamanagement','nosql', 'mongodb', 'datastax', 'bigdata', 'hadoop', 'neo4j', 'titandb'])
	    stream.filter(track=['tories','labour','brexit','corbyn', 'conservatives', 'ukip', 'libdems', 'trump','farage'])
	    #stream.filter(track=['ucl','champsleague','championsleague','prem','epl','laliga','seriea','facup','worldcup','premierleague','soccer'])



# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('192.168.0.40', 10000)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()

    try:
        print >>sys.stderr, 'connection from', client_address

        # Receive the data in small chunks and retransmit it
        while True:
                #connection.sendall(data)
                startStreaming().letsGo()

    finally:
        # Clean up the connection
        connection.close()
