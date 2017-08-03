import urllib
import json
import requests
import time
import re
import sqlite3
from math import sqrt

TOKEN = "432789513:AAGlAVSm7WdfWKEQgL6MsG8MBy6mxSdi_bE"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
	response = requests.get(url)
	content = response.content.decode("utf8")
	return content

def get_json_from_url(url):
	content = get_url(url)
	js = json.loads(content)
	return js

def get_updates(offset=None):
	url = URL + "getUpdates?timeout=100"
	if offset:
		url += "&offset={}".format(offset)
	js = get_json_from_url(url)
	return js

def get_last_update_id(updates):
	update_ids = []
	for update in updates["result"]:
		update_ids.append(int(update["update_id"]))
	return max(update_ids)

def get_last_chat_id_and_text(updates):
	num_updates = len(updates["result"])
	last_update = num_updates - 1
	text = updates["result"][last_update]["message"]["text"]
	chat_id = updates["result"][last_update]["message"]["chat"]["id"]
	return (text, chat_id)

def send_message(text, chat_id):
	import urllib.parse
	text = urllib.parse.quote_plus(text)
	url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
	get_url(url)

from dbhelper import DBHelper

db= DBHelper()

def main():
	connection, cursor = db.get_connection_and_cursor()
	last_update_id = None
	text = None
	chat_id = None
	B = 'Hello!'
	while True:
		print("getting updates")
		updates = get_updates(last_update_id)
		text, chat_id=get_last_chat_id_and_text(updates)
		text.strip()
		if text == '':
			break
		elif text == "/start":
			send_message("Hello, I am your new artificial friend.", chat_id)
		else:
			send_message(B, chat_id)
		words = db.get_words(B)
		words_length = sum([n * len(word) for word, n in words])
		sentence_id = db.get_id('sentence', text)
		for word, n in words:
			word_id = db.get_id('word', word)
			weight = sqrt(n / float(words_length))
			cursor.execute('INSERT INTO associations VALUES (?, ?, ?)', (word_id, sentence_id, weight))
		connection.commit()		
		cursor.execute('CREATE TEMPORARY TABLE results(sentence_id INT, sentence TEXT, weight REAL)')
		words = db.get_words(text)
		words_length = sum([n * len(word) for word, n in words])
		for word, n in words:
			weight = sqrt(n / float(words_length))
			cursor.execute('INSERT INTO results SELECT associations.sentence_id, sentences.sentence, ?*associations.weight/(4+sentences.used) FROM words INNER JOIN associations ON associations.word_id=words.rowid INNER JOIN sentences ON sentences.rowid=associations.sentence_id WHERE words.word=?', (weight, word,))
		cursor.execute('SELECT sentence_id, sentence, SUM(weight) AS sum_weight FROM results GROUP BY sentence_id ORDER BY sum_weight DESC LIMIT 1')
		row = cursor.fetchone()
		cursor.execute('DROP TABLE results')
		if row is None:
			cursor.execute('SELECT rowid, sentence FROM sentences WHERE used = (SELECT MIN(used) FROM sentences) ORDER BY RANDOM() LIMIT 1')
			row = cursor.fetchone()
		B = row[1]
		cursor.execute('UPDATE sentences SET used=used+1 WHERE rowid=?', (row[0],))
		if len(updates["result"]) > 0:
			last_update_id = get_last_update_id(updates) + 1
		time.sleep(0.5)

if __name__ == '__main__':
    main()