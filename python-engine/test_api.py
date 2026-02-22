import requests

url = 'http://127.0.0.1:18432/api/voices/voice_male_01/preview'
headers = {'Content-Type': 'application/json'}
data = {}

response = requests.post(url, headers=headers, json=data)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type")}')
print(f'Content-Length: {len(response.content)}')

with open('D:\\test_preview27.wav', 'wb') as f:
    f.write(response.content)
print('Saved to D:\\test_preview27.wav')
