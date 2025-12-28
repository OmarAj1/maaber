Maaber Bot (مــعــابــر) 🚦

Maaber Bot is a high-performance, asynchronous Telegram bot designed to monitor and report real-time traffic and checkpoint statuses in Palestine.

By combining a Telethon Userbot (listener) with a Python-Telegram-Bot (responder), Maaber Bot acts as a bridge: it continuously listens to a dedicated status channel, parses unstructured text updates using fuzzy logic, and serves instant, structured answers to user queries.

🌟 Key Features

Hybrid Architecture: Uses Telethon to listen to channel updates in real-time and python-telegram-bot to handle user interactions concurrently.

Smart Status Parsing:

Detects Open (🟢), Closed (🔴), and Caution (⚠️) states.

Identifies sub-conditions like heavy traffic, police presence, or road accidents.

Handles mixed signals (e.g., "Was closed, now open") using weighted precedence logic.

Fuzzy Search: Powered by rapidfuzz to understand user typos and colloquialisms (e.g., matching "Qalandia" with "kalandia").

Optimized Performance:

In-Memory Caching: Serves requests instantly without disk I/O latency.

Background Persistence: Asynchronously saves statistics and data to disk to prevent data loss without blocking the main thread.

Analytics: Tracks most frequently queried borders and logs unknown queries for future mapping improvements.

🛠️ Tech Stack

Language: Python 3.9+

Core Libraries:

python-telegram-bot (Interaction Handler)

Telethon (Channel Listener)

rapidfuzz (Fuzzy String Matching)

pytz (Timezone Handling)

🚀 Installation & Setup

1. Clone the Repository

git clone [https://github.com/yourusername/maaber-bot.git](https://github.com/yourusername/maaber-bot.git)
cd maaber-bot


2. Install Dependencies

Ensure you have Python installed, then run:

pip install -r requirements.txt


3. Environment Configuration

The bot relies on environment variables for security. Create a .env file or configure your deployment environment (e.g., Heroku, Docker) with the following keys:

Variable

Description

BOT_TOKEN

Your Telegram Bot API Token (from @BotFather).

API_ID

Your Telegram App API ID (from my.telegram.org).

API_HASH

Your Telegram App API Hash.

SESSION_NAME

Name for the Telethon session file (e.g., userbot_session).

CHANNEL_LINK

The username or link of the channel to monitor (e.g., @ahwalaltreq).

STATUS_FILE

Path to the status database (e.g., borders.json).

4. Data Files

Ensure the following JSON files exist in your root directory (or let the bot create empty ones):

borders_mapping.json: A dictionary mapping canonical border names to list of keywords/synonyms.

{
  "Qalandia": ["Qalandia", "Kalandia", "calandia"],
  "Jericho": ["Jericho", "Ariha"]
}


▶️ Usage

To start the bot locally:

python maaber_bot.py


Upon startup, the bot will:

Load existing data into memory.

Start the Telethon client to listen for new channel messages.

Start the Bot API poller to reply to users.

Launch a background task to save data every 60 seconds.

📂 File Structure

maaber_bot.py: The main application logic, containing the event loop, parsers, and handlers.

borders_mapping.json: Configuration file defining synonyms for checkpoints.

borders.json: (Generated) Stores the current status of all checkpoints.

usage_stats.json: (Generated) Tracks user query statistics.

unknown_queries.json: (Generated) Logs unrecognized user inputs for review.

requirements.txt: Python dependency list.

🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Fork the project.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

⚠️ Disclaimer

This bot relies on parsing user-generated content from third-party Telegram channels. The accuracy of the status reports depends entirely on the source channel's accuracy and the clarity of the text messages. The developers are not responsible for decisions made based on this information.
