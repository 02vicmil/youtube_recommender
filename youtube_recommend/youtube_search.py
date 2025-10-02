import json
from datetime import datetime, timezone
from googleapiclient.discovery import build
import os
import re
import pathlib

def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

# -----------------------------
# Load API key from config.json
# -----------------------------
with open(get_directory_path(__file__) + "/config.json", "r") as f:
    config = json.load(f)

API_KEY = config["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=API_KEY)

def search_youtube(search_query, max_results=50):
    """
    Perform a single YouTube search and fetch raw video details for those results.

    Args:
        search_query (str): The search term.
        max_results (int): Number of search results to fetch (max 50 per API limits).

    Returns:
        dict: Raw search and video API responses.
    """
    # Step 1: Single search request
    search_response = youtube.search().list(
        q=search_query,
        part="id,snippet",
        maxResults=max_results,
        type="video"
    ).execute()

    # Step 2: Extract video IDs
    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    # Step 3: Fetch raw video details for the search results
    video_response = {}
    if video_ids:
        video_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()

    return {
        "search_query": search_query,
        "search_response": search_response,
        "video_response": video_response
    }

# -----------------------------
# Extract important video data
# -----------------------------
import re

def parse_duration(duration):
    """
    Parse an ISO 8601 duration string (e.g. 'PT1H2M5S') into total seconds.

    Args:
        duration (str): ISO 8601 duration string.

    Returns:
        int: Duration in seconds.
    """
    pattern = re.compile(
        r'PT'                       # starts with PT
        r'(?:(\d+)H)?'              # optional hours
        r'(?:(\d+)M)?'              # optional minutes
        r'(?:(\d+)S)?'              # optional seconds
    )
    match = pattern.match(duration)
    if not match:
        return 0

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds

def filter_youtube_data(raw_data, min_views=5000):
    filtered_videos = []

    search_query = raw_data.get("search_query", {})
    video_responses = raw_data.get("video_response", {})
    items = video_responses.get("items", [])

    for video in items:
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})
        content = video.get("contentDetails", {})

        try:
            view_count = int(stats.get("viewCount", 0))
        except ValueError:
            view_count = 0

        if view_count < min_views:
            continue

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high") or 
            thumbnails.get("medium") or 
            thumbnails.get("default") or {}
        ).get("url")

        video_id = video.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # --- Extract duration without external libs ---
        duration_iso = content.get("duration")  # e.g. "PT15M33S"
        duration_seconds = parse_duration(duration_iso) if duration_iso else None

        if duration_seconds < 60 * 5:
            continue

        video_data = {
            "video_id": video_id,
            "video_url": video_url,
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "thumbnail_url": thumbnail_url,
            "view_count": view_count,
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "published_at": snippet.get("publishedAt"),
            "channel_title": snippet.get("channelTitle"),
            "duration_seconds": duration_seconds,
            "duration_raw": duration_iso,
            "search_query": search_query,
        }

        filtered_videos.append(video_data)

    return filtered_videos


def get_latest_json_file(data_dir = get_directory_path(__file__) + "/raw_data"):
    """Find the most recent JSON file in the data/ directory."""
    files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
    if not files:
        return None
    files = [os.path.join(data_dir, f) for f in files]
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def load_latest_data():
    """Load the latest JSON file as Python data."""
    latest_file = get_latest_json_file()
    print(latest_file)
    if not latest_file:
        return []
    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)
    

def fetch_new_raw_data(query):
    raw_results = search_youtube(query)

    # Save raw responses with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = get_directory_path(__file__) + f"/raw_data/search_results_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

def fetch_new_filtered_data():
    raw_results = load_latest_data()
    print(len(raw_results))
    search_results = filter_youtube_data(raw_results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = get_directory_path(__file__) + f"/data/search_results_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(search_results, f, ensure_ascii=False, indent=4)

    return search_results


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    query = "Anomaly Detection in Machine Learning tutorial for beginners"
    # fetch_new_raw_data(query)
    fetch_new_filtered_data()
