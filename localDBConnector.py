#!/usr/bin/python
# -*- coding: utf-8 -*-
import psycopg2
from psycopg2 import sql
import datetime
import time

class SQLConnector(object):

	def __init__(self,url):
		operation_complete = False
		while not operation_complete:
			try:
				self.database_url = url
				self.conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (url.path[1:], 
																						url.username, 
																						url.password, 
																						url.hostname))
				self.c = self.conn.cursor()
				self.c_execute("""SET client_encoding to 'UTF8'""")
				operation_complete = True
			except psycopg2.DatabaseError as e:
				print e     
				print "Database Error: Waiting 3 minutes from", datetime.datetime.now()
				time.sleep(180)
			except psycopg2.OperationalError as e:
				print e     
				print "Operational Error: Waiting 3 minutes from", datetime.datetime.now()
				time.sleep(180)  
				
	def __del__(self):
		self.conn.close()
		print 'Database connection closed'

	def c_execute(self, *args):
		operation_complete = False
		while not operation_complete:
			try:
				self.c.execute(*args)
				operation_complete = True
			except psycopg2.DatabaseError as e:
				print e
				print "Database Error: Closing Connection"
				print args
				self.conn.close()
				print "Database Error: Waiting 3 minutes from", datetime.datetime.now()
				#time.sleep(180)
				self.conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (self.database_url.path[1:],
																						 self.database_url.username,
																						 self.database_url.password,
																						 self.database_url.hostname))
				self.c = self.conn.cursor()
				self.c.execute("""SET client_encoding to 'UTF8'""")
				print "Reconnected to Database"
			except psycopg2.OperationalError as e:
				print e
				print "Operational Error: Closing Connection"
				print args
				self.conn.close()
				print "Operational Error: Waiting 30 minutes from", datetime.datetime.now()
				#time.sleep(1800)
				self.conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (self.database_url.path[1:],
																						 self.database_url.username,
																						 self.database_url.password,
																						 self.database_url.hostname))
				self.c = self.conn.cursor()
				self.c.execute("""SET client_encoding to 'UTF8'""")
				print "Reconnected to Database"

	def c_executemany(self, *args):
		operation_complete = False
		while not operation_complete:
			try:
				self.c.executemany(*args)
				operation_complete = True
			except psycopg2.DatabaseError as e:
				print e
				print "Database Error: Closing Connection"
				self.conn.close()
				print "Database Error: Waiting 3 minutes from", datetime.datetime.now()
				time.sleep(180)
				self.conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (self.database_url.path[1:], 
				                                                                         self.database_url.username, 
				                                                                         self.database_url.password, 
				                                                                         self.database_url.hostname))
				self.c = self.conn.cursor()
				self.c.execute("""SET client_encoding to 'UTF8'""")
				print "Reconnected to Database"
			except psycopg2.OperationalError as e:
				print e
				print "Operational Error: Closing Connection"
				self.conn.close()
				print "Operational Error: Waiting 3 minutes from", datetime.datetime.now()
				time.sleep(1800)
				self.conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (self.database_url.path[1:], 
				                                                                         self.database_url.username, 
				                                                                         self.database_url.password, 
				                                                                         self.database_url.hostname))
				self.c = self.conn.cursor()
				self.c.execute("""SET client_encoding to 'UTF8'""")
				print "Reconnected to Database"

	def commit(self):
		self.conn.commit()
		self.newCursor()

	def newCursor(self):
		self.c.close()
		self.c = self.conn.cursor()


	def createTrumpTweetsTable(self):        
		self.c.execute("""CREATE TABLE trump_tweets (
							id text,
							poster_handle text,
							created_at timestamp,
							tweet_text text,
							contributers text,
							in_reply_to_status_id text,
							tweet_source text,
							in_reply_to_screen_name text,
							retweet_count integer,
							favourite_count integer,
							url text,
							hashtag text,
							media_url text,
							UNIQUE(id))""")


	def insertIntoTrumpTweetsTable(self, 
										array):
		self.c.executemany("""INSERT OR REPLACE INTO trump_tweets
								VALUES (%s,%s,%s,%s,%s,
										%s,%s,%s,%s,%s,
										%s,%s,%s)""", array) 

	def getAllTrumpTweetsData(self):
		self.c.execute("""SELECT * 
							FROM trump_tweets""") 
		try:
			return self.c.fetchall()
		except TypeError:
			print 'There are no records in the Trump Tweets database table'
			return False  


	def getTrumpTweetsData(self,
							keywords=None,
							start_date=datetime.datetime(2010,1,1),
							end_date=None):

		if end_date is None:
			end_date=datetime.datetime.now()

		if keywords:
			parsed_keywords = '%'+keywords+'%'
			self.c.execute("""SELECT * 
					 FROM trump_tweets
					 WHERE created_at > %s 
					 AND created_at < %s 
					 AND tweet_text LIKE %s
					 ORDER BY created_at""",[start_date,end_date,parsed_keywords]) 
		else:
			self.c.execute("""SELECT * 
					 FROM trump_tweets
					 WHERE created_at > %s 
					 AND created_at < %s 
					 ORDER BY created_at""",[start_date,end_date]) 
		return self.c.fetchall()

