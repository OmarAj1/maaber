# Maaber Bot (مــعــابــر) 🚦

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

**Maaber Bot** is a high-performance, asynchronous Telegram bot designed to monitor and report real-time traffic and checkpoint statuses in Palestine.

By combining a **Telethon Userbot** (listener) with a **Python-Telegram-Bot** (responder), Maaber Bot acts as a bridge: it continuously listens to a dedicated status channel, parses unstructured text updates using fuzzy logic, and serves instant, structured answers to user queries.

---

## 🌟 Key Features

* **Hybrid Architecture:** Uses `Telethon` to listen to channel updates in real-time and `python-telegram-bot` to handle user interactions concurrently.
* **Smart Status Parsing:**
    * Detects **Open** (🟢), **Closed** (🔴), and **Caution** (⚠️) states.
    * Identifies sub-conditions like heavy traffic, police presence, or road accidents.
    * Handles mixed signals (e.g., "Was closed, now open") using weighted precedence logic.
* **Fuzzy Search:** Powered by `rapidfuzz` to understand user typos and colloquialisms (e.g., matching "Qalandia" with "kalandia").
* **Optimized Performance:**
    * **In-Memory Caching:** Serves requests instantly without disk I/O latency.
    * **Background Persistence:** Asynchronously saves statistics and data to disk to prevent data loss without blocking the main thread.
* **Analytics:** Tracks most frequently queried borders and logs unknown queries for future mapping improvements.

---

## 🛠️ Tech Stack

* **Language:** Python 3.9+
* **Core Libraries:**
    * `python-telegram-bot` (Interaction Handler)
    * `Telethon` (Channel Listener)
    * `rapidfuzz` (Fuzzy String Matching)
    * `pytz` (Timezone Handling)

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/maaber-bot.git](https://github.com/yourusername/maaber-bot.git)
cd maaber-bot
```

### 2. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
The bot relies on environment variables for security. Create a `.env` file in the root directory or configure your deployment environment (e.g., Heroku, Docker) with the following keys:

```env
BOT_TOKEN=Your_Telegram_Bot_Token_From_BotFather
API_ID=Your_Telegram_App_API_ID
API_HASH=Your_Telegram_App_API_Hash
SESSION_NAME=userbot_session
CHANNEL_LINK=@ahwalaltreq
STATUS_FILE=borders.json
```

### 4. Data Files
Ensure a `borders_mapping.json` file exists in your root directory. This maps canonical border names to keywords/synonyms.

**Example `borders_mapping.json`:**
```json
{
  "Qalandia": ["Qalandia", "Kalandia", "calandia"],
  "Jericho": ["Jericho", "Ariha"],
  "DCO": ["DCO", "Mahkama", "Beit El"]
}
```

---

## ▶️ Usage

To start the bot locally:

```bash
python maaber_bot.py
```

**Upon startup, the bot will:**
1.  Load existing data into memory.
2.  Start the Telethon client to listen for new channel messages.
3.  Start the Bot API poller to reply to users.
4.  Launch a background task to save data every 60 seconds.

---

## 📂 File Structure

* `maaber_bot.py`: The main application logic (event loop, parsers, and handlers).
* `borders_mapping.json`: Configuration file defining synonyms for checkpoints.
* `borders.json`: *(Generated)* Stores the current status of all checkpoints.
* `usage_stats.json`: *(Generated)* Tracks user query statistics.
* `unknown_queries.json`: *(Generated)* Logs unrecognized user inputs for review.
* `requirements.txt`: Python dependency list.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## ⚠️ Disclaimer

This bot relies on parsing user-generated content from third-party Telegram channels. The accuracy of the status reports depends entirely on the source channel's accuracy and the clarity of the text messages. The developers are not responsible for decisions made based on this information.
