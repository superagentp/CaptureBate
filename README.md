CaptureBate
==========

CaptureBate lets you follow and archive your favorite models shows on chaturbate.com

Requirements
==========
(Debian 7, minimum)

[RTMPDump(ksv)](https://github.com/BurntSushi/rtmpdump-ksv) used to capture the streams.

[BeautifulSoup4](https://pypi.python.org/pypi/beautifulsoup4/4.3.2) the screen-scraping library.

[ffmpeg](https://www.ffmpeg.org/download.html) compiled with support for `libmp3lame` & `libspeex` audio for converting the output files.

Setup
===========

Install requirements `sudo pip install -r requirements.txt`

Get a [chaturbate account](https://chaturbate.com/accounts/register/), once you're signed up put your credentials in the `config.conf` file and - if needed - adjust the other options.

NOTE: if you find captures aren't starting set an absolute directory for captures in `config.conf` like so `Video_folder = /home/user/CaptureBate/Captured`

Be mindful when capturing many streams at once to have plenty of space on disk and the bandwidth available or you'll endup dropping a lot of frames and the files will be useless.

Before you can start capturing streams you first need to [follow](https://i.imgur.com/o9QyAVC.png) the models you want on site and then paste their usernames into the `wishlist.txt` file, once you have done this you're ready to start `main.py`

Running & Output
===========

To start capturing streams you need to run `python main.py` I reccomend you do this in [screen](https://www.gnu.org/software/screen/) as there is no output and it can just be left running in the background. To see what's going on run `tail -f output.log`

Standard output should look something this when recording streams ..

    17/11/2014 09:37:13 PM INFO:Connecting to https://chaturbate.com/auth/login/
    17/11/2014 09:37:13 PM INFO:Starting new HTTPS connection (1): chaturbate.com
    17/11/2014 09:37:15 PM INFO:0 Models in the list before checking: []
    17/11/2014 09:37:15 PM INFO:Redirecting to https://chaturbate.com/followed-cams/
    17/11/2014 09:37:16 PM INFO:[Models_list] 2 models are online: [u'hottminx', u'adryeenmely']
    17/11/2014 09:37:16 PM INFO:[Compare_lists] Checking model list:
    17/11/2014 09:37:16 PM INFO:[Compare_lists] hottminx is still being recorded
    17/11/2014 09:37:16 PM INFO:[Compare_lists] adryeenmely is still being recorded
    17/11/2014 09:37:16 PM INFO:[Loop]List of new models for adding: []
    17/11/2014 09:37:16 PM INFO:[Select_models] Which models are approved?
    17/11/2014 09:37:16 PM WARNING:[Select_models]  No models for approving
    17/11/2014 09:37:16 PM INFO:[Loop]Model list after check looks like: 0 models:
     []
     and models currently being recorded are:
     ['adryeenmely', 'hottminx']
    17/11/2014 09:37:16 PM INFO:[Sleep] Waiting for next check (45 seconds)

Encoding
===========

Once you've captured some streams you're going to need to convert the audio to have them play nice in vlc, etc. This is where ffmpeg comes in, there is no need to convert the video so this doesn't take too long. To convert individual files do `ffmpeg -i input.flv -vcodec copy -acodec libmp3lame output.mp4` this will convert the speex audio to mp3 and change the container to mp4 (stream is h264)

If you want to batch convert your captured streams run `find ./ -name '*.flv' -execdir mkdir converted_bates \;; for file in *.flv; do ffmpeg -i "$file" -vcodec copy -acodec libmp3lame "converted_bates/${file%.flv}.mp4"; done` from your `CaptureBate/Captured/` directory.

If you don't want to do any conversion you can install the [speex audio codec](http://speex.org/downloads/) which is a huge pain in the ass to get working correctly under linux/vlc.
