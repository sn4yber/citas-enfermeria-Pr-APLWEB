import urllib.request
import json

# Login as admin to get token
data = json.dumps({"email": "admin@admin.com", "password": "admin"}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/token/', data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())['access']
    print("Got token")
except Exception as e:
    print("Failed to login as admin", e)
    # let's try getting medicos to see their IDs without token
    pass

req = urllib.request.Request('http://localhost:8000/api/medicos/')
resp = urllib.request.urlopen(req)
medicos = json.loads(resp.read())
print("Medicos:")
for m in medicos:
    print(m)

