import asyncio
import os
import re
import json
import logging
from datetime import datetime, timedelta

import pytz
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from rapidfuzz import process, fuzz

############################################
# Config & Data Loading
############################################

USAGE_FILE = "usage_stats.json"
UNKNOWN_QUERIES_FILE = "unknown_queries.json"
USERBOT_STATUS_FILE = "userbot_status.json"
MAPPING_FILE = "borders_mapping.json"


import os
import json
import logging

def load_config() -> dict:
    """Loads configuration from environment variables."""
    config = {}
    
    # List of required keys from environment variables
    required_keys = [
        "BOT_TOKEN",
        "API_ID",
        "API_HASH",
        "SESSION_NAME",
        "CHANNEL_LINK",
        "STATUS_FILE",
    ]

    for key in required_keys:
        value = os.environ.get(key)
        if not value:
            raise KeyError(f"Missing required environment variable: {key}")
        config[key] = value

    return config


def load_data(borders_file: str, mapping_file: str):
    status_data, names, mapping = {}, [], {}
    if os.path.exists(borders_file):
        try:
            with open(borders_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                status_data = data.get("status", {})
                names = data.get("names", [])
        except (json.JSONDecodeError, FileNotFoundError):
            logging.warning("Could not parse borders file. Starting empty store.")
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logging.warning("Could not parse mapping file. Using empty mapping.")
    return status_data, names, mapping


def save_status(borders_file: str, status_data: dict, names: list):
    with open(borders_file, "w", encoding="utf-8") as f:
        json.dump({"status": status_data, "names": names}, f, ensure_ascii=False, indent=2)


def get_user_stats():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total_queries": 0, "border_queries": {}, "last_updated": ""}


def save_user_stats(stats: dict):
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def get_unknown_queries():
    if os.path.exists(UNKNOWN_QUERIES_FILE):
        with open(UNKNOWN_QUERIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_unknown_queries(queries: dict):
    with open(UNKNOWN_QUERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)


def get_userbot_status():
    if os.path.exists(USERBOT_STATUS_FILE):
        with open(USERBOT_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_update_timestamp": "N/A", "mode": "on_demand"}


def set_userbot_status(mode: str, timestamp: str):
    with open(USERBOT_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update_timestamp": timestamp, "mode": mode}, f, ensure_ascii=False, indent=2)


############################################
# Helpers
############################################

def get_jerusalem_time() -> datetime:
    jerusalem_tz = pytz.timezone("Asia/Jerusalem")
    return datetime.now(jerusalem_tz)


def escape_md(text: str) -> str:
    return re.sub(r"([_*`\[])", r"\\\1", text)


def get_best_match(text: str, mapping: dict):
    if not mapping:
        return None, None, 0
    all_keywords = {kw: border for border, keywords in mapping.items() for kw in keywords}
    best_match = process.extractOne(text, all_keywords.keys(), scorer=fuzz.token_set_ratio, score_cutoff=70)
    if best_match:
        matched_keyword, score, _ = best_match
        canonical_name = all_keywords[matched_keyword]
        return canonical_name, matched_keyword, score
    return None, None, 0


def parse_status_from_text(text: str):
    emoji_mapping = {
        "✅": "🟢", "🟢": "🟢", "✔️": "🟢", "☑️": "🟢",
        "❌": "🔴", "❎": "🔴", "✖️": "🔴", "⛔": "🔴", "🚫": "🔴", "🛑": "🔴", "⚫": "🔴",
        "🟡": "⚠️", "⚠️": "⚠️", "🚦": "⚠️", "🔶": "⚠️", "🚧": "⚠️", "🚓": "⚠️", "🚨": "⚠️", "👮": "⚠️", "🚶‍♂️": "⚠️",
    }
    
    # Priority 1: Check for emojis
    for emoji_char, status_val in emoji_mapping.items():
        if emoji_char in text:
            return {"status": status_val, "sub_status": None, "match": emoji_char}
    
    # Priority 2: Fallback to keywords
    positive_keywords = ["سالك", "سالكة", "تمام", "فاتح", "مفتوح", "بدون", "بحري", "ماشية", "منسوب", "سهل", "خفيف", "لا يوجد", "سلس"]
    negative_keywords = ["مغلق", "تسكير", "اغلاق", "واقف", "وقوف"]
    
    # New branched structure for caution keywords
    caution_keywords = {
        "traffic_jam": {
            "stopping": ["وقوف تام"],
            "high": ["ازمة", "ازمه", "كثافة سير", "كثافه سير", "عجقة", "بطيء", "تأخير"],
            "medium": ["يتحرك", "سريع", "خفيف"]
        },
        "police_presence": ["جيش", "شرطة", "تواجد", "تفتيش"],
        "road_event": ["حادث", "عرقلة", "مشاة", "تجمع"]
    }
    
    # Find best match for all keywords
    pos_match, pos_score = find_status_keyword(text, positive_keywords)
    neg_match, neg_score = find_status_keyword(text, negative_keywords)
    
    caution_match = None
    best_caution_score = 0
    best_sub_status = None
    
    # Check for branched caution keywords and get the best match
    # Traffic
    for level, keywords in caution_keywords["traffic_jam"].items():
        match, score = find_status_keyword(text, keywords)
        if match and score > best_caution_score:
            best_caution_score = score
            best_sub_status = f"traffic_{level}"
            caution_match = match

    # Police presence
    match, score = find_status_keyword(text, caution_keywords["police_presence"])
    if match and score > best_caution_score:
        best_caution_score = score
        best_sub_status = "police_presence"
        caution_match = match

    # Road event
    match, score = find_status_keyword(text, caution_keywords["road_event"])
    if match and score > best_caution_score:
        best_caution_score = score
        best_sub_status = "road_event"
        caution_match = match

    if pos_match and pos_score > max(neg_score, best_caution_score):
        return {"status": "🟢", "sub_status": None, "match": pos_match}
    if neg_match and neg_score > max(pos_score, best_caution_score):
        return {"status": "🔴", "sub_status": None, "match": neg_match}
    if best_sub_status:
        return {"status": "⚠️", "sub_status": best_sub_status, "match": caution_match}
    
    return None

def find_status_keyword(text: str, keywords: list):
    if not text or not keywords:
        return None, 0
    best_match = process.extractOne(text, keywords, scorer=fuzz.token_set_ratio, score_cutoff=80)
    if best_match:
        return best_match[0], best_match[1]
    return None, 0

############################################
# Core Logic
############################################

async def process_message(event):
    """Event handler for new channel messages."""
    global status_data, names, mapping
    text = event.message.message
    if not text:
        return

    canonical_name, matched_keyword, score = get_best_match(text, mapping)
    if not canonical_name:
        return

    current_time = get_jerusalem_time()
    result = parse_status_from_text(text)
    
    if canonical_name not in status_data:
        status_data[canonical_name] = {}
        if canonical_name not in names:
            names.append(canonical_name)

    status_data[canonical_name]['last_seen_message'] = text
    status_data[canonical_name]['last_seen_timestamp'] = current_time.isoformat()
    if result:
        status_data[canonical_name]["status"] = result["status"]
        status_data[canonical_name]["sub_status"] = result["sub_status"]
        status_data[canonical_name]["timestamp"] = current_time.isoformat()
    
    save_status(config["STATUS_FILE"], status_data, names)
    set_userbot_status("event-based", current_time.isoformat())
    logging.info(f"✅ Updated border '{canonical_name}' with status '{result}' based on new message.")

async def handle_user_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    global status_data, names, mapping
    status_data, names, mapping = load_data(config["STATUS_FILE"], MAPPING_FILE)

    user_text = update.message.text.strip()
    
    stats = get_user_stats()
    stats["total_queries"] = stats.get("total_queries", 0) + 1
    stats["last_updated"] = get_jerusalem_time().isoformat()
    
    border_name, matched_keyword, score = get_best_match(user_text, mapping)
    
    if border_name:
        stats.setdefault("border_queries", {})
        stats["border_queries"][border_name] = stats["border_queries"].get(border_name, 0) + 1
        save_user_stats(stats)
        
        status_info = status_data.get(border_name, {})
        timestamp_str = status_info.get("timestamp")
        
        # Check if the cached status is recent
        if timestamp_str:
            last_update_time = datetime.fromisoformat(timestamp_str)
            jerusalem_tz = pytz.timezone("Asia/Jerusalem")
            current_time = datetime.now(jerusalem_tz)
            time_since_update = current_time - last_update_time
            
            # Use cached status if it's less than 30 minutes old
            if time_since_update < timedelta(minutes=30):
                await reply_with_status(update, border_name, status_info, timestamp_str)
                return

        # If cache is old, perform live search
        telethon_client = context.application.bot_data["telethon_client"]
        channel_entity = context.application.bot_data["channel_entity"]
        msg = await search_latest_message_for_border(telethon_client, channel_entity, border_name, mapping)
        
        if msg:
            result = parse_status_from_text(msg.text or "")
            msg_time = msg.date.astimezone(pytz.timezone("Asia/Jerusalem"))
            
            status_data.setdefault(border_name, {})
            if result:
                status_data[border_name]["status"] = result["status"]
                status_data[border_name]["sub_status"] = result["sub_status"]
            status_data[border_name]["timestamp"] = msg_time.isoformat()
            status_data[border_name]["last_seen_message"] = msg.text or ""
            status_data[border_name]["last_seen_timestamp"] = msg_time.isoformat()

            save_status(config["STATUS_FILE"], status_data, names)
            await reply_with_status(update, border_name, status_data[border_name], msg_time.isoformat())
            return
        
        # Fallback if no new message found
        if "last_seen_message" in status_info:
            await reply_with_status(update, border_name, status_info, status_info.get("last_seen_timestamp"))
            return
            
    # Handle unknown queries
    unknown_queries = get_unknown_queries()
    timestamp = get_jerusalem_time().isoformat()
    unknown = unknown_queries.get(user_text, {"count": 0, "timestamp": timestamp})
    unknown["count"] += 1
    unknown["timestamp"] = timestamp
    unknown_queries[user_text] = unknown
    save_unknown_queries(unknown_queries)
    save_user_stats(stats)
    await update.message.reply_text("ℹ️ لم يتم العثور على المعبر. تم تسجيل الاستعلام للمراجعة.")


async def search_latest_message_for_border(client: TelegramClient, channel, border_name: str, mapping: dict):
    """Search the channel for the latest message containing ANY synonym of the given border."""
    synonyms = mapping.get(border_name, []) or [border_name]
    latest_msg = None
    for kw in synonyms:
        msgs = await client.get_messages(channel, limit=1, search=kw)
        if msgs and msgs[0]:
            if latest_msg is None or msgs[0].date > latest_msg.date:
                latest_msg = msgs[0]
    return latest_msg


async def reply_with_status(update: Update, border_name: str, status_info: dict, timestamp_str: str):
    status = status_info.get("status")
    sub_status = status_info.get("sub_status")
    last_seen_message = status_info.get("last_seen_message")
    
    header = ""
    if status == "🟢":
        header = f"✅ **{escape_md(border_name)}**: سالك! الأمور ماشية زي السكر."
    elif status == "🔴":
        header = f"❌ **{escape_md(border_name)}**: إغلاق! الطريق مغلق حالياً."
    elif status == "⚠️":
        if sub_status == "traffic_stopping":
            header = f"⚠️ **{escape_md(border_name)}**: ازمة سير خانقة. الطريق واقف تماماً."
        elif sub_status == "traffic_high":
            header = f"⚠️ **{escape_md(border_name)}**: ازمة سير قوية. ممكن تأخير."
        elif sub_status == "traffic_medium":
            header = f"⚠️ **{escape_md(border_name)}**: في شوية بطء بالسير."
        elif sub_status == "police_presence":
            header = f"⚠️ **{escape_md(border_name)}**: في تواجد أمني. الرجاء الحذر.\n\n`{escape_md(last_seen_message or '')}`"
        elif sub_status == "road_event":
            # Identify the specific event from the message
            road_events = ["حادث", "عرقلة", "مشاة", "تجمع"]
            event = next((e for e in road_events if e in (last_seen_message or '')), "عرقلة")
            header = f"⚠️ **{escape_md(border_name)}**: في {event} على الطريق. الرجاء توخي الحذر."
        else:
            # Fallback for general caution if a sub_status is not found
            header = f"⚠️ **{escape_md(border_name)}**: في شوية تأخير. ممكن تعدي، بس بالصبر."
    else:
        # For unclear messages, just send the full message content
        cleaned_message = (last_seen_message or '').replace('`', '"')
        header = f"ℹ️ **{escape_md(border_name)}**:\n`{escape_md(cleaned_message)}`"
    
    try:
        update_time = datetime.fromisoformat(timestamp_str)
        jerusalem_tz = pytz.timezone("Asia/Jerusalem")
        now_jerusalem = datetime.now(jerusalem_tz)
        today = now_jerusalem.date()
        yesterday = today - timedelta(days=1)
        date_text = "اليوم" if update_time.date() == today else "أمس" if update_time.date() == yesterday else update_time.strftime("%Y-%m-%d")
        time_text = update_time.strftime("%I:%M %p")
        footer = f"\n\n🕒 آخر تحديث: {date_text} - {time_text}"
    except (ValueError, TypeError):
        footer = ""
    
    await update.message.reply_text(header + footer, parse_mode='Markdown')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = "👋 أهلاً! أنا بوت أحوال الطرق والمعابر.\nأرسل اسم المعبر وسأوافيك بآخر التحديثات."
    await update.message.reply_text(welcome_message)

async def check_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_user_stats()
    total_queries = stats.get("total_queries", 0)
    top_borders = sorted(stats.get("border_queries", {}).items(), key=lambda item: item[1], reverse=True)[:5]
    last_updated = stats.get("last_updated", "N/A")
    
    reply = f"📊 **إحصائيات استخدام البوت**\n\nإجمالي الاستعلامات: {total_queries}\n"
    reply += "أكثر 5 معابر تم الاستعلام عنها:\n"
    for border, count in top_borders:
        reply += f"  • {border}: {count} استعلام\n"
    reply += f"\nآخر استعلام تمت معالجته: {last_updated}"
    
    await update.message.reply_text(reply, parse_mode='Markdown')

async def check_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userbot_status = get_userbot_status()
    last_update_str = userbot_status.get("last_update_timestamp", "N/A")
    mode = userbot_status.get("mode", "N/A")
    reply = f"🔄 **حالة تحديث البوت**\n\nوضع التحديث: `{mode}`\nآخر تحديث لملف `borders.json`: {last_update_str}\n"
    await update.message.reply_text(reply, parse_mode='Markdown')


async def main():
    global config, status_data, names, mapping
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    config = load_config()
    TOKEN = config["BOT_TOKEN"]
    API_ID = int(config["API_ID"])
    API_HASH = config["API_HASH"]
    SESSION_NAME = config["SESSION_NAME"]
    CHANNEL_LINK = config["CHANNEL_LINK"]

    status_data, names, mapping = load_data(config["STATUS_FILE"], MAPPING_FILE)

    application = Application.builder().token(TOKEN).build()
    telethon_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await telethon_client.start()
    channel_entity = await telethon_client.get_entity(CHANNEL_LINK)

    # Store shared objects
    application.bot_data["telethon_client"] = telethon_client
    application.bot_data["channel_entity"] = channel_entity

    # Register the real-time event handler
    telethon_client.add_event_handler(process_message, events.NewMessage(chats=channel_entity))

    # Register PTB handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("usage", check_usage))
    application.add_handler(CommandHandler("updates", check_updates))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_query))
    
    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        # Run indefinitely and let event handlers do the work
        await telethon_client.run_until_disconnected()
        await application.updater.stop()
        await application.stop()
        await telethon_client.disconnect()


if __name__ == "__main__":

    asyncio.run(main())
