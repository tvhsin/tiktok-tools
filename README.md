`download_parts.py` is a file where u set which posts u want downloaded. put username in `USERNAME` and the post IDs in `POST_IDS` list. the post id is in the video link when u open a video on browser. the script has a username set u should edit.
`caption_and_send.py` is a file that i made to put captions that i provided directly onto the image. and optionally send me those on telegram using a bot. you can make a telegram bot by texting the bot @BotFather and then edit caption_and_send.py file with the bot token and the channel id of your telegram chat/group. google how to get the id.

all of this is vibecoded and copilot wrote the readme below, because i cannot be bothered. im js cleaning up my pc and archiving my script folder.

# TikTok photo downloader, captioner, and telegram sender

## Setup

```powershell
Set-Location 'E:\Scripts\tiktok post downloader'
python -m pip install -U "yt-dlp[default,curl-cffi]" pillow requests img2pdf
```

`download_parts.py` needs a valid TikTok `cookies.txt` in this folder. Get it using "Get cookies.txt LOCALLY" extension. The Telegram bot token is inside
`caption_and_send.py`;

## Download photo posts

Run the four post IDs configured near the top of `download_parts.py`:

```powershell
python .\download_parts.py
```

The script creates `readmewhenyouneedme\` again and saves the images under
`part 1\` through `part 4\`. Existing numbered images in those folders are
skipped if you rerun it.

Download one photo post instead:

```powershell
python .\download_parts.py --url 'https://www.tiktok.com/@account/video/POST_ID'
```

That creates a subfolder named after the post ID. Add `--folder bonus` to
choose a different name. This downloader handles photo slideshows, not
ordinary video posts.

## Caption and Telegram tools

`caption_and_send.py` is a separate workflow. It expects these inputs directly
inside `readmewhenyouneedme\`:

- Original images named `5.jpg` through `124.jpg`.
- A `captions.txt` with exactly 120 captions, separated by lines containing
  `---` or one caption per non-empty line.

The four-post downloader does **not** create that numbered image set or
`captions.txt`. The personal copies were deleted, so prepare/copy those inputs
yourself before running the caption tool. Then:

```powershell
python .\caption_and_send.py embed
python .\caption_and_send.py send
```

`embed` writes captioned images to `readmewhenyouneedme\captioned\`.
`send` sends those existing captioned images to the configured Telegram
chat. To send the original images with Telegram captions instead:

```powershell
python .\caption_and_send.py send --raw
```

Other options: `--test` embeds only the first image; `--start N --end N`
limits the image range; `--album` sends groups of up to 10; `--as-file`
sends documents instead of compressed Telegram photos. `embed send` does
both steps in one run. `--both` adds Telegram captions as well as embedded
text.

Successful Telegram sends are logged in
`readmewhenyouneedme\captioned\sent_ids.json`. Delete only those logged
messages with:

```powershell
python .\caption_and_send.py delete
```

`delete --probe` sweeps recent message IDs not in the log. `delete --all`
attempts to sweep all message IDs in the chat; either can delete unrelated
bot messages, so use them only if that is intended.

## Make PDFs

`makepdf.py` was moved here so it would survive the sample-folder cleanup.
It reads numbered images `1.jpg` through `124.jpg` from
`readmewhenyouneedme\` and writes PDFs to `readmewhenyouneedme\pdfs\`:

```powershell
python .\makepdf.py
```

It makes one cover/contents PDF from images 1-4 and twelve volumes from
images 5-124. It does not download or create the numbered images. The
`readmewhenyouneedme\` folder and required image inputs must exist first.

## Moving the project

`download_parts.py` saves relative to its own folder. `makepdf.py` also finds
its input folder relative to itself. `caption_and_send.py` still has
`E:\Scripts\tiktok post downloader\readmewhenyouneedme` configured directly
in the script; change `IMG_DIR` there if you move the project.
