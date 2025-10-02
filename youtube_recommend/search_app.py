import sys
import pathlib
from flask import Flask, Blueprint, render_template, jsonify, request
import os

sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))

from search_db import fetch_videos_by_prompt, fetch_random_videos, get_most_recent_prompts, insert_video_data
import youtube_search

# -----------------------------
# Track recent searches in memory
# -----------------------------
RECENT_SEARCHES = []

# -----------------------------
# Utility to get absolute path
# -----------------------------
def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

# -----------------------------
# Setup Flask app and routes
# -----------------------------
def setup_routes(app, namespace="/videos", templates_folder=None):
    templates_folder = templates_folder or os.path.join(os.path.dirname(__file__), "templates")
    bp = Blueprint("youtube_search", __name__, url_prefix=namespace, template_folder=templates_folder)

    @bp.route("/")
    def search_home():
        """Home page: display random videos."""
        videos = fetch_random_videos(limit=12)
        
        for v in videos:
            if v.published_at: v.published_at = v.published_at.isoformat()
            else: v.published_at = ""
            if not v.description: v.description = ""
        return render_template("index.html", videos=videos)

    @bp.route("/search", methods=["GET"])
    def search():
        """Search videos by query and track recent searches."""
        query = request.args.get("q")
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400

        videos = fetch_videos_by_prompt(query)
        results = []
        for v in videos:
            results.append({
                "title": v.title,
                "video_url": v.video_url,
                "thumbnail_url": v.thumbnail_url,
                "description": v.description or "",
                "view_count": v.view_count,
                "like_count": v.like_count,
                "comment_count": v.comment_count,
                "channel_title": v.channel_title,
                "published_at": v.published_at.isoformat() if v.published_at else "",
                "duration_seconds": v.duration_seconds
            })

        if len(results) == 0:
            # perform proper fetch
            print("Fetching videos off youtube")
            youtube_search.fetch_new_raw_data(query)
            data = youtube_search.fetch_new_filtered_data()
            for video in data:
                insert_video_data(video)

            if data:
                results = data
        else:
            print("Reusing old query")

        return jsonify(results)

    @bp.route("/recent_searches", methods=["GET"])
    def recent_searches():
        # Returns list
        return jsonify(get_most_recent_prompts())

    app.register_blueprint(bp)

# -----------------------------
# Run Flask app
# -----------------------------
if __name__ == "__main__":
    app = Flask(__name__)
    setup_routes(app)
    app.run(debug=True)
