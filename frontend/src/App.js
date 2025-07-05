import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  // Authentication state
  const [user, setUser] = useState(null);
  const [isLogin, setIsLogin] = useState(true);
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '' });
  
  // Music player state
  const [tracks, setTracks] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  // Playlist state
  const [playlists, setPlaylists] = useState([]);
  const [currentPlaylist, setCurrentPlaylist] = useState(null);
  const [showCreatePlaylist, setShowCreatePlaylist] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  
  // UI state
  const [activeTab, setActiveTab] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  
  // Refs
  const audioRef = useRef(null);
  
  // API base URL
  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Auth token management
  const getAuthToken = () => localStorage.getItem('authToken');
  const setAuthToken = (token) => localStorage.setItem('authToken', token);
  const clearAuthToken = () => localStorage.removeItem('authToken');
  
  // API helper
  const apiCall = async (endpoint, options = {}) => {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers
    };
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  };
  
  // Authentication functions
  const handleAuth = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const data = isLogin 
        ? { username: authForm.username, password: authForm.password }
        : authForm;
      
      const response = await apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
      });
      
      setAuthToken(response.access_token);
      setUser({ username: response.username });
      setAuthForm({ username: '', email: '', password: '' });
      
      // Load user data
      await loadTracks();
      await loadPlaylists();
      
    } catch (error) {
      alert(isLogin ? 'Login failed' : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setCurrentTrack(null);
    setIsPlaying(false);
    setPlaylists([]);
    setCurrentPlaylist(null);
    setActiveTab('home');
  };
  
  // Data loading functions
  const loadTracks = async () => {
    try {
      const data = await apiCall('/api/tracks');
      setTracks(data);
    } catch (error) {
      console.error('Failed to load tracks:', error);
    }
  };
  
  const loadPlaylists = async () => {
    try {
      const data = await apiCall('/api/playlists');
      setPlaylists(data);
    } catch (error) {
      console.error('Failed to load playlists:', error);
    }
  };
  
  // Music player functions
  const playTrack = (track) => {
    if (currentTrack?.id === track.id) {
      setIsPlaying(!isPlaying);
    } else {
      setCurrentTrack(track);
      setIsPlaying(true);
    }
  };
  
  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };
  
  const skipTrack = (direction) => {
    const currentIndex = tracks.findIndex(t => t.id === currentTrack?.id);
    let nextIndex;
    
    if (direction === 'next') {
      nextIndex = (currentIndex + 1) % tracks.length;
    } else {
      nextIndex = currentIndex > 0 ? currentIndex - 1 : tracks.length - 1;
    }
    
    setCurrentTrack(tracks[nextIndex]);
    setIsPlaying(true);
  };
  
  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };
  
  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };
  
  const handleSeek = (e) => {
    const seekTime = (e.target.value / 100) * duration;
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };
  
  const handleVolumeChange = (e) => {
    const newVolume = e.target.value / 100;
    setVolume(newVolume);
    audioRef.current.volume = newVolume;
  };
  
  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };
  
  // Playlist functions
  const createPlaylist = async () => {
    if (!newPlaylistName.trim()) return;
    
    try {
      await apiCall('/api/playlists', {
        method: 'POST',
        body: JSON.stringify({
          name: newPlaylistName,
          description: '',
          track_ids: []
        })
      });
      
      setNewPlaylistName('');
      setShowCreatePlaylist(false);
      // Force reload playlists to show the new one
      await loadPlaylists();
    } catch (error) {
      alert('Failed to create playlist');
    }
  };
  
  const addToPlaylist = async (playlistId, trackId) => {
    try {
      const playlist = playlists.find(p => p.id === playlistId);
      const updatedTrackIds = [...playlist.track_ids, trackId];
      
      await apiCall(`/api/playlists/${playlistId}`, {
        method: 'PUT',
        body: JSON.stringify({
          track_ids: updatedTrackIds
        })
      });
      
      await loadPlaylists();
    } catch (error) {
      alert('Failed to add track to playlist');
    }
  };
  
  // Search function
  const handleSearch = async (query) => {
    setSearchQuery(query);
    
    if (query.trim()) {
      try {
        const results = await apiCall(`/api/tracks/search/${encodeURIComponent(query)}`);
        setSearchResults(results);
      } catch (error) {
        console.error('Search failed:', error);
      }
    } else {
      setSearchResults([]);
    }
  };
  
  // Effects
  useEffect(() => {
    // Check for existing auth token
    const token = getAuthToken();
    if (token) {
      // Verify token and load user data
      apiCall('/api/auth/me')
        .then(userData => {
          setUser(userData);
          loadTracks();
          loadPlaylists();
        })
        .catch(() => {
          clearAuthToken();
        });
    }
  }, []);
  
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play();
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, currentTrack]);
  
  // Render components
  const renderAuth = () => (
    <div className="auth-container">
      <div className="auth-form">
        <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
        <form onSubmit={handleAuth}>
          <input
            type="text"
            placeholder="Username"
            value={authForm.username}
            onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
            required
          />
          {!isLogin && (
            <input
              type="email"
              placeholder="Email"
              value={authForm.email}
              onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
              required
            />
          )}
          <input
            type="password"
            placeholder="Password"
            value={authForm.password}
            onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Loading...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>
        <p onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? 'Need an account? Sign up' : 'Already have an account? Login'}
        </p>
      </div>
    </div>
  );
  
  const renderTrackList = (trackList) => (
    <div className="track-list">
      {trackList.map(track => (
        <div key={track.id} className="track-item">
          <div className="track-info">
            <img src={track.image} alt={track.title} className="track-image" />
            <div className="track-details">
              <h4>{track.title}</h4>
              <p>{track.artist}</p>
            </div>
          </div>
          <div className="track-actions">
            <button onClick={() => playTrack(track)}>
              {currentTrack?.id === track.id && isPlaying ? '⏸️' : '▶️'}
            </button>
            <select onChange={(e) => addToPlaylist(e.target.value, track.id)}>
              <option value="">Add to playlist</option>
              {playlists.map(playlist => (
                <option key={playlist.id} value={playlist.id}>{playlist.name}</option>
              ))}
            </select>
          </div>
        </div>
      ))}
    </div>
  );
  
  const renderPlayer = () => (
    <div className="player-container">
      {currentTrack && (
        <>
          <audio
            ref={audioRef}
            src={currentTrack.audio_url}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={() => skipTrack('next')}
          />
          <div className="player-info">
            <img src={currentTrack.image} alt={currentTrack.title} />
            <div>
              <h4>{currentTrack.title}</h4>
              <p>{currentTrack.artist}</p>
            </div>
          </div>
          <div className="player-controls">
            <button onClick={() => skipTrack('prev')}>⏮️</button>
            <button onClick={togglePlay} className="play-button">
              {isPlaying ? '⏸️' : '▶️'}
            </button>
            <button onClick={() => skipTrack('next')}>⏭️</button>
          </div>
          <div className="player-progress">
            <span>{formatTime(currentTime)}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={duration ? (currentTime / duration) * 100 : 0}
              onChange={handleSeek}
              className="progress-bar"
            />
            <span>{formatTime(duration)}</span>
          </div>
          <div className="player-volume">
            <span>🔊</span>
            <input
              type="range"
              min="0"
              max="100"
              value={volume * 100}
              onChange={handleVolumeChange}
              className="volume-bar"
            />
          </div>
        </>
      )}
    </div>
  );
  
  if (!user) {
    return renderAuth();
  }
  
  return (
    <div className="app">
      <header className="app-header">
        <h1>🎵 Music Player</h1>
        <div className="header-actions">
          <input
            type="text"
            placeholder="Search music..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input"
          />
          <span>Welcome, {user.username}!</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>
      
      <div className="app-content">
        <nav className="sidebar">
          <button 
            onClick={() => setActiveTab('home')}
            className={activeTab === 'home' ? 'active' : ''}
          >
            🏠 Home
          </button>
          <button 
            onClick={() => setActiveTab('playlists')}
            className={activeTab === 'playlists' ? 'active' : ''}
          >
            📚 Playlists
          </button>
          <button 
            onClick={() => setActiveTab('search')}
            className={activeTab === 'search' ? 'active' : ''}
          >
            🔍 Search
          </button>
        </nav>
        
        <main className="main-content">
          {activeTab === 'home' && (
            <div>
              <h2>All Tracks</h2>
              {renderTrackList(tracks)}
            </div>
          )}
          
          {activeTab === 'playlists' && (
            <div>
              <div className="playlist-header">
                <h2>Your Playlists</h2>
                <button onClick={() => setShowCreatePlaylist(true)}>
                  + Create Playlist
                </button>
              </div>
              
              {showCreatePlaylist && (
                <div className="create-playlist">
                  <input
                    type="text"
                    placeholder="Playlist name"
                    value={newPlaylistName}
                    onChange={(e) => setNewPlaylistName(e.target.value)}
                  />
                  <button onClick={createPlaylist}>Create</button>
                  <button onClick={() => setShowCreatePlaylist(false)}>Cancel</button>
                </div>
              )}
              
              {playlists.map(playlist => (
                <div key={playlist.id} className="playlist-item">
                  <h3>{playlist.name}</h3>
                  <p>{playlist.track_ids.length} tracks</p>
                </div>
              ))}
            </div>
          )}
          
          {activeTab === 'search' && (
            <div>
              <h2>Search Results</h2>
              {searchResults.length > 0 ? (
                renderTrackList(searchResults)
              ) : (
                <p>No results found</p>
              )}
            </div>
          )}
        </main>
      </div>
      
      {renderPlayer()}
    </div>
  );
};

export default App;