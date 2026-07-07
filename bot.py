import discord
from discord.ext import commands, tasks
import json
import os
import yt_dlp
import asyncio
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


if not os.path.exists(config["download_folder"]):
    os.makedirs(config["download_folder"])


def load_videos():
    with open("videos.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_videos(data):
    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    check_videos.start()



def get_latest_video(channel):

    options = {
        "quiet": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            channel,
            download=False
        )

        videos = info.get("entries")

        if videos:
            video = videos[0]

            return {
                "id": video["id"],
                "title": video["title"],
                "url": f"https://youtube.com/watch?v={video['id']}"
            }

    return None



def download_video(url):

    date = datetime.now().strftime("%Y-%m-%d")

    folder = os.path.join(
        config["download_folder"],
        date
    )

    os.makedirs(folder, exist_ok=True)


    options = {
        "outtmpl": f"{folder}/%(title)s.%(ext)s"
    }


    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            url,
            download=True
        )

        return os.path.abspath(
            ydl.prepare_filename(info)
        )



@tasks.loop(minutes=5)
async def check_videos():

    videos_saved = load_videos()


    for channel in config["youtube_channels"]:

        try:

            video = get_latest_video(channel)


            if video and video["id"] not in videos_saved:


                path = download_video(
                    video["url"]
                )


                videos_saved.append(
                    video["id"]
                )

                save_videos(
                    videos_saved
                )


                discord_channel = bot.get_channel(
                    config["discord_channel_id"]
                )


                await discord_channel.send(
                    f"🔔 {config['mention_user']} a publié une nouvelle vidéo !\n\n"
                    f"🎬 Titre : {video['title']}\n"
                    f"🌐 Voir la vidéo : {video['url']}\n"
                    f"💾 Copie sauvegardée : `{path}`"
                )


        except Exception as e:
            print("Erreur :", e)



@bot.command()
async def test(ctx):

    await ctx.send(
        "✅ Le bot fonctionne !"
    )


bot.run(TOKEN)