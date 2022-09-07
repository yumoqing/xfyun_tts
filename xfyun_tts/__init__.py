import os
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from appPublic.audioplayer import AudioPlayer
from appPublic.background import Background

from .version import __version__
from unitts.basedriver import BaseDriver
from unitts.voice import Voice
from websocket import WebSocketApp

import tempfile
import wave

def wavhead(wavfile, nchannels=1, framerate=16000):
	wf = wave.open(wavfile, 'wb')
	wf.setnchannels(nchannels)
	wf.setsampwidth(2)
	wf.setframerate(framerate)
	return wf

def temp_file(suffix='.txt'):
	x = tempfile.mkstemp(suffix=suffix)
	os.close(x[0])
	return x[1]

app_info = {}

def set_app_info(appid, appkey, appsecret):
	app_info.update({
		'appid':appid,
		'appkey':appkey,
		'appsecret':appsecret
	})

def buildDriver(proxy):
	return XFYunTTSDriver(proxy)

class XFYunTTSDriver(BaseDriver):
	def __init__(self, proxy):
		BaseDriver.__init__(self, proxy)
		self.ready = False
		self.APPID = app_info.get('appid')
		self.APIKey = app_info.get('appkey')
		self.APISecret = app_info.get('appsecret')
		self.CommonArgs = {"app_id":app_info.get('appid')}
		self.BusinessArgs = {
			"aue": "raw",
			"auf": "audio/L16;rate=16000", 
			"vcn": "xiaoyan", 
			"tte": "utf8"
		}
		self.player = AudioPlayer(on_stop=self.speak_finish)
		self.ws = websocket.WebSocket()
		self.ws.connect(self._ws_url() )

	def xfyun_tts(self, text, busi_params = {}):
		data = self.text_encode(text)
		d = {
			'common':self.CommonArgs,
			'business':self.BusinessArgs.copy().update(busi_params),
			'data':data
		}
		buf = json.dumps(d)
		self.ws.send(buf)
		audiofile = temp_file(suffix='.wav')
		self.wav_fd = wavhead(audiofile)
		d = self.ws.recv()
		while True:
			ret = self.on_message(d)
			print('ret=', ret)
			if ret == 'Done':
				return audiofile
			if ret == 'KeepGoing':
				d = self.ws.recv()
			else:
				return None


	def _ws_url(self):
		url = 'wss://tts-api.xfyun.cn/v2/tts'
		# 生成RFC1123格式的时间戳
		now = datetime.now()
		date = format_date_time(mktime(now.timetuple()))

		# 拼接字符串
		signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
		signature_origin += "date: " + date + "\n"
		signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
		# 进行hmac-sha256进行加密
		signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
								 digestmod=hashlib.sha256).digest()
		signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

		authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
			self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
		authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
		# 将请求的鉴权参数组合为字典
		v = {
			"authorization": authorization,
			"date": date,
			"host": "ws-api.xfyun.cn"
		}
		# 拼接鉴权参数，生成url
		url = url + '?' + urlencode(v)
		# print("date: ",date)
		# print("v: ",v)
		# 此处打印出建立连接时候的url,
		# 参考本demo的时候可取消上方打印的注释，比对
		# 相同参数时生成的url与自己代码生成的url是否一致
		# print('websocket url :', url)
		return url

	def text_encode(self, text):
		data = {
			"status": 2, 
			"text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
		}
		return data

	def on_message(self, message):
		try:
			message =json.loads(message)
			code = message["code"]
			sid = message["sid"]
			audio = message["data"]["audio"]
			audio = base64.b64decode(audio)
			status = message["data"]["status"]
			print(message)
			if code != 0:
				errMsg = message["message"]
				print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
				return 'ServerError'
			else:
				self.wav_fd.writeframes(audio)
			if status == 2:   # audio finish
				self.wav_fd.close()
				return 'Done'
			return 'KeepGoing'
		except Exception as e:
			print('receive msg, but parse exception:', e)
			return 'Except'

	def on_error(self, e):	
		print('ws error:', e)

	def on_close(self):
		print('### ws closed ###')

	def on_open(self, ws):
		self.ready = True

	def destroy(self):
		self.ws.close()		# stop the websocket
		self.player.unload()
		if self.task:
			self.running = False
			self.task.join()

	def pre_command(self, sentence):
		attrs = self.normal_voice
		if sentence.dialog:
			attrs = self.dialog_voice
		busi_params = {
			'vcn':attrs.get('voice', 'xiaoyan'),
			'speed':attrs.get('rate', 50),
			'pitch':attrs.get('patch', 50)
		}
		x = self.xfyun_tts(sentence.text, busi_params=busi_params)
		if x is None:
			return None, None
		return sentence.start_pos, x

	def command(self, pos, audiofile):
		print('pos=', pos, 'audiofile=', audiofile)
		self.player.set_source(audiofile)
		self.player.play()

	def stop(self):
		if self._proxy.isBusy():
			self._completed = False
		self.player.stop()

	def getProperty(self, name):
		if name == 'normal_voice':
			return self.normal_voice
		if name == 'dialog_voice':
			return self.dialog_voice

		if name == 'voices':
			return Voices

		if name == 'voice':
			for v in Voices:
				if v.id == self.voice:
					return v
			return None
		if name == 'rate':
			return self.rate
		if name == 'volume':
			return self.volume
		if name == 'pitch':
			return self.pitch

	def setProperty(self, name, value):
		if name == 'normal_voice':
			self.normal_voice = value
		if name == 'dialog_voice':
			self.dialog_voice = value
		if name == 'voice':
			self.voice = value
		if name == 'rate':
			self.rate = value
		if name == 'pitch':
			self.rate = value
		if name == 'language':
			self.language = value
		if name == 'volume':
			self.volume = value
