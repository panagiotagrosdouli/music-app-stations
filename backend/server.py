from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from datetime import datetime
import uuid
from pymongo import MongoClient
import json

app = FastAPI(title="Global Music Hub API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
try:
    client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'), serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    db = client.music_app
    comments_collection = db.comments
    stations_collection = db.stations
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection error: {str(e)}")
    # Create dummy collections that won't actually store data
    # This allows the app to run even if MongoDB is not available
    from pymongo.collection import Collection
    class DummyCollection:
        def __init__(self, name):
            self.name = name
            self._data = []
            
        def insert_one(self, document):
            self._data.append(document)
            return type('obj', (object,), {'inserted_id': document.get('id', 'dummy_id')})
            
        def find(self, query=None, projection=None):
            return self._data
            
        def update_one(self, filter, update, upsert=False):
            return type('obj', (object,), {'modified_count': 0, 'upserted_id': None})
            
        def delete_one(self, query):
            return type('obj', (object,), {'deleted_count': 0})
            
        def sort(self, *args, **kwargs):
            return self
    
    db = type('obj', (object,), {'name': 'dummy_db'})
    comments_collection = DummyCollection('comments')
    stations_collection = DummyCollection('stations')

# Models
class Comment(BaseModel):
    id: str = None
    content: str
    author: str
    target_id: str  # station ID or track ID
    target_type: str  # 'station' or 'track'
    timestamp: datetime = None

class RadioStation(BaseModel):
    stationuuid: str
    name: str
    url: str
    country: str
    language: str
    tags: str
    votes: int
    codec: str
    bitrate: int
    favicon: str

# Radio Browser API base URL
RADIO_API_BASE = "https://de1.api.radio-browser.info/json"

@app.get("/")
async def root():
    return {"message": "Global Music Hub API", "status": "running"}

# Radio Stations Endpoints
@app.get("/api/stations/popular", response_model=List[dict])
async def get_popular_stations(limit: int = 20):
    """Get popular radio stations worldwide"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RADIO_API_BASE}/stations/topvote/{limit}")
            response.raise_for_status()
            stations = response.json()
            
            # Try to store/update stations in database, but continue if it fails
            try:
                for station in stations:
                    stations_collection.update_one(
                        {'stationuuid': station.get('stationuuid')},
                        {'$set': station},
                        upsert=True
                    )
            except Exception as db_error:
                print(f"Warning: Could not update database: {str(db_error)}")
            
            return stations
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching stations: {str(e)}")

@app.get("/api/stations/by-country/{country}", response_model=List[dict])
async def get_stations_by_country(country: str, limit: int = 20):
    """Get radio stations by country"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RADIO_API_BASE}/stations/bycountry/{country}?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching stations: {str(e)}")

@app.get("/api/stations/search")
async def search_stations(q: str = Query(..., description="Search query"), limit: int = 20):
    """Search radio stations by name or tag"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RADIO_API_BASE}/stations/byname/{q}?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error searching stations: {str(e)}")

@app.get("/api/countries")
async def get_countries():
    """Get list of countries with radio stations"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RADIO_API_BASE}/countries")
            response.raise_for_status()
            countries = response.json()
            # Sort by station count
            return sorted(countries, key=lambda x: x.get('stationcount', 0), reverse=True)[:50]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching countries: {str(e)}")

# Comments Endpoints
@app.post("/api/comments")
async def create_comment(comment: Comment):
    """Create a new comment"""
    comment_data = {
        'id': str(uuid.uuid4()),
        'content': comment.content,
        'author': comment.author,
        'target_id': comment.target_id,
        'target_type': comment.target_type,
        'timestamp': datetime.utcnow()
    }
    
    try:
        comments_collection.insert_one(comment_data)
        return comment_data
    except Exception as e:
        print(f"Error creating comment: {str(e)}")
        # Return the comment data anyway, even if we couldn't save it to the database
        return comment_data

@app.get("/api/comments/{target_id}")
async def get_comments(target_id: str, target_type: str = Query(...)):
    """Get comments for a specific station or track"""
    try:
        comments = list(comments_collection.find(
            {'target_id': target_id, 'target_type': target_type},
            {'_id': 0}
        ).sort('timestamp', -1))
        return comments
    except Exception as e:
        print(f"Error fetching comments: {str(e)}")
        # Return an empty list if we couldn't fetch comments from the database
        return []

@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: str):
    """Delete a comment"""
    try:
        result = comments_collection.delete_one({'id': comment_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error deleting comment: {str(e)}")
        # Return success even if we couldn't delete from the database
        return {"message": "Comment deletion attempted"}

# Spotify Integration Endpoints (Ready for credentials)
@app.get("/api/spotify/search")
async def spotify_search(q: str = Query(...), limit: int = 20):
    """Search Spotify tracks (requires Spotify credentials)"""
    # TODO: Implement when Spotify credentials are available
    return {"message": "Spotify integration pending credentials", "query": q}

@app.post("/api/spotify/auth/login")
async def spotify_login():
    """Initiate Spotify OAuth login"""
    # TODO: Implement when Spotify credentials are available
    return {"message": "Spotify auth pending credentials"}

@app.get("/api/spotify/auth/callback")
async def spotify_callback(code: str):
    """Handle Spotify OAuth callback"""
    # TODO: Implement when Spotify credentials are available
    return {"message": "Spotify callback pending credentials", "code": code}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}