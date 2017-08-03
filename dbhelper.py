import sqlite3
import re

from collections import Counter
from string import punctuation

class DBHelper:
	connection = sqlite3.connect('chatbot.sqlite')
	cursor = connection.cursor()		
	
	def get_connection_and_cursor(self):
		return (DBHelper.connection,DBHelper.cursor)

	def create_tables():
		create_table_request_list = [
			'CREATE TABLE words(word TEXT UNIQUE)',
			'CREATE TABLE sentences(sentence TEXT UNIQUE, used INT NOT NULL DEFAULT 0)',
			'CREATE TABLE associations (word_id INT NOT NULL, sentence_id INT NOT NULL, weight REAL NOT NULL)',
		]
		for create_table_request in create_table_request_list:
			try:
				DBHelper.cursor.execute(create_table_request)
			except:
				pass

	def get_id(self, entityName, text):
		tableName = entityName + 's'
		columnName = entityName
		DBHelper.cursor.execute('SELECT rowid FROM ' + tableName + ' WHERE ' + columnName + ' = ?', (text,))
		row = DBHelper.cursor.fetchone()
		if row:
			return row[0]
		else:
			DBHelper.cursor.execute('INSERT INTO ' + tableName + ' (' + columnName + ') VALUES (?)', (text,))
			return DBHelper.cursor.lastrowid

	def get_words(self, text):
		wordsRegexpString = '(?:\w+|[' + re.escape(punctuation) + ']+)'
		wordsRegexp = re.compile(wordsRegexpString)
		wordsList = wordsRegexp.findall(text.lower())
		return Counter(wordsList).items()