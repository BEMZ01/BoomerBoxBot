# Quick Start Guide - BoomerBox Bot

## What This Bot Does

✅ **Monitors** submission channel for Instagram URLs
✅ **Downloads** Instagram content via your Cobalt API
✅ **Reposts** content as Discord attachments
✅ **Deletes** the original Instagram link automatically
✅ **Showcases** a random submission daily at 12:00 PM

## Files

- `main.py` - The main bot code
- `requirements.txt` - Python dependencies
- `README.md` - Full documentation
- `.env` - Your configuration (already exists)
- `.env.example` - Configuration template
- `.gitignore` - Protects sensitive files
- `start_bot.bat` - Easy startup script

## Quick Setup

1. **Install Dependencies** (if not already done):
   ```
   .venv\Scripts\pip.exe install discord.py requests python-dotenv
   ```

2. **Configure Discord Bot**:
   - Go to https://discord.com/developers/applications
   - Create a bot or use existing one
   - Enable "Message Content Intent" under Bot → Privileged Gateway Intents
   - Copy your bot token to the .env file (already done)

3. **Invite Bot to Server**:
   Use this URL (replace YOUR_CLIENT_ID):
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274878024704&scope=bot%20applications.commands
   ```
   **Note:** Make sure to include `applications.commands` scope for slash commands!

4. **Run the Bot**:
   - Double-click `start_bot.bat` OR
   - Run: `.venv\Scripts\python.exe main.py`

## How to Use

1. In any Discord channel, type: `/setup`
   - Select a submission channel (where users post)
   - Select a showcase channel (where daily highlights go)
   - Requires "Manage Channels" permission

2. In the submission channel, post:
   - Instagram URLs: `https://www.instagram.com/p/ABC123/`
   - Regular content: images, videos, text
   
3. For Instagram URLs, the bot will:
   - ✅ Detect the URL
   - ✅ Download the content via Cobalt
   - ✅ Repost it with attribution
   - ✅ Delete your original Instagram link

4. Daily at 12:00 PM:
   - ✅ Bot picks a random post from submission channel
   - ✅ Showcases it in the showcase channel with a beautiful embed

## Slash Commands

All commands use Discord's slash command interface (type `/` to see them):

- `/setup` - Configure submission and showcase channels
- `/showcase_now` - Manually showcase a post immediately
- `/status` - Show current configuration and last showcase date

## Troubleshooting

**Slash commands don't appear:**
- Make sure you invited the bot with the `applications.commands` scope
- Wait a few minutes for commands to sync (can take up to 1 hour globally)
- Commands will appear when you type `/` in Discord

**Bot doesn't respond:**
- Check that "Message Content Intent" is enabled
- Verify bot has proper permissions

**Can't delete messages:**
- Bot needs "Manage Messages" permission
- Check role hierarchy

**Download fails:**
- Verify COBALT_API_URL and COBALT_API_KEY in .env
- Test your Cobalt instance manually

## Your Current Configuration

Your .env file is already configured with:
- Discord Token: ✓
- Cobalt API URL: https://cobalt.bemz.info
- Cobalt API Key: ✓
- User Agent: BoomerBox/1.0

You're ready to run the bot!

