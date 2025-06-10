import requests
import json

url = 'http://9.135.166.211:8280/cgi-bin/api/llm_plug/chat_no_stream'
params = {
'x-timestamp': '1723113102',
'x-sa-v': '3',
'x-appid': 'snp',
'x-sa-sign': '1234567890'
}
headers = {
'Content-Type': 'application/json'
}
data = {
'meta': {
'platform': 'lily',
'model': 'deepseek'
},
'input': {
'messages': ['东方集团退市股票怎么办']
}
}

response = requests.post(url, headers=headers, params=params, data=json.dumps(data))

print(response.text)
print(json.loads(response.text)['result'])

