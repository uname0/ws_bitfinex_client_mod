#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import websocket
import ssl

import json
import requests
import sys


HEADERS = {'user-agent': 'python-developer'} 
CHANID_PAIR = {}
TMP = {}



def load_config(config_filename):
	with open(config_filename, 'r') as fd:
		json_data = json.loads(fd.read())

	return json_data


def ws_subscribe_ticker(ws, pair):
	req = {}
	req["event"] = "subscribe"
	req["channel"] = "ticker"
	req["pair"] = pair

	ws.send(json.dumps(req))
	
	return req


def dict_event(recv):
	global CHANID_PAIR
	global TMP

	CHANID_PAIR[recv.get("chanId")] = recv.get("pair")
	TMP[recv.get("chanId")] = 0



def list_event(recv, price_type, to_url, login_info):
	global TMP

	if recv[1] != 'hb':
		chanId = recv[0]

		#print("\nreceived:\n{}".format(recv))

		# {"code":"код пары", "quote": актуальная цена}
		payload = {}
		payload["code"] = CHANID_PAIR.get(chanId)

		if price_type == "BID":
			payload["quote"] = recv[1]
		elif price_type == "ASK":
			payload["quote"] = recv[4]
		elif price_type == "LAST_PRICE":
			payload["quote"] = recv[7]
		else:
			print("[!] Error: unknown price_type: {}".format(price_type))
			sys.exit(1)


		if payload["quote"] != TMP.get(chanId):
			#print("\npost request to {}:\n{}\nprice_type: {}\n".format(to_url, payload, price_type))

			r = requests.post(to_url, headers=HEADERS, json=payload, auth=login_info)

			#print("\nresponse from {}:".format(to_url))
			#print(r.status_code)
			#print(r.headers)
			#print(r.text)
			print("[+] {} - post request to srv({})".format(payload, r.status_code))
		else:
			#print("{} = {}".format(payload["quote"], TMP.get(chanId)))
			print("[-] {} = {}".format(payload.get("quote"), TMP.get(chanId)))


		TMP[chanId] = payload["quote"]

		#print("\n\n###")

	else:
		print("[*] {} - hb".format(recv[0]))



def handler(ssl_uri, to_url, login_info, pairs, price_type):
	try:
		print('connect to {}'.format(ssl_uri))
		
		ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
		ws.connect(ssl_uri)

		print(ws.recv())

		for pair in pairs:
			req = ws_subscribe_ticker(ws, pair)
			print(req)

		print("\nall pairs: {}".format(pairs))
		print("price type: {}".format(price_type))
		print("post requests to this server: {}".format(to_url))

		print('\n\trecv:\n\n')

		while True:
			recv = eval(ws.recv())

			if type(recv) == type({}):
				dict_event(recv)
			elif type(recv) == type([]):
				list_event(recv, price_type, to_url, login_info)


	except KeyboardInterrupt:
		print("\nexit\n")

	except Exception as err:
		print('\nsome error:\n{}\n'.format(err))


def main():
	res = load_config('config_tcl.json')

	ssl_uri = res.get('ssl_uri')
	to_url = res.get('to_url')
	login_info = (res.get('login'), res.get('pass'))

	pairs = res.get('pairs')
	price_type = res.get('price_type')

	handler(ssl_uri, to_url, login_info, pairs, price_type)



if __name__ == "__main__":
	main()
