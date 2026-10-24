from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "-1003987555752")
# 초기 상태에서는 FINAL URL 비활성 - 깔끔한 빈 상태
FINAL_FORM_URL = "https://shiny-hall-b9ed.duribun8.workers.dev?v=INITIAL"
# 새 NPOINT ID - 실매매 계산 통일 - 2026-10-24 - Render 로그인 없이 GitHub로 교체
NPOINT_ID = "10b790b906137128e435"
NPOINT_URL = "https://api.npoint.io/10b790b906137128e435"

# 수익확인 고지 문구 - 개인PC/관리자PC와 동일 - 2026-10-24 수정
PROFIT_DISCLAIMER = "수수료0.02%(증권사별 다름) + 슬리피지0.5틱 미포함 이기 때문에 정확한 수익은 이용 하고 있는 증권사의 매매집계를 참조 하십시요"
FEE_INFO = "수수료0.02%(증권사별 다름) + 슬리피지0.5틱 미포함"
REAL_CALC = {"fee": 0.0002, "slippage": 0.5, "formula": "(청산가-진입가)*수량*포인트가치 - 수수료0.02% - 슬리피지0.5틱", "note": "텔레그램,관리자PC,유저PC 모두 실매매처럼 계산"}
text += f"\n\n※ {PROFIT_DISCLAIMER}"
def tg_api(method, payload=None):
    if not BOT_TOKEN:
        return {"ok": False, "error": "NO_TOKEN"}
    base = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if payload is None:
            r = requests.get(base, timeout=10)
        else:
            r = requests.post(base, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route("/")
def root():
    return jsonify({
        "서비스": "mnq-v21-server",
        "상태": "초기상태 - 모든 설정 삭제됨",
        "버전": "INITIAL_STATE_v1",
        "channel": CHANNEL_ID,
        "note": "텔레그램 초기 상태로 복구됨"
    })

@app.route("/health")
def health():
    return jsonify({"ok": True, "state": "INITIAL"})

@app.route("/api/factory-reset", methods=["GET"])
def factory_reset():
    """텔레그램을 완전 초기 상태로 복구 - 모든 설정 삭제"""
    results = {}
    
    # 1. Webhook 삭제 - Telegram 서버에서 webhook 제거
    results["deleteWebhook"] = tg_api("deleteWebhook", {"drop_pending_updates": True})
    
    # 2. 모든 Bot 명령어 삭제
    results["deleteMyCommands"] = tg_api("deleteMyCommands", {})
    
    # 3. 메뉴 버튼 초기화
    results["setMenuButton_default"] = tg_api("setChatMenuButton", {"menu_button": {"type": "default"}})
    
    # 4. 채널과 개인 채팅에 remove_keyboard 전송 - 버튼 2개 제거
    # 채널
    try:
        payload_channel = {
            "chat_id": CHANNEL_ID,
            "text": "🗑️ 초기 상태 복구 - 모든 설정 삭제됨\n\n이제 텔레그램을 재설치한 것과 같은 깨끗한 상태입니다.",
            "reply_markup": {"remove_keyboard": True}
        }
        results["remove_keyboard_channel"] = tg_api("sendMessage", payload_channel)
    except Exception as e:
        results["remove_keyboard_channel"] = {"ok": False, "error": str(e)}
    
    return jsonify({
        "ok": True,
        "message": "텔레그램 초기 상태로 복구 완료",
        "results": results,
        "next": [
            "1. Telegram 앱을 삭제 후 재설치하면 클라이언트도 초기 상태",
            "2. 채널 -1003987555752 삭제 후 재생성하면 메시지 0개 초기 상태",
            "3. /start 입력하면 이제 아무 버튼도 없는 깨끗한 상태에서 시작"
        ]
    })

@app.route("/api/remove-keyboard")
def remove_keyboard():
    chat_id = request.args.get("chat_id", CHANNEL_ID)
    payload = {
        "chat_id": chat_id,
        "text": "🗑️ 키보드 제거 완료 - 초기 상태",
        "reply_markup": {"remove_keyboard": True}
    }
    r = tg_api("sendMessage", payload)
    return jsonify({"ok": True, "result": r})

@app.route("/api/delete-all")
def delete_all():
    # 위 factory-reset과 동일하지만 짧은 이름
    return factory_reset()

@app.route("/telegram-webhook", methods=["POST"])
def webhook():
    # 초기 상태에서는 webhook이 없으므로 아무것도 하지 않음
    return jsonify({"ok": True, "state": "INITIAL - no action"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
