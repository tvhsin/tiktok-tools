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

## Caption tool: options in plain English

The words after the script say what to do:

- `embed` puts the caption on each picture.
- `send` sends pictures to Telegram.
- `delete` removes messages the script sent.

You can combine actions: `embed send` captions the pictures, then sends them.
With no extra options, `send` sends the already-captioned pictures.

### Pick pictures or change how they are sent

- `--start 5 --end 14` handles only pictures 5 through 14. By default it
  handles 5 through 124.
- `--test` with `embed` captions only the first picture in the chosen range.
  It will not send anything, even if you also wrote `send`.
- `--raw` sends the original pictures with captions in Telegram, instead of
  sending pictures with text drawn on them.
- `--both` sends the pictures with text drawn on them and also puts the
  caption in Telegram.
- `--album` groups up to 10 pictures into each Telegram album.
- `--as-file` sends them as files instead of Telegram photos.

Examples:

```powershell
python .\caption_and_send.py embed --test
python .\caption_and_send.py send --raw --start 5 --end 14
python .\caption_and_send.py send --album
python .\caption_and_send.py send --both --as-file
```

### Delete sent Telegram messages

Normally, `delete` removes only message IDs saved in
`captioned\sent_ids.json`:

```powershell
python .\caption_and_send.py delete
```

If the messages are not in that log, `delete --probe` tries the latest 150
message IDs. Change that number with `--count`, for example
`delete --probe --count 300`.

`delete --all` tries every message ID in the chat and asks you to type `yes`.
It may delete other bot messages too; use it only if you really want that.

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
