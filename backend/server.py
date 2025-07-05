from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
import os
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
import json

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client['music_app']
users_collection = db['users']
playlists_collection = db['playlists']
tracks_collection = db['tracks']

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Sample music tracks data
SAMPLE_TRACKS = [
    {
        "id": "1",
        "title": "Chill Vibes",
        "artist": "Lofi Master",
        "album": "Relaxation Vol. 1",
        "duration": 180,
        "genre": "Lofi Hip Hop",
        "image": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300&h=300&fit=crop",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    },
    {
        "id": "2",
        "title": "Summer Breeze",
        "artist": "Acoustic Dreams",
        "album": "Seasonal Moods",
        "duration": 210,
        "genre": "Indie Folk",
        "image": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=300&h=300&fit=crop",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    },
    {
        "id": "3",
        "title": "Neon Nights",
        "artist": "Synthwave Collective",
        "album": "Retro Future",
        "duration": 240,
        "genre": "Synthwave",
        "image": "https://images.unsplash.com/photo-1571330735066-03aaa9429d89?w=300&h=300&fit=crop",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    },
    {
        "id": "4",
        "title": "Coffee Shop Jazz",
        "artist": "Urban Quartet",
        "album": "City Sounds",
        "duration": 195,
        "genre": "Jazz",
        "image": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&h=300&fit=crop",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    },
    {
        "id": "5",
        "title": "Electronic Dreams",
        "artist": "Digital Waves",
        "album": "Cyber Meditation",
        "duration": 220,
        "genre": "Electronic",
        "image": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=300&h=300&fit=crop",
        "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    }
]

# Initialize sample tracks in database
def init_sample_tracks():
    if tracks_collection.count_documents({}) == 0:
        for track in SAMPLE_TRACKS:
            tracks_collection.insert_one(track)

# Pydantic models
class User(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Track(BaseModel):
    title: str
    artist: str
    album: str
    duration: int
    genre: str
    image: Optional[str] = None
    audio_url: Optional[str] = None

class Playlist(BaseModel):
    name: str
    description: Optional[str] = ""
    track_ids: List[str] = []

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    track_ids: Optional[List[str]] = None

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Authentication endpoints
@app.post("/api/auth/register")
async def register(user: User):
    # Check if user already exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = hash_password(user.password)
    user_data = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(user_data)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    user = users_collection.find_one({"username": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "email": user["email"]}

# Music endpoints
@app.get("/api/tracks")
async def get_all_tracks():
    tracks = list(tracks_collection.find({}, {"_id": 0}))
    return tracks

@app.get("/api/tracks/{track_id}")
async def get_track(track_id: str):
    track = tracks_collection.find_one({"id": track_id}, {"_id": 0})
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@app.get("/api/tracks/search/{query}")
async def search_tracks(query: str):
    tracks = list(tracks_collection.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"artist": {"$regex": query, "$options": "i"}},
            {"album": {"$regex": query, "$options": "i"}},
            {"genre": {"$regex": query, "$options": "i"}}
        ]
    }, {"_id": 0}))
    return tracks

# Playlist endpoints
@app.get("/api/playlists")
async def get_user_playlists(current_user: str = Depends(get_current_user)):
    playlists = list(playlists_collection.find({"username": current_user}, {"_id": 0}))
    return playlists

@app.post("/api/playlists")
async def create_playlist(playlist: Playlist, current_user: str = Depends(get_current_user)):
    playlist_data = {
        "id": str(uuid.uuid4()),
        "name": playlist.name,
        "description": playlist.description,
        "track_ids": playlist.track_ids,
        "username": current_user,
        "created_at": datetime.utcnow()
    }
    playlists_collection.insert_one(playlist_data)
    return {"message": "Playlist created successfully", "playlist_id": playlist_data["id"]}

@app.get("/api/playlists/{playlist_id}")
async def get_playlist(playlist_id: str, current_user: str = Depends(get_current_user)):
    playlist = playlists_collection.find_one({"id": playlist_id, "username": current_user}, {"_id": 0})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get track details
    tracks = []
    for track_id in playlist["track_ids"]:
        track = tracks_collection.find_one({"id": track_id}, {"_id": 0})
        if track:
            tracks.append(track)
    
    playlist["tracks"] = tracks
    return playlist

@app.put("/api/playlists/{playlist_id}")
async def update_playlist(playlist_id: str, playlist: PlaylistUpdate, current_user: str = Depends(get_current_user)):
    existing_playlist = playlists_collection.find_one({"id": playlist_id, "username": current_user})
    if not existing_playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    update_data = {}
    if playlist.name is not None:
        update_data["name"] = playlist.name
    if playlist.description is not None:
        update_data["description"] = playlist.description
    if playlist.track_ids is not None:
        update_data["track_ids"] = playlist.track_ids
    
    if update_data:
        playlists_collection.update_one({"id": playlist_id}, {"$set": update_data})
    
    return {"message": "Playlist updated successfully"}

@app.delete("/api/playlists/{playlist_id}")
async def delete_playlist(playlist_id: str, current_user: str = Depends(get_current_user)):
    result = playlists_collection.delete_one({"id": playlist_id, "username": current_user})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"message": "Playlist deleted successfully"}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_sample_tracks()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)