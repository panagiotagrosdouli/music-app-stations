import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentView, setCurrentView] = useState('discover');
  const [stations, setStations] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [currentStation, setCurrentStation] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [userName, setUserName] = useState('Anonymous');
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    fetchPopularStations();
    fetchCountries();
  }, []);

  const fetchPopularStations = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/stations/popular?limit=30`);
      const data = await response.json();
      setStations(data);
    } catch (error) {
      console.error('Error fetching stations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCountries = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/countries`);
      const data = await response.json();
      setCountries(data);
    } catch (error) {
      console.error('Error fetching countries:', error);
    }
  };

  const fetchStationsByCountry = async (country) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/stations/by-country/${country}?limit=30`);
      const data = await response.json();
      setStations(data);
    } catch (error) {
      console.error('Error fetching stations:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchStations = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/stations/search?q=${encodeURIComponent(searchQuery)}&limit=30`);
      const data = await response.json();
      setStations(data);
    } catch (error) {
      console.error('Error searching stations:', error);
    } finally {
      setLoading(false);
    }
  };

  const playStation = (station) => {
    if (currentStation?.stationuuid === station.stationuuid && isPlaying) {
      // Pause current station
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    if (audioRef.current) {
      audioRef.current.src = station.url;
      audioRef.current.play().then(() => {
        setCurrentStation(station);
        setIsPlaying(true);
        fetchComments(station.stationuuid);
      }).catch(error => {
        console.error('Error playing station:', error);
        alert('Could not play this station. It might be offline.');
      });
    }
  };

  const stopStation = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    setCurrentStation(null);
    setIsPlaying(false);
    setComments([]);
  };

  const fetchComments = async (stationId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/comments/${stationId}?target_type=station`);
      const data = await response.json();
      setComments(data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const addComment = async () => {
    if (!newComment.trim() || !currentStation) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newComment,
          author: userName,
          target_id: currentStation.stationuuid,
          target_type: 'station'
        }),
      });

      if (response.ok) {
        setNewComment('');
        fetchComments(currentStation.stationuuid);
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="app">
      {/* Audio element for radio playback */}
      <audio ref={audioRef} />

      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <img src="https://images.unsplash.com/photo-1707563496465-5963942d562c" alt="Global Music Hub" className="logo-image" />
            <h1>Global Music Hub</h1>
          </div>
          
          <nav className="nav">
            <button 
              className={`nav-btn ${currentView === 'discover' ? 'active' : ''}`}
              onClick={() => setCurrentView('discover')}
            >
              🌍 Discover
            </button>
            <button 
              className={`nav-btn ${currentView === 'countries' ? 'active' : ''}`}
              onClick={() => setCurrentView('countries')}
            >
              🏳️ Countries
            </button>
            <button 
              className={`nav-btn ${currentView === 'spotify' ? 'active' : ''}`}
              onClick={() => setCurrentView('spotify')}
            >
              🎵 Spotify
            </button>
          </nav>

          <div className="user-section">
            <input
              type="text"
              placeholder="Your name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              className="user-name-input"
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* Search Bar */}
        <div className="search-section">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search radio stations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchStations()}
              className="search-input"
            />
            <button onClick={searchStations} className="search-btn">
              🔍 Search
            </button>
          </div>
        </div>

        <div className="content-grid">
          {/* Left Panel - Stations */}
          <div className="stations-panel">
            {currentView === 'discover' && (
              <div>
                <h2>🔥 Popular Stations Worldwide</h2>
                <button onClick={fetchPopularStations} className="refresh-btn">
                  ↻ Refresh
                </button>
              </div>
            )}

            {currentView === 'countries' && (
              <div>
                <h2>🌍 Browse by Country</h2>
                <select
                  value={selectedCountry}
                  onChange={(e) => {
                    setSelectedCountry(e.target.value);
                    if (e.target.value) {
                      fetchStationsByCountry(e.target.value);
                    }
                  }}
                  className="country-select"
                >
                  <option value="">Select a country...</option>
                  {countries.map((country) => (
                    <option key={country.name} value={country.name}>
                      {country.name} ({country.stationcount} stations)
                    </option>
                  ))}
                </select>
              </div>
            )}

            {currentView === 'spotify' && (
              <div className="spotify-coming-soon">
                <h2>🎵 Spotify Integration</h2>
                <div className="coming-soon-card">
                  <div className="spotify-icon">🎧</div>
                  <h3>Coming Soon!</h3>
                  <p>Spotify integration is being prepared. You'll be able to:</p>
                  <ul>
                    <li>🔍 Search millions of tracks</li>
                    <li>🎵 Play full songs (Premium required)</li>
                    <li>💬 Comment on your favorite tracks</li>
                    <li>📱 Control playback from any device</li>
                  </ul>
                  <div className="setup-note">
                    <strong>Setup Required:</strong> Spotify API credentials needed
                  </div>
                </div>
              </div>
            )}

            {(currentView === 'discover' || currentView === 'countries') && (
              <div className="stations-list">
                {loading ? (
                  <div className="loading">🔄 Loading stations...</div>
                ) : (
                  stations.map((station) => (
                    <div
                      key={station.stationuuid}
                      className={`station-card ${currentStation?.stationuuid === station.stationuuid ? 'active' : ''}`}
                    >
                      <div className="station-info">
                        {station.favicon && (
                          <img src={station.favicon} alt="" className="station-favicon" />
                        )}
                        <div className="station-details">
                          <h3 className="station-name">{station.name}</h3>
                          <div className="station-meta">
                            <span className="station-country">📍 {station.country}</span>
                            <span className="station-votes">👍 {station.votes}</span>
                            {station.bitrate > 0 && (
                              <span className="station-quality">{station.bitrate}kbps</span>
                            )}
                          </div>
                          {station.tags && (
                            <div className="station-tags">
                              {station.tags.split(',').slice(0, 3).map((tag, index) => (
                                <span key={index} className="tag">#{tag.trim()}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => playStation(station)}
                        className={`play-btn ${currentStation?.stationuuid === station.stationuuid && isPlaying ? 'playing' : ''}`}
                      >
                        {currentStation?.stationuuid === station.stationuuid && isPlaying ? '⏸️' : '▶️'}
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Now Playing & Comments */}
          <div className="player-panel">
            {currentStation ? (
              <div>
                <div className="now-playing">
                  <h2>🎵 Now Playing</h2>
                  <div className="current-station">
                    {currentStation.favicon && (
                      <img src={currentStation.favicon} alt="" className="current-favicon" />
                    )}
                    <div>
                      <h3>{currentStation.name}</h3>
                      <p>📍 {currentStation.country}</p>
                      <div className="playback-controls">
                        <button onClick={stopStation} className="stop-btn">
                          ⏹️ Stop
                        </button>
                        <div className="volume-info">
                          {isPlaying ? '🔊 Playing' : '⏸️ Paused'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="comments-section">
                  <h3>💬 Comments ({comments.length})</h3>
                  
                  <div className="add-comment">
                    <textarea
                      placeholder="Share your thoughts about this station..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      className="comment-input"
                      rows="3"
                    />
                    <button onClick={addComment} className="comment-btn">
                      💬 Add Comment
                    </button>
                  </div>

                  <div className="comments-list">
                    {comments.map((comment) => (
                      <div key={comment.id} className="comment">
                        <div className="comment-header">
                          <span className="comment-author">👤 {comment.author}</span>
                          <span className="comment-time">{formatTime(comment.timestamp)}</span>
                        </div>
                        <p className="comment-content">{comment.content}</p>
                      </div>
                    ))}
                    
                    {comments.length === 0 && (
                      <div className="no-comments">
                        <p>🎭 No comments yet. Be the first to share your thoughts!</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-station">
                <div className="welcome-message">
                  <h2>🎧 Welcome to Global Music Hub</h2>
                  <p>Select a radio station to start listening and join the conversation!</p>
                  <div className="features">
                    <div className="feature">
                      <span className="feature-icon">🌍</span>
                      <span>Global radio stations</span>
                    </div>
                    <div className="feature">
                      <span className="feature-icon">💬</span>
                      <span>Real-time comments</span>
                    </div>
                    <div className="feature">
                      <span className="feature-icon">🎵</span>
                      <span>Spotify integration (coming soon)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;