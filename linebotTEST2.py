# -*- coding: utf-8 -*-


import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi('')
handler = WebhookHandler('')

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

# 解析中獎號碼的函數
def check_invoice(invoice_number):
    # 從網址取得 XML 資料
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
            # 檢查是否中獎
            if invoice_number == special_prize:
                answer= "特別獎"
            elif invoice_number == grand_prize:
                answer= "特獎"
            else:
                for i in first_prizes:
                    if invoice_number == i:
                        answer= "頭獎"
                    elif invoice_number[-7:]==i[-7:]:
                        answer= "二獎"
                    elif invoice_number[-6:]==i[-6:]:
                        answer= "三獎"
                    elif invoice_number[-5:]==i[-5:]:
                        answer= "四獎"
                    elif invoice_number[-4:]==i[-4:]:
                        answer= "五獎"
                    elif invoice_number[-3:]==i[-3:]:
                        answer= "六獎"
            try:
                return answer
            except:
                return "可惜，您沒有沒中獎"
        else:
            return "Error fetching the XML data."
    except requests.exceptions.Timeout:
        return "Connection timed out."
    except requests.exceptions.ConnectionError:
        return "Connection error occurred."

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
