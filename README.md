# xfyun_tts 
this is a tts driver using [xfyun](https://xfyun.cn) for unitts

## Dependent

* [websocket-client](https://pypi.org/project/websocket-client)
* [apppublic](https://pypi.org/project/apppublic)

## Installation
```
pip install xfyun_tts
```

## Usage

in the beginning, 
```
from xfyun_tts import set_app_info
import unitts

set_app_info(appid, apikey, apisecret)
tts = unitts.init('xfyun_tts')

tts.say('hello xfyun')
tts.startLoop()
tts.endLoop()
```

