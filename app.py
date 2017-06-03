import gspread
from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask,jsonify,request
import json

from time import time

import re
app = Flask(__name__)

def getgspread():
	scope = ['https://spreadsheets.google.com/feeds']
	credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
	gc = gspread.authorize(credentials)
	print "Connecting to gspread"
	return gc

def setup_app(app):
	try:
		gc = getgspread()
		wks = gc.open('BF_Template').sheet1
		return wks
	except Exception as e:
		print(e)
		return None
wks = setup_app(app)

def dataFormatter(code,message,data):
	resp = jsonify({
			'code':code,
			'message':message,
			'data':data
		})
	resp.status_code=code
	return resp

@app.route('/validate',methods=['GET','POST'])
def getCode():
	if request.method == 'GET':
		if request.args:
			keys = request.args.keys()
			if len(keys) is 1 and keys[0] == 'phone':
				phone = request.args.get('phone')
				if validatePhone(phone):
					if wks:
						phone_list = wks.col_values(3)
					else: 
						return dataFormatter(500,'Could not connect to database',[])
					if phone not in phone_list:
						i = emptyslot(phone_list)
						wks.update_cell(i+1,3,phone)
						code = wks.cell(i+1,2).value
						return dataFormatter(200,'Phone number registered successfully',[code])
					else:
						i = phone_list.index(phone)
						code = wks.cell(i+1,2).value
						return dataFormatter(409,'Phone number already used',[code])
				else:
					return dataFormatter(400,'Invalid phone number',[])
			else:
				return dataFormatter(400,"Bad Request",[])
		else:
			return dataFormatter(422,"No request parameter",[])
	else:
		return dataFormatter(405,'Wrong request type',[])

def validatePhone(phone):
	if not phone or re.search('[a-zA-Z]',phone):
		return False
	return True

def emptyslot(phone_list):
	for i,val in enumerate(phone_list):
		if not val:
			break
	return i


if __name__ == '__main__':
	app.run(host='0.0.0.0',debug = True)
