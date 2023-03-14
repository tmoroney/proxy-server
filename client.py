import requests

s = requests.Session()

s.proxies = {
  'http': '127.0.0.1:8080',
  'https': '127.0.0.1:8080',
}

r = s.get('https://reqbin.com/echo')

print(f'Status Code: {r.status_code}')