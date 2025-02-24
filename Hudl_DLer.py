import requests
import os
from concurrent.futures import ThreadPoolExecutor
# from threading import Lock  
import subprocess
import time
import random
from datetime import datetime


class TSDownloader:
  def __init__(self, base_url, game_id2, resolution, start_index=0, end_index=800,
         min_delay=1.0, max_delay=3.0, max_retries=3):
    """
    Initialize the downloader with base URL and parameters
    
    Args:
      base_url (str): Base URL without resolution and TS number
      resolution (str): Resolution path (e.g., '270', '540')
      start_index (int): Starting TS index
      end_index (int): Ending TS index to try
      min_delay (float): Minimum delay between requests in seconds
      max_delay (float): Maximum delay between requests in seconds
      max_retries (int): Maximum number of retry attempts per file
    """
    self.base_url = base_url
    self.game_id2 = game_id2
    self.resolution = resolution
    self.start_index = start_index
    self.end_index = end_index
    self.downloaded_files = []
    self.min_delay = min_delay
    self.max_delay = max_delay
    self.max_retries = max_retries
    self.last_request_time = 0
    # self.lock = Lock()
    self.res_map_start = { # This specifies the paths resolution part
      270: "270p.hls",
      540: "540p-lo.hls",
      720: "720p-2.5.hls",
      1080: "1080p30-6.0.hls",
    }
    self.res_map_end = { # This specifies the paths bitrate part
      270: "b360800",
      540: "b1680800",
      720: "b2890800",
      1080: "b6740800",
    }

    
  def get_url(self, index):
    """Generate URL for specific TS file"""
    return f"{self.base_url}/{self.res_map_start[self.resolution]}/media-{self.game_id2}_{self.res_map_end[self.resolution]}_d10000_{index}.ts"
  
  def wait_between_requests(self):
    # with self.lock:
    #   current_time = time.time()
    #   elapsed = current_time - self.last_request_time
    #   if elapsed < self.min_delay:
    #       delay = max(self.min_delay - elapsed, 0) + random.uniform(0, self.max_delay - self.min_delay)
    #       time.sleep(delay)
    #   self.last_request_time = time.time()
    current_time = time.time()
    elapsed = current_time - self.last_request_time
    
    if elapsed < self.min_delay:
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    self.last_request_time = time.time()

  def download_file(self, index):
    """Download a single TS file with retries and rate limiting"""
    for attempt in range(self.max_retries):
      try:
        self.wait_between_requests()
        
        url = self.get_url(index)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
          filename = f"segment_{index:04d}.ts"
          with open(filename, 'wb') as f:
            f.write(response.content)
          print(f"{datetime.now().strftime('%H:%M:%S')} - Downloaded {filename}")
          return filename
        elif response.status_code == 429: # Too Many Requests
          print(f"{index} - Rate limit hit, waiting longer before retry {attempt + 1}")
          time.sleep(random.uniform(5, 10)) # Longer wait on rate limit
        elif response.status_code == 403: # The file either doesn't exist or is restriced (Forbidden)
          print(f"{index} - Forbidden from resource. Does it exist? Waiting longer before retry {attempt + 1}")
          time.sleep(random.uniform(5, 10)) # Longer wait on rate limit
        else:
          print(f"Failed to download index {index}: Status {response.status_code}")
          
      except requests.exceptions.RequestException as e:
        print(f"Error downloading index {index}: {e}")
        time.sleep(random.uniform(2, 5)) # Wait before retry
        
    return None # Return None if all retries failed

  def download_all(self):
    """Download all TS files using thread pool with limited concurrency"""
    os.makedirs("downloads", exist_ok=True)
    os.chdir("downloads")
    
    # Reduced number of workers to avoid overwhelming the server
    with ThreadPoolExecutor(max_workers=3) as executor:
      futures = []
      for i in range(self.start_index, self.end_index+1):
        futures.append(executor.submit(self.download_file, i))
      
      for future in futures:
        result = future.result()
        if result:
          self.downloaded_files.append(result)
    
    self.downloaded_files.sort() # Ensure files are in order
    
  def concatenate_files(self, output_filename):
    """Concatenate all downloaded TS files into a single MP4"""
    if not self.downloaded_files:
      print("No files to concatenate")
      return
      
    # Create a file list for ffmpeg
    with open('file_list.txt', 'w') as f:
      for filename in self.downloaded_files:
        f.write(f"file '{filename}'\n")
    
    # Use ffmpeg to concatenate files
    cmd = [
      'ffmpeg',
      '-f', 'concat',
      '-safe', '0',
      '-i', 'file_list.txt',
      '-map', '0:v',  # Include video stream
      '-map', '0:a',  # Include audio stream
      '-c', 'copy',
      output_filename
    ]
    
    try:
      subprocess.run(cmd, check=True)
      print(f"Successfully created {output_filename}")
    except subprocess.CalledProcessError as e:
      print(f"Error during concatenation: {e}")
    
    # Clean up individual TS files
    os.remove('file_list.txt')
    for file in self.downloaded_files:
      os.remove(file)

# Example usage
def download_game(game_id1, game_id2, resolution, file_name, start_index, end_index):
  # https://di2g5yar1p6ph.cloudfront.net/sn-zpcczwe0/1080p60-6.0.hls/media-b933ecda_b6740800_d10000_9.ts
  base_url = f"https://di2g5yar1p6ph.cloudfront.net/{game_id1}"
  # Create downloader with conservative rate limiting
  downloader = TSDownloader(
    base_url,
    game_id2,
    resolution,
    min_delay=1.5,  # Minimum 2 seconds between requests
    max_delay=3.0,  # Maximum 4 seconds between requests
    max_retries=3,   # Retry failed downloads up to 3 
    start_index=start_index,
    end_index=end_index
  )
  downloader.download_all()
  downloader.concatenate_files(f"{file_name}_{resolution}.mp4")

if __name__ == "__main__":
  # Example: Download a specific game at 270p resolution


  ### CHANGE THESE FOR EVERY GAME
  download_resolution = 270
  game_code1 = "sn-zpcczwe0"
  game_code2 = "b933ecda"
  download_name = "Wildcats" # Purely the name of your resulting download. Mine would be Menlo_720.mp4
  start_index = 0 # In my testing it usually doesn't start at 0. Don't be scared at the error on 0.
  end_index = 15 # specific to each recording too. go to end and see what the index at the end is.
  ### CHANGES OVER


  if (download_resolution not in {270, 540, 720, 1080}):
    print("Invalid resolution, must be 270, 540, 720, or 1080")
    exit()


  download_game(game_code1, game_code2, download_resolution, download_name, start_index, end_index)