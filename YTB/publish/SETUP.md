# YouTube publisher: one-time setup (about 10 minutes, free)

You do this once, on your PC. After that, publishing a reel is one command.

## 1. Create a Google Cloud project
1. Go to https://console.cloud.google.com/ and sign in with the Google account that owns **PaperLit**.
2. Top bar: project picker > **New project** > name it `PaperLit Publisher` > **Create**. Make sure it's selected.

## 2. Turn on the YouTube API
1. Left menu: **APIs & Services > Library**.
2. Search **YouTube Data API v3** > open it > **Enable**.

## 3. Consent screen
1. **APIs & Services > OAuth consent screen** (may be called **Google Auth Platform**) > **Get started**.
2. App name `PaperLit Publisher`, support email: yours. Audience: **External**. Contact email: yours. Agree > **Create**.
3. **Audience** tab > **Test users** > **Add users** > add your own Gmail (the one that owns PaperLit) > Save.
   (The app stays in "Testing": only you can use it, no Google review needed.)

## 4. Create the key file
1. **APIs & Services > Credentials** (or **Clients**) > **Create credentials > OAuth client ID**.
2. Application type: **Desktop app**, name `PaperLit PC` > **Create**.
3. Click **Download JSON**. Rename the file to `client_secret.json` and put it in this folder (`YTB\publish\`).
   Never share this file or paste it in chat. It's already excluded from git.

## 5. Install (once)
```
python -m pip install google-api-python-client google-auth-oauthlib tzdata
```

## 6. First run
```
cd YTB\publish
python youtube_publish.py list
```
Your browser opens. Pick the **PaperLit** channel (not Better Off Human). You'll see "Google hasn't verified this app":
click **Continue** (it's your own app). Allow both permissions. The terminal then lists your videos.
A `token.json` file is saved so you won't sign in again. Keep it private too.

## Daily use
```
python youtube_publish.py reel ..\lanternfold\reels\07_your_reel
```
Uploads the reel, sets title, description, tags, cover, "not made for kids", and schedules it for the next 04:00 Morocco time.
Then it posts the pinned-comment text: open the video in the YouTube app, tap the comment's ⋮ > **Pin**.

Other commands: `--when "2026-11-11 04:00"`, `--now`, `edit VIDEO_ID --title "..." --thumb cover.jpg`, `list`.

**Limits:** free quota is 10,000 units a day; one upload costs about 1,700, so up to 5 uploads a day.
If Google ever says the sign-in expired (test apps re-ask about every 7 days), just run the command again and sign in.
