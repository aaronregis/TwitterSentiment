#Import the necessary methods from tweepy library
from __future__ import print_function
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import socket
import sys
import json
from textblob import TextBlob
from time import gmtime, strftime
import argparse
import traceback
import os

def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, handler):
        super(StdOutListener, self).__init__()
        self.handler = handler

    def on_status(self, status):
        self.handler.process_tweet_list(status)
        return True

    def on_error(self, status):
        print(status)

class ServerHandler:
    def __init__(self, args):
        self.args = args
        self.connections = []
    
    def startTwitter(self):
        #Variables that contains the user credentials to access Twitter API
        access_token = self.args.access_token or os.environ.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = self.args.access_secret or os.environ.get('TWITTER_ACCESS_SECRET')
        consumer_key = self.args.consumer_key or os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = self.args.consumer_secret or os.environ.get('TWITTER_CONSUMER_SECRET')
        if access_token_secret is None or access_token is None or consumer_key is None or consumer_secret is None:
            print("Access token/secret or consumer key/secret isn't specified!")
            return False
        
        #This handles Twitter authetification and the connection to Twitter Streaming API
        l = StdOutListener(self)
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.stream = Stream(auth, l)
        
        errprint("Successfully logged into Twitter and listening..")
        languages = self.args.languages
        if (languages is not None):
            languages = languages.split(',')
        if self.args.mode == 'terms':
            terms = self.args.terms.split(',')
            errprint("Going to listen for following terms: " + str(terms))
            self.stream.filter(track=terms, is_async=True, languages=languages)
        else:
            errprint("Going to listen for sampled stream")
            self.stream.sample(is_async=True, languages=languages)

        return True

    def startServer(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        server_address = (self.args.address, self.args.port)
        errprint('starting up on %s port %s' % server_address)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(server_address)

        # Connect to Twitter
        if (not self.startTwitter()):
            print("Can't start Twitter stream!")
            return

        # Listen for incoming connections
        sock.listen(1)

        while True:
            # Wait for a connection
            errprint('waiting for a connection')
            try:
                connection, client_address = sock.accept()

                errprint('connection from ' + str(client_address))
                self.connections.append(connection)
            except KeyboardInterrupt:
                errprint("Got Ctrl-C, exiting...")
                self.stream.disconnect()
                for connection in self.connections:
                    connection.close()
                return

    def process_tweet_list(self, status):
        try:
            user_id = status.id
            user_name = status.user.screen_name
            tweet = status.text
            #create_date = data['created_at']
            # TODO: use data from tweet itself...
            create_date = strftime("%Y-%m-%d %H:%M:%S+0000", gmtime())
                
            mentions = ""
 
            try:
                location = status.user.location
                in_reply_to = str(status.in_reply_to_screen_name).replace('None','')

                for doc in status.entities['user_mentions']:
                    mentions = mentions + doc['screen_name'] + " "
                mentions.strip()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                errprint("data exception! " + str(e) + ", data=" + str(status))
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

            conLen = len(self.connections)
            current = 0
            while current < conLen:
                connection=self.connections[current]
                try :
                    connection.sendall(textToStream.encode('utf-8'))
                    current = current + 1
                except KeyboardInterrupt:
                    raise
                except socket.error:
                    errprint('Send failed! Removing this connection from list of connections...')
                    del self.connections[current]
                    conLen = conLen - 1
                    
            print(textToStream)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            errprint("exception! " + str(e)  + ", data=" + str(status))
            traceback.print_exc()
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="terms", choices=['terms','sample'])
    parser.add_argument("--terms", default=None, type=str,
                        help="comma-separated list of terms to fetch. Required when --mode is 'terms'")
    parser.add_argument("--address", default="127.0.0.1", type=str, help = "Address to listen on")
    parser.add_argument("--port", default=10000, type=int, help="Port to listen on")
    parser.add_argument("--access-token", type=str, dest='access_token', help="Twitter's access token")
    parser.add_argument("--access-secret", type=str, dest='access_secret', help="Twitter's access token secret")
    parser.add_argument("--consumer-key", type=str, dest='consumer_key', help="Twitter's consumer key")
    parser.add_argument("--consumer-secret", type=str, dest='consumer_secret', help="Twitter's consumer secret")
    parser.add_argument("--languages", type=str, help="Comma-separated list of languages to handle")

    args = parser.parse_args()
    if args.mode == 'terms' and args.terms is None:
        errprint("--terms is required when 'terms' mode is used!")
        parser.print_help()
        exit(1)
    handler = ServerHandler(args)
    handler.startServer()

if __name__ == "__main__":
    main()
