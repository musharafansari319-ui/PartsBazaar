import os, requests, json
from flask import Flask, request
import gspread

app = Flask(__name__)

GEMINI_KEY = os.environ['GEMINI_KEY']
SHEETS_KEY = os.environ['SHEETS_KEY']
SHEET_ID = os.environ['SHEET_ID']
WA_TOKEN = os.environ['WA_TOKEN']
PHONE_ID = os.environ['PHONE_ID']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']

def get_inventory():
  gc = gspread.api_key(SHEETS_KEY)
  sh = gc.open_by_key(SHEET_ID)
  return sh.sheet1.get_all_records()

def ask_gemini(user_msg, inventory):
  inv_text = '\n'.join([
    f"{r['part_name']} | {r['variant']} | Rs.{r['price']} | Stock:{r['stock_qty']}"
    for r in inventory
  ])
  prompt = f"""Aap Parts Dukan AI assistant hain Pakistan mein.
Roman Urdu aur English mix mein reply karein. Short rakhen.
Inventory:\n{inv_text}\n
Rules:
- Jab panel pucha jaye, sab variants dikhao with prices
- Out of stock ho to sorry kaho aur restock time batao
- Friendly raho jaise local dukaan
- Typos samjho (batry=battery, panl=panel, iphon=iphone)

Customer: {user_msg}"""
  r = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
    json={{"contents":[{{"parts":[{{"text":prompt}}]}}]}}
  )
  return r.json()['candidates'][0]['content']['parts'][0]['text']

def send_whatsapp(to, text):
  requests.post(
    f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages",
    headers={{"Authorization":f"Bearer {WA_TOKEN}","Content-Type":"application/json"}},
    json={{"messaging_product":"whatsapp","to":to,"type":"text","text":{{"body":text}}}}
  )

@app.route('/webhook', methods=['GET'])
def verify():
  if request.args.get('hub.verify_token') == VERIFY_TOKEN:
    return request.args.get('hub.challenge')
  return 'Invalid', 403

@app.route('/webhook', methods=['POST'])
def webhook():
  data = request.json
  try:
    msg = data['entry'][0]['changes'][0]['value']['messages'][0]
    from_num = msg['from']
    text = msg['text']['body']
    inv = get_inventory()
    reply = ask_gemini(text, inv)
    send_whatsapp(from_num, reply)
  except: pass
  return 'OK', 200

if __name__ == '__main__':
  app.run()
