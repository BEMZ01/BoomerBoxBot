# BoomerBox Discord Bot

A Discord bot that automatically downloads Instagram content from a submission channel using Cobalt.tools, and randomly showcases user submissions once per day.

## Features

- 🔍 **Instagram Link Detection**: Automatically detects and processes Instagram URLs in submission channel
- 📥 **Media Download**: Fetches media using your self-hosted Cobalt.tools API
- 📤 **Discord Repost**: Uploads downloaded content as Discord attachments
- 🗑️ **Auto-Cleanup**: Deletes the original Instagram link after successful download
- 🎠 **Carousel Support**: Handles Instagram posts with multiple images/videos
- 🎲 **Random Selection**: Picks a random post from the submission channel daily
- 🌟 **Showcase Posts**: Creates beautiful embeds with user attribution
- 🕐 **Scheduled Daily**: Automatically runs at 12:00 PM every day
- ⚙️ **Easy Setup**: Simple configuration with a single command
- 💾 **Persistent Configuration**: Settings are saved and restored on bot restart
- 🎯 **Manual Override**: Ability to showcase a post immediately on demand

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token_here
COBALT_API_URL=https://your-cobalt-instance.com
COBALT_API_KEY=your_cobalt_api_key_here
COBALT_USER_AGENT=BoomerBox/1.0
CLOUDFLARE_BYPASS_HEADER=optional_cf_header_name
CLOUDFLARE_BYPASS_VALUE=optional_cf_header_value
```

#### Getting Your Discord Bot Token:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select an existing one
3. Go to the "Bot" section
4. Click "Reset Token" to get your bot token
5. **Important**: Enable the "Message Content Intent" under Privileged Gateway Intents

#### Bot Permissions:

Your bot needs these permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Manage Messages (to delete original Instagram links)

Use this permission integer when adding the bot: `274878024704`

### 3. Run the Bot

```bash
python main.py
```

## Commands

All commands require the "Manage Channels" permission and are slash commands:

- `/setup <submission_channel> <showcase_channel>` - Configure which channel to pull submissions from and where to showcase them
- `/showcase_now` - Manually trigger a showcase post immediately (won't affect the daily scheduled showcase)
- `/status` - Display current configuration and last showcase date

## Usage Example

1. Run `/setup` and select a submission channel and a showcase channel
2. Users post content in the submission channel:
   - Regular text/image posts
   - Instagram URLs (e.g., `https://www.instagram.com/reel/ABC123/`)
3. When Instagram URLs are posted, the bot will:
   - Detect the URL automatically
   - Download the media via Cobalt API
   - Repost it as a Discord attachment
   - Delete the original Instagram link
4. Every day at 12:00 PM, the bot will:
   - Randomly select one post from the submission channel (last 100 messages)
   - Create a beautiful embed with the user's content
   - Post it to the showcase channel with proper attribution
5. Use `/showcase_now` if you want to manually showcase a post immediately

## How It Works

### Instagram Processing (Real-time)
1. **Message Monitoring**: Bot listens to all messages in the submission channel
2. **URL Detection**: Uses regex to find Instagram URLs (posts, reels, TV)
3. **Cobalt API**: Sends the URL to your Cobalt instance to get a download link
4. **Media Download**: Streams the media content into memory
5. **Discord Upload**: Uploads the media as a Discord attachment with attribution
6. **Cleanup**: Deletes the original Instagram link message

### Daily Showcase (Scheduled)
1. **Configuration**: Admin uses `/setup` to designate submission and showcase channels
2. **Daily Task**: At 12:00 PM every day, the bot runs automatically
3. **Random Selection**: Bot fetches last 100 messages from submission channel
4. **Filtering**: Ignores bot messages and empty posts
5. **Random Pick**: Selects one post randomly using Python's `random.choice()`
6. **Showcase**: Creates an embed with:
   - User's display name and avatar
   - Original message content
   - All attachments (images/videos)
   - Timestamp and source channel
7. **Post**: Sends the showcase to the designated showcase channel

### Persistence & Scheduling

- **Configuration Storage**: Channel settings are saved to `bot_config.json`
- **Date Tracking**: Remembers the last showcase date to prevent duplicates
- **Automatic Restoration**: Settings persist across bot restarts
- **Scheduled Tasks**: Uses discord.py's `@tasks.loop` for reliable daily execution
- **Time Zone**: Runs at 12:00 PM in the server's time zone

## Showcase Features

- **Smart Filtering**: Only considers messages from real users (ignores bots)
- **Content Validation**: Ensures showcased posts have content or attachments
- **Beautiful Embeds**: Professional-looking showcase posts with proper formatting
- **Attribution**: Always credits the original author with name and avatar
- **Attachment Support**: Handles multiple types of media (images, videos, etc.)
- **One Per Day**: Prevents spam by limiting to one showcase per day
- **Manual Override**: Use `/showcase_now` for immediate showcases without affecting daily schedule

## Supported Instagram Content

- Instagram Posts (single image/video)
- Instagram Reels
- Instagram TV (IGTV)
- Instagram Carousels (multiple images/videos)

## Error Handling

The bot handles various errors gracefully:
- Invalid Cobalt API responses
- Download failures
- Missing or deleted channels
- Permission errors
- Attachment download failures
- Empty submission channels
- Network timeouts

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot has proper permissions in the channel
- Verify the "Message Content Intent" is enabled in the Discord Developer Portal

### Can't delete original messages
- The bot needs "Manage Messages" permission
- Check the role hierarchy (bot's role should be high enough)

### Download failures
- Verify your Cobalt API URL and key are correct
- Check that your Cobalt instance is running and accessible
- Some Instagram content may be protected or unavailable

## Technical Details

- **Language**: Python 3.7+
- **Framework**: discord.py 2.0+
- **API**: Cobalt.tools for media downloading
- **Async**: Fully asynchronous for efficient performance

## License

This project is open source and available for personal and educational use.

