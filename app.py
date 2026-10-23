from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import requests

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")  
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1003987555752")
FINAL_FORM_URL = os.environ.get("FINAL_FORM_URL", "https://shiny-hall-b9ed.duribun8.workers.dev?v=20261024_D_FIXED")

latest_signal = {"signal": "WAIT", "price": 0, "time": 0, "profit": 0, "account": "", "raw": {}}
history = []

def tg_api(method, payload):
    if not BOT_TOKEN:
        return {"ok": False, "error": "NO_TOKEN"}
    base = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        r = requests.post(base, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_with_fixed_keyboard(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "keyboard": [
                [{"text": "매매 확인", "web_app": {"url": FINAL_FORM_URL}}]
            ],
            "resize_keyboard": True,
            "is_persistent": True,
            "one_time_keyboard": False
        }
    }
    return tg_api("sendMessage", payload)

def send_form_with_both(chat_id):
    payload = {
        "chat_id": chat_id,
        "text": "🟢 <b>MNQ V21 최종이용자 폼</b>\n\n아래 버튼을 클릭하면 최종이용자 전용 대시보드가 텔레그램 안에서 열립니다. (김성택 / $2,111,184 화면)",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "📱 최종이용자 폼 열기", "web_app": {"url": FINAL_FORM_URL}}],
                [{"text": "🌐 브라우저에서 열기", "url": FINAL_FORM_URL}]
            ]
        }
    }
    return tg_api("sendMessage", payload)

def format_final_user_message(data):
    signal = data.get("signal", "WAIT")
    price = data.get("price", 0)
    profit = data.get("profit", 0)
    account = data.get("account", "-")
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    if signal == "BUY":
        return f"🟢 <b>MNQ V21 매수 신호</b>\n<b>신호: BUY</b>\n가격: {price}\n수익: {profit}\n계좌: {account}\n시간: {t}\n\n<code>BUY | {price} | {profit}</code>"
    elif signal == "SELL":
        return f"🔴 <b>MNQ V21 매도 신호</b>\n<b>신호: SELL</b>\n가격: {price}\n수익: {profit}\n계좌: {account}\n시간: {t}\n\n<code>SELL | {price} | {profit}</code>"
    else:
        return f"🟦 <b>MNQ V21 대기중</b>\n신호: WAIT\n가격: {price}\n수익: {profit}\n계좌: {account}\n시간: {t}"

@app.route("/")
def root():
    return jsonify({"서비스": "mnq-v21-server", "상태": "정상", "버전": "V21-AB-FIXED-FINAL", "channel": CHANNEL_ID, "final_form_url": FINAL_FORM_URL})

@app.route("/health")
def health():
    return jsonify({"ok": True, "latest": latest_signal})

@app.route("/api", methods=["GET","POST"])
@app.route("/api/", methods=["GET","POST"])
def api():
    global latest_signal
    if request.method == "GET":
        return jsonify(latest_signal)
    data = request.get_json(force=True, silent=True) or {}
    signal = data.get("signal") or data.get("action") or "WAIT"
    signal = str(signal).upper()
    latest_signal = {"signal": signal, "price": data.get("price", 0), "time": int(time.time()), "profit": data.get("profit", 0), "account": data.get("account", ""), "raw": data}
    history.append(latest_signal)
    if len(history) > 100: history.pop(0)
    tg_text = format_final_user_message(latest_signal)
    tg_api("sendMessage", {"chat_id": CHANNEL_ID, "text": tg_text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[{"text": "📱 최종이용자 폼 열기", "web_app": {"url": FINAL_FORM_URL}}]]}})
    return jsonify({"ok": True, "received": latest_signal})

@app.route("/api/set-webhook")
def set_webhook():
    webhook_url = f"https://{request.host}/telegram-webhook"
    resp = tg_api("setWebhook", {"url": webhook_url})
    info = tg_api("getWebhookInfo", {})
    return jsonify({"ok": resp.get("ok", False), "setWebhook_response": resp, "webhookInfo": info, "webhook_url": webhook_url})

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True, silent=True) or {}
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        if text == "/start":
            welcome = f"🟢 <b>MNQ Signal Bot</b>\n\n하단 <b>'매매 확인'</b> 버튼을 누르면 최종이용자 폼이 열립니다.\n\n📱 폼: {FINAL_FORM_URL}\n채널: {CHANNEL_ID}\n\n명령어:\n/start - 시작 및 버튼 생성\n/form - 폼 바로 열기\n/remove - 키보드 2개 제거\n/clear - 키보드 2개 제거"
            send_with_fixed_keyboard(chat_id, welcome)
            return jsonify({"ok": True})
        elif text in ["/remove", "/clear", "/reset", "/delete"]:
            # 키보드 2개 제거
            payload = {
                "chat_id": chat_id,
                "text": "🗑️ 기존 매매 확인 버튼 2개 제거 완료.\n\n이제 /start 입력하면 최종이용자 폼 1개만 생성됩니다.",
                "reply_markup": {"remove_keyboard": True}
            }
            tg_api("sendMessage", payload)
            return jsonify({"ok": True, "action": "remove_keyboard"})
        elif text == "매매 확인" or text == "/form" or "/form" in text or "/매매" in text:
            send_form_with_both(chat_id)
            return jsonify({"ok": True})
    return jsonify({"ok": True})


@app.route("/api/remove-keyboard")
def remove_keyboard_route():
    # chat_id from query, default to channel and also try to clear menu
    chat_id = request.args.get("chat_id", CHANNEL_ID)
    # 1. Remove reply keyboard
    payload = {
        "chat_id": chat_id,
        "text": "🗑️ 기존 키보드 2개 제거됨. 이제 /start 로 1개만 다시 생성하십시오.",
        "reply_markup": {"remove_keyboard": True}
    }
    r1 = tg_api("sendMessage", payload)
    # 2. Also try to remove from channel
    if str(chat_id) != str(CHANNEL_ID):
        payload2 = {
            "chat_id": CHANNEL_ID,
            "text": "🗑️ 채널 키보드 제거",
            "reply_markup": {"remove_keyboard": True}
        }
        r2 = tg_api("sendMessage", payload2)
    else:
        r2 = {"ok": True, "note": "same as channel"}
    # 3. Clear bot commands menu (optional)
    return jsonify({"ok": True, "remove_sent_to": chat_id, "result1": r1, "result2": r2, "next": "텔레그램에서 /start 입력하면 매매 확인 1개만 생성됩니다."})

@app.route("/api/set-single-keyboard")
def set_single_keyboard_route():
    chat_id = request.args.get("chat_id", CHANNEL_ID)
    payload = {
        "chat_id": chat_id,
        "text": f"✅ 매매 확인 1개만 생성됨\n\n최종이용자 폼: {FINAL_FORM_URL}\n채널: {CHANNEL_ID}\n\n하단 파란색 '매매 확인' 1개만 뜹니다.",
        "parse_mode": "HTML",
        "reply_markup": {
            "keyboard": [
                [{"text": "매매 확인", "web_app": {"url": FINAL_FORM_URL}}]
            ],
            "resize_keyboard": True,
            "is_persistent": True,
            "one_time_keyboard": False
        }
    }
    r = tg_api("sendMessage", payload)
    return jsonify({"ok": True, "sent_to": chat_id, "result": r, "final_form_url": FINAL_FORM_URL})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
