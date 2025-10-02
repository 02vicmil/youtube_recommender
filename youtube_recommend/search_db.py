# video_db.py
import os
import pathlib
from datetime import datetime, timezone
import random
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, func, desc
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

# -----------------------------
# Utility to get absolute path
# -----------------------------
def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

# -----------------------------
# Database setup
# -----------------------------
BASE_DIR = get_directory_path(__file__, 0)  # adjust up_directories if needed
DB_FILE = os.path.join(BASE_DIR, "videos.db")
DB_PATH = f"sqlite:///{DB_FILE}"

engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -----------------------------
# Video data model
# -----------------------------
class VideoData(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, index=True, nullable=False)
    video_url = Column(String, nullable=False)
    title = Column(String)
    description = Column(String)
    thumbnail_url = Column(String)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    published_at = Column(DateTime(timezone=True))
    channel_title = Column(String)
    duration_seconds = Column(Integer)
    duration_raw = Column(String)
    search_query = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<VideoData(title='{self.title}', video_id='{self.video_id}', search_query='{self.search_query}')>"

# Create tables if they do not exist
Base.metadata.create_all(engine)

def parse_video_datetime(video_dict):
    """Convert ISO datetime strings to datetime objects with timezone."""
    if "published_at" in video_dict and isinstance(video_dict["published_at"], str):
        iso_str = video_dict["published_at"]
        # Convert 'Z' to '+00:00' for UTC
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        video_dict["published_at"] = datetime.fromisoformat(iso_str)
    return video_dict

# -----------------------------
# Database helper functions
# -----------------------------
def insert_video_data(video_dict):
    """Insert a single video record into the database, skipping duplicates."""
    session = SessionLocal()
    try:
        # Parse datetime fields
        video_dict = parse_video_datetime(video_dict)
        video = VideoData(**video_dict)
        session.add(video)
        session.commit()
        session.refresh(video)
        return video
    except IntegrityError:
        # Video with this video_id already exists
        session.rollback()
        print(f"Skipping duplicate video: {video_dict.get('video_id')}")
        return None
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def fetch_videos_by_prompt(prompt):
    """Fetch all videos for a given search query."""
    session = SessionLocal()
    try:
        return session.query(VideoData).filter(VideoData.search_query == prompt).all()
    finally:
        session.close()

def fetch_random_videos(limit=5):
    """Fetch a random selection of videos."""
    session = SessionLocal()
    try:
        total = session.query(func.count(VideoData.id)).scalar()
        if total == 0:
            return []
        random_offsets = random.sample(range(total), min(limit, total))
        videos = []
        for offset in random_offsets:
            video = session.query(VideoData).offset(offset).first()
            if video:
                videos.append(video)
        return videos
    finally:
        session.close()

def remove_video(video_id):
    """Remove a video by its video_id."""
    session = SessionLocal()
    try:
        video = session.query(VideoData).filter(VideoData.video_id == video_id).first()
        if video:
            session.delete(video)
            session.commit()
            return True
        return False
    finally:
        session.close()

def get_most_recent_prompts(limit=10):
    """Return a list of the most recent search queries."""
    session = SessionLocal()
    try:
        results = (
            session.query(VideoData.search_query)
            .group_by(VideoData.search_query)
            .order_by(desc(func.max(VideoData.created_at)))
            .limit(limit)
            .all()
        )
        return [r[0] for r in results]
    finally:
        session.close()

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    example_video = {
        "video_id": "abc123",
        "video_url": "https://youtube.com/watch?v=abc123",
        "title": "Example Video",
        "description": "Just an example",
        "thumbnail_url": "",
        "view_count": 1000,
        "like_count": 50,
        "comment_count": 10,
        "published_at": datetime.now(timezone.utc),
        "channel_title": "Test Channel",
        "duration_seconds": 600,
        "duration_raw": "PT10M",
        "search_query": "example query"
    }
    insert_video_data(example_video)

    remove_video(example_video["video_id"])

    print("Random videos:")
    for v in fetch_random_videos(2):
        print(v)

    print("\nVideos for 'example query':")
    for v in fetch_videos_by_prompt("example query"):
        print(v)

    print("\nRecent prompts:")
    print(get_most_recent_prompts())
