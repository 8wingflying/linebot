import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3

app = Flask(__name__)

line_bot_api = LineBotApi('h/CGBP0eDeYlKf5se+2cCOD/kV1cArUYO9O401UGgBWr8qpGyaa0OxVQ62tshBKyiznpySyA4uUFz1pJpC41moaCBfVebdIFnCMWkP/twrXY8gJLBRN8rkbWW1M77ssPN4rseJoCwSoaxDnOMhZWuAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('4371239cc012d6d1160c7090ee846caf')

# SQLite 數據庫文件路徑
DB_FILE_PATH = 'invoice_data.db'

# 定義中獎訊息
prize_messages = {
    "特別獎": "恭喜！您中了特別獎，獎金新臺幣一千萬元。",
    "特獎": "恭喜！您中了特獎，獎金新臺幣二百萬元。",
    "頭獎": "恭喜！您中了頭獎，獎金新臺幣二十萬元。",
    "二獎": "恭喜！您中了二獎，獎金新臺幣四萬元。",
    "三獎": "恭喜！您中了三獎，獎金新臺幣一萬元。",
    "四獎": "恭喜！您中了四獎，獎金新臺幣四千元。",
    "五獎": "恭喜！您中了五獎，獎金新臺幣一千元。",
    "六獎": "恭喜！您中了六獎，獎金新臺幣二百元。"
}

# 初始化 SQLite 數據庫
if not os.path.exists(DB_FILE_PATH):
    conn = sqlite3.connect(DB_FILE_PATH)
    c = conn.cursor()
    # 建立資料表
    c.execute('''CREATE TABLE IF NOT EXISTS invoices
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    special_prize TEXT UNIQUE,
                    grand_prize TEXT,
                    big_prize1 TEXT,
                    big_prize2 TEXT,
                    big_prize3 TEXT)''')
    conn.commit()
    conn.close()

# 檢查並更新數據庫
conn = sqlite3.connect(DB_FILE_PATH)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
count = c.fetchone()[0]
if count == 0:
    url = 'https://invoice.etax.nat.gov.tw/invoice.xml'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            tree = ET.fromstring(response.text)
            item = tree.find('.//item')
            description = item.find('description').text
            special_prize = description.split('<p>特別獎：')[1].split('</p>')[0]
            grand_prize = description.split('<p>特獎：')[1].split('</p>')[0]
            first_prizes_str = [x.split('</p>')[0] for x in description.split('<p>頭獎：')[1:]]  # 取得所有頭獎的字串列表
            
            # 將每個頭獎字串進一步分割為單獨的頭獎號碼
            first_prizes = []
            for prize_str in first_prizes_str:
                first_prizes.extend(prize_str.split('、'))  # 將多個頭獎號碼加入到列表中
                
            # 將數據插入到數據庫中
            c.execute("INSERT INTO invoices (special_prize, grand_prize, big_prize1, big_prize2, big_prize3) VALUES (?, ?, ?, ?, ?)", (special_prize, grand_prize, first_prizes[0], first_prizes[1], first_prizes[2]))
            conn.commit()
    except requests.exceptions.Timeout:
        # pass "Connection timed out."
        pass
    except requests.exceptions.ConnectionError:
        # return "Connection error occurred."
        pass
conn.close()

# 解析中獎號碼的函數
def check_invoice(invoice_number):
    conn = sqlite3.connect(DB_FILE_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM invoices")
    data = c.fetchone()
    if data is not None:
        _,special_prize, grand_prize, big_prize1, big_prize2, big_prize3 = data
        if invoice_number == special_prize:
            answer = "特別獎"
        elif invoice_number == grand_prize:
            answer = "特獎"
        elif invoice_number == big_prize1 or invoice_number == big_prize2 or invoice_number == big_prize3:
            answer = "頭獎"
        elif invoice_number[-7:] == big_prize1[-7:] or invoice_number[-7:] == big_prize2[-7:] or invoice_number[-7:] == big_prize3[-7:]:
            answer = "二獎"
        elif invoice_number[-6:] == big_prize1[-6:] or invoice_number[-6:] == big_prize2[-6:] or invoice_number[-6:] == big_prize3[-6:]:
            answer = "三獎"
        elif invoice_number[-5:] == big_prize1[-5:] or invoice_number[-5:] == big_prize2[-5:] or invoice_number[-5:] == big_prize3[-5:]:
            answer = "四獎"
        elif invoice_number[-4:] == big_prize1[-4:] or invoice_number[-4:] == big_prize2[-4:] or invoice_number[-4:] == big_prize3[-4:]:
            answer = "五獎"
        elif invoice_number[-3:] == big_prize1[-3:] or invoice_number[-3:] == big_prize2[-3:] or invoice_number[-3:] == big_prize3[-3:]:
            answer = "六獎"
        else:
            answer = "可惜，您沒有中獎"
    else:
        answer = "資料庫中無資料，請稍後再試"
    conn.close()
    return answer

# Line Bot 的 Webhook 處理
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    
    # 檢查是否為 8 位數的數字
    if user_input.isdigit() and len(user_input) == 8:
        result = check_invoice(user_input)
        # 回覆訊息
        if result in prize_messages:
            reply_message = prize_messages[result]
        else:
            reply_message = result
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"您輸入的發票號碼為：{user_input}\n {reply_message}"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 8 位數的發票號碼。"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
