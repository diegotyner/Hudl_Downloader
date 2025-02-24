# Hudl_Downloader


Definitely not an easy to use tool, this is mostly for personal use. 
It is good for downloading files hosted on team1sport / HudlTV, such as games from Willamette University or UCSC. 

To use, make sure that you have the following dependencies:
- Requests: pip install requests
- ffmpeg on your terminal (this script uses it to stitch together the stream files)

*Mild Warning:* The downloaded files will be LARGE. If you're downloading a 1:30hr game at 1080p, expect around a 7Gb, and make sure you have double that free at least to process the temporary transport stream files. 

---

#### Usage:

```
  download_resolution = 270 
  game_code1 = "sn-xsk0y3sq"
  game_code2 = "f4293a83"
  download_name = "Menlo" # Purely the name of your resulting download. Mine would be Menlo_720.mp4
  end_index = 639 # specific to each recording too. go to end and see what the index at the end is.
```

To find the codes to make the script work:
1) Go to the page with the game you're interested in
2) Press `Ctrl+Shift+I` to open Devtools, then switch to the Network tab in your browser
3) Go to the filter tab around the top left of the Network tab that just opened, and enter `media`. This will only show network requests with this title. 
4) Click one of them, and you should see a panel of information open up. Find the request URL and copy it. It should resemble this:
  - `https://di2g5yar1p6ph.cloudfront.net/sn-zpcczwe0/1080p60-6.0.hls/media-b933ecda_b6740800_d10000_9.ts`
5) When broken down, the URL is really this:
  - `https://di2g5yar1p6ph.cloudfront.net/{game_id1}/{resolution_string}/media-{game_id2}_{bitrate}_d10000_{index}.ts`

After you have the request URL, fill them out in the script and run it. Enjoy the rather large mp4 of the game! 