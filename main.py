import discord
from discord.ext import commands, tasks
import requests
import json
from dotenv import load_dotenv
import os
import re
import io
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import random

# --- Configuration ---

load_dotenv()

# --- End Configuration ---

# Regular expression to match Instagram URLs
INSTAGRAM_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+/?(?:\?[^\s]*)?',
    re.IGNORECASE
)



def get_download_link(api_url: str, api_key: Optional[str], media_url: str,
                     bypass_header_name: Optional[str] = None,
                     bypass_header_value: Optional[str] = None,
                     user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches a download link from a self-hosted cobalt.tools API.
    Returns a dict with status and download info, or None on error.
    """

    # 1. Set up headers based on api.md documentation
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Add User-Agent header (required for API key authentication)
    if user_agent:
        headers["User-Agent"] = user_agent

    # Only add Authorization header if api_key is provided
    if api_key:
        headers["Authorization"] = f"Api-Key {api_key}"

    # Add Cloudflare Bypass Header if provided
    if bypass_header_name and bypass_header_value:
        headers[bypass_header_name] = bypass_header_value

    # 2. Set up the payload (request body)
    payload = {
        "url": media_url,
        "videoQuality": "1080"  # Request 1080p, cobalt gets best available
    }

    print(f"Requesting download for: {media_url}")

    try:
        # 3. Make the POST request to the API
        response = requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        # Raise an exception for bad HTTP status codes
        response.raise_for_status()

        # 4. Parse the JSON response
        data = response.json()

        # 5. Return the parsed data
        return data

    except requests.exceptions.HTTPError as err:
        print(f"❌ HTTP Error: {err}")
        if err.response:
            print(f"   Response body: {err.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ A connection error occurred: {e}")
        return None


async def download_media(url: str) -> Optional[io.BytesIO]:
    """
    Downloads media from a URL and returns it as a BytesIO object.
    """
    try:
        print(f"Downloading media from: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        # Read the content into a BytesIO object
        media_data = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            media_data.write(chunk)

        media_data.seek(0)
        print(f"✅ Downloaded {len(media_data.getvalue())} bytes")
        return media_data

    except Exception as e:
        print(f"❌ Error downloading media: {e}")
        return None

class BoomerBoxBot(commands.Bot):
    def __init__(self, **options):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='!', intents=intents, **options)

        # Load configuration from environment
        self.cobalt_url = os.environ.get("COBALT_API_URL")
        self.cobalt_key = os.environ.get("COBALT_API_KEY")
        self.cf_header = os.environ.get("CLOUDFLARE_BYPASS_HEADER")
        self.cf_value = os.environ.get("CLOUDFLARE_BYPASS_VALUE")
        self.user_agent = os.environ.get("COBALT_USER_AGENT")

        # Store bot configuration
        self.config_file = Path("guild_configs.json")
        self.guild_configs: Dict[int, Dict] = {}
        self.load_config()

    def save_config(self):
        """Save all guild configurations to a JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.guild_configs, f, indent=2)
            print(f"✅ Saved configuration for {len(self.guild_configs)} guild(s)")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")

    def load_config(self):
        """Load all guild configurations from JSON file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    self.guild_configs = {int(k): v for k, v in data.items()}
                print(f"✅ Loaded configuration for {len(self.guild_configs)} guild(s)")
            else:
                print("ℹ️ No existing configuration file found, starting fresh")
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            self.guild_configs = {}

    def get_guild_config(self, guild_id: int) -> Dict:
        """Get the configuration for a specific guild, creating it if it doesn't exist."""
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = {
                "submission_channel_id": None,
                "showcase_channel_id": None,
                "last_showcase_date": None,
                "showcase_time": "12:00",
                "delete_after_showcase": True
            }
        return self.guild_configs[guild_id]

    async def pick_and_showcase_post(self, guild_id: int):
        """Randomly pick a post from a guild's submission channel and showcase it."""
        guild_config = self.get_guild_config(guild_id)

        submission_channel_id = guild_config.get("submission_channel_id")
        showcase_channel_id = guild_config.get("showcase_channel_id")

        if not submission_channel_id or not showcase_channel_id:
            print(f"⚠️ Channels not configured for guild {guild_id}. Skipping showcase.")
            return

        submission_channel = self.get_channel(submission_channel_id)
        showcase_channel = self.get_channel(showcase_channel_id)

        if not submission_channel or not showcase_channel:
            print(f"❌ Could not find configured channels for guild {guild_id}")
            return

        print(f"\n🎲 Selecting random post from {submission_channel.name} in guild {guild_id}...")

        try:
            # Collect all messages from submission channel (last 100)
            messages = []
            async for message in submission_channel.history(limit=100):
                # Include messages from users, or from the bot if it has attachments
                if (not message.author.bot and (message.content or message.attachments)) or \
                   (message.author == self.user and message.attachments):
                    messages.append(message)

            if not messages:
                print(f"⚠️ No messages found in submission channel for guild {guild_id}")
                await showcase_channel.send("📢 No submissions to showcase today!")
                return

            # Pick a random message
            chosen_message = random.choice(messages)
            print(f"✅ Selected message from {chosen_message.author} in guild {guild_id}")

            # Create showcase post
            embed = discord.Embed(
                title="🌟 Daily Showcase",
                description=chosen_message.content if chosen_message.content else "",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            embed.set_author(name=chosen_message.author.display_name, icon_url=chosen_message.author.display_avatar.url)

            # Calculate next showcase time for the footer
            now = datetime.now()
            showcase_time_str = guild_config.get('showcase_time', '12:00')
            showcase_hour, showcase_minute = map(int, showcase_time_str.split(':'))
            next_showcase_dt = now.replace(hour=showcase_hour, minute=showcase_minute, second=0, microsecond=0)
            if now >= next_showcase_dt:
                next_showcase_dt += timedelta(days=1)

            embed.add_field(
                name="⏳ Next Showcase",
                value=f"<t:{int(next_showcase_dt.timestamp())}:R>",
                inline=False
            )

            # Handle attachments
            files = []
            if chosen_message.attachments:
                for attachment in chosen_message.attachments:
                    try:
                        # Download attachment
                        file_data = await attachment.read()
                        files.append(discord.File(io.BytesIO(file_data), filename=attachment.filename))

                        # Set first image as embed thumbnail
                        if attachment.content_type and attachment.content_type.startswith("image") and not embed.image:
                            embed.set_image(url=attachment.url)
                    except Exception as e:
                        print(f"⚠️ Could not process attachment: {e}")

            # Post to showcase channel
            if files:
                await showcase_channel.send(embed=embed, files=files)
            else:
                await showcase_channel.send(embed=embed)

            print(f"✅ Showcased post in {showcase_channel.name} for guild {guild_id}")

            # Delete original message if configured
            if guild_config.get("delete_after_showcase", False):
                try:
                    await chosen_message.delete()
                    print(f"🗑️ Deleted showcased message from {submission_channel.name}")
                except discord.Forbidden:
                    print(f"⚠️ Missing permissions to delete message in {submission_channel.name}")
                except Exception as e:
                    print(f"⚠️ Could not delete showcased message: {e}")

            # Update last showcase date
            guild_config["last_showcase_date"] = datetime.now().strftime("%Y-%m-%d")
            self.save_config()

        except discord.Forbidden:
            print(f"❌ Missing permissions in channels for guild {guild_id}")
        except Exception as e:
            print(f"❌ Error during showcase for guild {guild_id}: {e}")

    @tasks.loop(minutes=1)  # Check every minute
    async def daily_showcase_task(self):
        """Daily task to showcase a random post for each guild."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        for guild_id, config in self.guild_configs.items():
            showcase_time = config.get("showcase_time", "12:00")
            last_showcase_date = config.get("last_showcase_date")

            if current_time_str == showcase_time and last_showcase_date != today_str:
                print(f"🚀 Triggering showcase for guild {guild_id} at {showcase_time}")
                await self.pick_and_showcase_post(guild_id)

    @daily_showcase_task.before_loop
    async def before_daily_showcase(self):
        """Wait until the bot is ready before starting the task."""
        await self.wait_until_ready()
        print("🕐 Daily showcase task started (runs every minute to check for scheduled showcases)")


    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'✅ Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        # Start the daily showcase task
        if not self.daily_showcase_task.is_running():
            self.daily_showcase_task.start()

        print('🤖 Bot is ready!')

    async def on_message(self, message: discord.Message):
        """Called when a message is received."""
        # Don't respond to our own messages or DMs
        if message.author == self.user or not message.guild:
            return

        # Process commands first
        await self.process_commands(message)

        # Check if this is a configured submission channel for this guild
        guild_config = self.get_guild_config(message.guild.id)
        submission_channel_id = guild_config.get("submission_channel_id")

        if not submission_channel_id or message.channel.id != submission_channel_id:
            return

        # Check for supported URLs
        instagram_urls = INSTAGRAM_URL_PATTERN.findall(message.content)

        # If a supported URL is found, process it
        if instagram_urls:
            print(f"Found {len(instagram_urls)} Instagram URL(s) in message from {message.author} in guild {message.guild.id}")
            for url in instagram_urls:
                await self.process_instagram_url(message, url)
            return

        # If the message has no attachments and no supported URLs, delete it.
        if not message.attachments:
            try:
                await message.delete()
                print(f"🗑️ Deleted message from {message.author} in {message.channel.name} (no attachment or supported URL)")
            except discord.Forbidden:
                print(f"⚠️ Missing permissions to delete message in {message.channel.name}")
            except Exception as e:
                print(f"⚠️ Could not delete message: {e}")

    async def process_instagram_url(self, message: discord.Message, url: str):
        """Process an Instagram URL: download it and repost it."""
        try:
            # Send a status message
            status_msg = await message.channel.send(f"🔄 Processing Instagram link...", delete_after=60)

            # Get download link from Cobalt
            cobalt_response = await asyncio.to_thread(
                get_download_link,
                self.cobalt_url,
                self.cobalt_key,
                url,
                self.cf_header,
                self.cf_value,
                self.user_agent
            )

            if not cobalt_response:
                await status_msg.edit(content="❌ Failed to get download link from Cobalt.")
                return

            status = cobalt_response.get("status")

            if status in ("redirect", "tunnel"):
                # Single video/image
                download_url = cobalt_response.get("url")
                if download_url:
                    await self.download_and_post(message, download_url, status_msg)

            elif status == "picker":
                # Multiple items (carousel)
                picker_items = cobalt_response.get("picker", [])
                if picker_items:
                    await status_msg.edit(content=f"🔄 Downloading {len(picker_items)} items from carousel...")

                    for idx, item in enumerate(picker_items):
                        item_url = item.get("url")
                        if item_url:
                            await self.download_and_post(message, item_url, status_msg if idx == 0 else None, item_num=idx+1, total_items=len(picker_items))

            elif status == "error":
                error_code = cobalt_response.get("error", {}).get("code", "unknown")
                error_text = cobalt_response.get("text", "Unknown error")
                await status_msg.edit(content=f"❌ Cobalt error: {error_code} - {error_text}")
                return

            else:
                await status_msg.edit(content=f"❔ Unknown Cobalt response status: {status}")
                return

            # Delete the status message after a short delay
            await asyncio.sleep(2)
            await status_msg.delete()

        except Exception as e:
            print(f"❌ Error processing Instagram URL: {e}")
            await message.channel.send(f"❌ Error processing link: {str(e)}", delete_after=30)

    async def download_and_post(self, original_message: discord.Message, download_url: str,
                                status_msg: Optional[discord.Message] = None,
                                item_num: int = 0, total_items: int = 1, source: str = "Instagram content"):
        """Download media and post it as a Discord attachment."""
        try:
            # Download the media
            media_data = await download_media(download_url)

            if not media_data:
                if status_msg:
                    await status_msg.edit(content="❌ Failed to download media.")
                return

            # Determine file extension from URL
            file_ext = ".mp4"  # Default to mp4
            if ".jpg" in download_url or ".jpeg" in download_url:
                file_ext = ".jpg"
            elif ".png" in download_url:
                file_ext = ".png"

            filename = f"instagram_media{f'_{item_num}' if total_items > 1 else ''}{file_ext}"

            # Create Discord file object
            discord_file = discord.File(media_data, filename=filename)

            # Post the media with attribution
            content = f"📹 Instagram content from {original_message.author.mention}"
            if total_items > 1:
                content += f" (Item {item_num}/{total_items})"

            await original_message.channel.send(content=content, file=discord_file)

            # If this is the last item, delete the original message
            if item_num == total_items or total_items == 1:
                try:
                    await original_message.delete()
                    print(f"✅ Deleted original message from {original_message.author}")
                except discord.Forbidden:
                    print("⚠️ Missing permissions to delete message")
                except Exception as e:
                    print(f"⚠️ Could not delete original message: {e}")

        except Exception as e:
            print(f"❌ Error posting media: {e}")
            if status_msg:
                await status_msg.edit(content=f"❌ Error posting media: {str(e)}")

# --- Run the bot ---
if __name__ == "__main__":
    bot_options = {}
    debug_guild_ids = os.environ.get("DISCORD_DEBUG_GUILD_IDS")
    if debug_guild_ids:
        print(f"🐛 Running in debug mode for guilds: {debug_guild_ids}")
        bot_options["debug_guilds"] = [int(gid) for gid in debug_guild_ids.split(",")]

    bot = BoomerBoxBot(**bot_options)

    # Slash Commands
    @bot.slash_command(name="setup", description="Configure submission, showcase channels, and showcase time")
    @commands.has_permissions(manage_guild=True)
    async def setup_command(
        ctx: discord.ApplicationContext,
        submission_channel: discord.Option(discord.TextChannel, description="Channel where users submit posts"),
        showcase_channel: discord.Option(discord.TextChannel, description="Channel where featured posts are showcased"),
        showcase_time: discord.Option(str, description="Time to showcase posts (HH:MM format, e.g., 14:30)", default="12:00")
    ):
        """Configure the bot for this server."""
        guild_config = bot.get_guild_config(ctx.guild.id)

        # Validate time format
        try:
            datetime.strptime(showcase_time, "%H:%M")
        except ValueError:
            await ctx.respond("❌ Invalid time format. Please use HH:MM (e.g., 14:30).", ephemeral=True, delete_after=30)
            return

        guild_config["submission_channel_id"] = submission_channel.id
        guild_config["showcase_channel_id"] = showcase_channel.id
        guild_config["showcase_time"] = showcase_time
        bot.save_config()

        await ctx.respond(
            f"✅ Configuration updated!\n"
            f"📥 Submission channel: {submission_channel.mention}\n"
            f"🌟 Showcase channel: {showcase_channel.mention}\n"
            f"⏰ Showcase time: {showcase_time} daily"
        , ephemeral=True, delete_after=15)

    @bot.slash_command(name="showcase_now", description="Immediately showcase a random post")
    @commands.has_permissions(manage_guild=True)
    async def showcase_now_command(ctx: discord.ApplicationContext):
        """Manually trigger a showcase post for this server."""
        await ctx.defer()

        guild_config = bot.get_guild_config(ctx.guild.id)
        if not guild_config.get("submission_channel_id") or not guild_config.get("showcase_channel_id"):
            await ctx.respond("❌ Please configure channels first using `/setup`", ephemeral=True, delete_after=30)
            return

        # Temporarily allow showcasing even if already done today
        original_date = guild_config.get("last_showcase_date")
        guild_config["last_showcase_date"] = None

        await bot.pick_and_showcase_post(ctx.guild.id)

        # Restore original date so daily task won't run again today
        guild_config["last_showcase_date"] = original_date
        bot.save_config()

        await ctx.respond("✅ Showcase posted!", ephemeral=True, delete_after=15)

    @bot.slash_command(name="status", description="Show bot configuration and status for this server")
    @commands.has_permissions(manage_guild=True)
    async def status_command(ctx: discord.ApplicationContext):
        """Display the current bot configuration for this server."""
        guild_config = bot.get_guild_config(ctx.guild.id)

        submission_channel_id = guild_config.get("submission_channel_id")
        showcase_channel_id = guild_config.get("showcase_channel_id")

        if not submission_channel_id or not showcase_channel_id:
            await ctx.respond("ℹ️ Bot is not configured yet. Use `/setup` to configure channels.", ephemeral=True, delete_after=30)
            return

        submission_channel = bot.get_channel(submission_channel_id)
        showcase_channel = bot.get_channel(showcase_channel_id)

        embed = discord.Embed(
            title=f"🤖 Bot Status for {ctx.guild.name}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📥 Submission Channel",
            value=submission_channel.mention if submission_channel else "❌ Not found",
            inline=False
        )

        embed.add_field(
            name="🌟 Showcase Channel",
            value=showcase_channel.mention if showcase_channel else "❌ Not found",
            inline=False
        )

        embed.add_field(
            name="📅 Last Showcase",
            value=guild_config.get("last_showcase_date", "Never"),
            inline=True
        )

        embed.add_field(
            name="⏰ Showcase Time",
            value=f"Daily at {guild_config.get('showcase_time', '12:00')}",
            inline=True
        )

        delete_status = "✅ Enabled" if guild_config.get('delete_after_showcase') else "❌ Disabled"
        embed.add_field(
            name="🗑️ Delete After Showcase",
            value=delete_status,
            inline=True
        )

        # Calculate next showcase time
        now = datetime.now()
        showcase_time_str = guild_config.get('showcase_time', '12:00')
        showcase_hour, showcase_minute = map(int, showcase_time_str.split(':'))
        next_showcase_dt = now.replace(hour=showcase_hour, minute=showcase_minute, second=0, microsecond=0)
        if now >= next_showcase_dt:
            next_showcase_dt += timedelta(days=1)

        embed.add_field(
            name="⏳ Next Showcase",
            value=f"<t:{int(next_showcase_dt.timestamp())}:R>",
            inline=False
        )

        await ctx.respond(embed=embed, ephemeral=True, delete_after=60)

    @bot.slash_command(name="settings", description="Modify bot settings for this server")
    @commands.has_permissions(manage_guild=True)
    async def settings_command(
        ctx: discord.ApplicationContext,
        showcase_time: discord.Option(str, description="Time to showcase posts (HH:MM format, e.g., 14:30)", required=False),
        delete_after_showcase: discord.Option(bool, description="Delete submission after it's showcased?", required=False)
    ):
        """Modify bot settings for this server."""
        guild_config = bot.get_guild_config(ctx.guild.id)
        updated_settings = []

        if showcase_time is not None:
            # Validate time format
            try:
                datetime.strptime(showcase_time, "%H:%M")
                guild_config["showcase_time"] = showcase_time
                updated_settings.append(f"⏰ Showcase time updated to **{showcase_time}** daily.")
            except ValueError:
                await ctx.respond("❌ Invalid time format for `showcase_time`. Please use HH:MM (e.g., 14:30).", ephemeral=True, delete_after=30)
                return

        if delete_after_showcase is not None:
            guild_config["delete_after_showcase"] = delete_after_showcase
            status = "✅ Enabled" if delete_after_showcase else "❌ Disabled"
            updated_settings.append(f"🗑️ Delete after showcase is now {status}.")

        if not updated_settings:
            await ctx.respond("ℹ️ You didn't specify any settings to change. Use the options to modify settings.", ephemeral=True, delete_after=30)
            return

        bot.save_config()

        await ctx.respond("✅ Settings updated!\n" + "\n".join(updated_settings), ephemeral=True, delete_after=30)

    discord_token = os.environ.get("DISCORD_TOKEN")
    if not discord_token:
        print("❌ Error: DISCORD_TOKEN not found in environment variables.")
        exit(1)

    if not bot.cobalt_url:
        print("❌ Error: COBALT_API_URL not found in environment variables.")
        exit(1)

    print("Starting BoomerBox Bot...")
    bot.run(discord_token)
