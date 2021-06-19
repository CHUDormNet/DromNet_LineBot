from config import config
from flask import Flask, request, abort, render_template, send_file
from urllib.parse import urlparse

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    TemplateSendMessage,
    MessageAction,
    QuickReply,
    QuickReplyButton,
    ConfirmTemplate,
)
from linebot.models.template import CarouselColumn, CarouselTemplate

import utils
import io
import os

app = Flask(__name__)

# =========== 載入開發時環境 ===========

# if app.config["ENV"] == "production":
#     app.config.from_object(config["pro"])
# else:
#     app.config.from_object(config["dev"])
# line_bot_api = LineBotApi(app.config["CHANNEL_ACCESS_TOKEN"])
# handler = WebhookHandler(app.config["CHANNEL_SECRET"])


# =========== 載入上線時環境 ===========
line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))


@app.route("/", methods=["GET"])
def index():
    # 一定要建立一個資料夾叫做：/templates，如果沒有設定，會優先指向 templates 資料夾。
    return render_template(
        "index.html",
    )


@app.route("/static/<path:filepath>/", methods=["GET"])
def img(filepath=None):
    if filepath is None:
        return render_template("404.html")
    else:
        with open(f"app/static/{filepath}", "rb") as bites:
            return send_file(io.BytesIO(bites.read()), mimetype="image/png")


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    host = f"https://{urlparse(request.base_url).hostname}"
    user = event.source.user_id
    # Step 1
    if event.message.text == "新生":
        carousel_template_message = TemplateSendMessage(
            alt_text="歡迎使用中華大學宿網會的簡易小機器人, 請至手機查看訊息。",
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url=f"{host}/static/img/new/s1_link.jpeg",
                        title="第一步：購買一條網路線",
                        text="規格：RJ-45 接口。\n長度：建議先到床位測量使用範圍。\n需要將網路線插入床位的壁孔才能使用。",
                        actions=[
                            MessageAction(label="請閱讀上方文字，不要點我", text="請遵守約定"),
                        ],
                    ),
                    CarouselColumn(
                        thumbnail_image_url=f"{host}/static/img/new/s2_check_computer.jpeg",
                        title="第二步：檢查電腦有無網路孔",
                        text="有網路孔請回答下面視窗，\n無網路孔請往右滑向第三步。\n學校宿舍內無 WelIFI，教室則有公共 WelIFI。",
                        actions=[
                            MessageAction(label="請閱讀上方文字，不要點我", text="請遵守約定"),
                        ],
                    ),
                    CarouselColumn(
                        thumbnail_image_url=f"{host}/static/img/new/s3_rj45_to_usb.jpeg",
                        title="第三步：電腦無網路孔需購買轉接頭",
                        text="轉接頭名稱：「RJ-45 轉 USB」",
                        actions=[
                            MessageAction(label="請閱讀上方文字，不要點我", text="請遵守約定"),
                        ],
                    ),
                ]
            ),
        )

        confirm_template_message = utils.ConfirmWindow(
            context="上面步驟已完成，你是屬於？", sucess_string="男生宿舍", error_string="女生宿舍"
        )

        line_bot_api.push_message(user, carousel_template_message)
        line_bot_api.reply_message(event.reply_token, confirm_template_message)
    # # Step 2 "一宿五樓", "二宿", "三宿"
    elif event.message.text == "男生宿舍":
        buttons_template_message = utils.ButtonWindow(
            title="請選擇你的宿舍及樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["一宿五樓", "二宿", "三宿"],
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # # Step 2 "一宿", "四宿"
    elif event.message.text == "女生宿舍":
        buttons_template_message = utils.ButtonWindow(
            title="請選擇妳的宿舍：",
            context="請選擇下面的選項：",
            number=2,
            label_list=["一宿", "四宿"],
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # # # Step 3 "一宿五樓"
    elif event.message.text == "一宿五樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/1-5.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # # # Step 3
    elif event.message.text == "一宿":
        buttons_template_message = utils.ButtonWindow(
            title="請選擇妳的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["一宿二樓", "一宿三樓", "一宿四樓"],
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # # # Step 3
    elif event.message.text == "二宿":
        buttons_template_message_1 = utils.ButtonWindow(
            title="請選擇你的樓層：",
            context="請選擇下面的選項：",
            number=4,
            label_list=["二宿二樓", "二宿三樓", "二宿四樓", "二宿五樓"],
        )
        buttons_template_message_2 = utils.ButtonWindow(
            title="請選擇你的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["二宿六樓", "二宿七樓", "二宿八樓"],
        )
        line_bot_api.push_message(user, buttons_template_message_1)
        line_bot_api.reply_message(
            event.reply_token, buttons_template_message_2)
    # # # Step 3
    elif event.message.text == "三宿":
        buttons_template_message_1 = utils.ButtonWindow(
            title="請選擇你的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["三宿一樓", "三宿二樓", "三宿三樓"],
        )
        buttons_template_message_2 = utils.ButtonWindow(
            title="請選擇你的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["三宿四樓", "三宿五樓", "三宿六樓"],
        )
        line_bot_api.push_message(user, buttons_template_message_1)
        line_bot_api.reply_message(
            event.reply_token, buttons_template_message_2)
    # # # Step 3
    elif event.message.text == "四宿":
        buttons_template_message_1 = utils.ButtonWindow(
            title="請選擇妳的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["四宿一樓", "四宿二樓", "四宿三樓"],
        )
        buttons_template_message_2 = utils.ButtonWindow(
            title="請選擇妳的樓層：",
            context="請選擇下面的選項：",
            number=3,
            label_list=["四宿四樓", "四宿五樓", "四宿六樓"],
        )
        line_bot_api.push_message(user, buttons_template_message_1)
        line_bot_api.reply_message(
            event.reply_token, buttons_template_message_2)

    elif event.message.text == "一宿二樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/1-2.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "一宿三樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/1-3.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "一宿四樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/1-4.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿二樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-2.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿三樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-3.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿四樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-4.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿五樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-5.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿六樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-6.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿七樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-7.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "二宿八樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/2-8.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿一樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-1.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿二樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-2.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿三樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-3.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿四樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-4.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿五樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-5.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "三宿六樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/3-6.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿一樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-1.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿二樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-2.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿三樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-3.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿四樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-4.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿五樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-5.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "四宿六樓":
        image_message = utils.ImageWindow(
            origin_path=f"{host}/static/img/hinet/4-6.jpeg"
        )
        alert_message = TextSendMessage(
            text=f"請找到同寢室的「HN 帳號」，\n並在後面加上「@hinet.net」\n{utils.Separate(10)} \n範例：1501房為 72186749，\n那帳號就是「72186749@hinet.net」，\n密碼全校宿舍皆為：「123456」。")
        buttons_template_message = utils.ButtonWindow(
            title="請根據上則訊息尋找連線帳號密碼：",
            context="請選擇下列選項。",
            number=3,
            label_list=["連線教學", "故障報修", "重新選擇宿舍"],
        )
        line_bot_api.push_message(user, image_message)
        line_bot_api.push_message(user, alert_message)
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    elif event.message.text == "舊生" or event.message.text == "不知道帳號密碼" or event.message.text == "重新選擇宿舍":
        confirm_template_message = utils.ConfirmWindow(
            context="請問您是屬於？", sucess_string="男生宿舍", error_string="女生宿舍"
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)

    # options: Windows, macOS, 連線教學
    elif event.message.text == "連線教學":
        buttons_template_message = utils.ButtonWindow(
            title="請問您的電腦系統為何？",
            context="請選擇下面的選項。",
            number=2,
            label_list=["Windows", "macOS"],
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # options: Windows 7, Windows 8, Windows 10
    elif event.message.text == "Windows":
        buttons_template_message = utils.ButtonWindow(
            title="請問是 Windows 的哪個版本呢？",
            context="請選擇下面的選項。",
            number=3,
            label_list=["Windows 7", "Windows 8", "Windows 10"],
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    # options: 網路帳號密碼查詢,
    elif event.message.text == "Windows 7":
        # TODO userId 取法, github issue https://github.com/line/line-bot-sdk-python/issues/139
        user = event.source.user_id
        text = "網路設定步驟如下：\n開啟【控制台】>【網路和網際網路】>【設定新的連線與網路】>【選擇連線到網際網路】>【下一步】>【寬頻(PPPOE)】 > 輸入使用者帳號及密碼。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
        confirm_template_message = utils.ButtonWindow(
            title="請問有解決你的問題嗎？",
            context="請選擇下面的選項。",
            number=3,
            label_list=["不知道帳號密碼", "我需要協助", "已完成"]
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)
    # options: 網路帳號密碼查詢,
    elif event.message.text == "Windows 8":
        user = event.source.user_id
        text = "網路設定步驟如下：\n開啟【網路和共用中心】>【設定新的連線與網路】>【選擇連線到網際網路】>【下一步】>【寬頻(PPPOE)】> 輸入使用者帳號及密碼。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
        confirm_template_message = utils.ButtonWindow(
            title="請問有解決你的問題嗎？",
            context="請選擇下面的選項。",
            number=3,
            label_list=["不知道帳號密碼", "我需要協助", "已完成"]
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)
    # options: 網路帳號密碼查詢,
    elif event.message.text == "Windows 10":
        user = event.source.user_id
        text = "網路設定步驟如下：\n開啟【控制台】>【網路和網際網路】>【網路和共用】>【設定新的連線與網路】>【選擇連線到網際網路】>【下一步】>【寬頻(PPPOE)】> 輸入使用者帳號及密碼。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
        confirm_template_message = utils.ButtonWindow(
            title="請問有解決你的問題嗎？",
            context="請選擇下面的選項。",
            number=3,
            label_list=["不知道帳號密碼", "我需要協助", "已完成"]
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)
    # options: 網路帳號密碼查詢,
    elif event.message.text == "macOS":
        user = event.source.user_id
        text = "網路設定步驟如下：\n【系統偏好設定】>【網路】>【點及左側底部「加入」並選擇 PPPoE】>【按一下「乙太網路」彈出式選單】> 輸入使用者帳號及密碼。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
        confirm_template_message = utils.ButtonWindow(
            title="請問有解決你的問題嗎？",
            context="請選擇下面的選項。",
            number=3,
            label_list=["不知道帳號密碼", "我需要協助", "已完成"]
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)
    elif event.message.text == "已完成":
        text = "很高興你已經可以使用宿舍網路了！我們下次見～"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
    elif event.message.text == "我需要協助":
        text = "這邊還沒做, 請等宿網會一下。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
    elif event.message.text == "請遵守約定":
        text = "這邊還沒做, 請等宿網會一下。"
        line_bot_api.push_message(to=user, messages=TextSendMessage(text))
    else:
        text_message = TextSendMessage(
            text="請點擊下方按鈕開始對話。\n"
                 + utils.Separate(30)
                 + "\n請依照自己的身份進行選擇：\n"
                 + "\n尚未入住過宿舍，請點選「我是新生 👋」"
                 + "\n已經入住過宿舍，請點選「我是舊生 🤟」"
                 + utils.Separate(30),
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(
                        label="我是新生 👋", text="新生")),
                    QuickReplyButton(action=MessageAction(
                        label="我是舊生 🤟", text="舊生")),
                    QuickReplyButton(action=MessageAction(
                        label="連線教學", text="連線教學")),
                    QuickReplyButton(action=MessageAction(
                        label="我需要協助", text="我需要協助")),
                ]
                 ),
        )
        line_bot_api.reply_message(event.reply_token, text_message)
    return "OK2"


if __name__ == "__main__":
    # app.run()
    app.run(port="5000", debug=True)
