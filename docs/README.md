# DocToAudiobook Documentation

## Overview

DocToAudiobook is a powerful tool for converting documents into audiobooks with advanced features like semantic analysis, contextual emphasis, and intelligent chunking. The system is built with a modular architecture and provides both a web interface and API endpoints.

## Features

- Document processing (DOCX, PDF, TXT)
- Semantic analysis for contextual emphasis
- Intelligent text chunking
- Multiple voice options and speed variants
- Bookmark management
- User authentication and management
- Job queue system for concurrent processing
- TTS caching for efficiency
- Comprehensive error handling and logging

## Architecture

The system is built with a modular architecture:

```
src/
├── core/                 # Core functionality modules
│   ├── user_manager.py   # User authentication and management
│   ├── job_queue.py      # Job processing queue
│   ├── cache_manager.py  # TTS caching
│   ├── document_processor.py  # Document handling
│   ├── audio_processor.py     # Audio processing
│   ├── chapter_manager.py     # Chapter detection
│   └── bookmark_manager.py    # Bookmark handling
├── api/                  # API endpoints
├── web/                  # Web interface
└── utils/               # Utility functions
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/doc2audiobook.git
cd doc2audiobook
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python src/init_db.py
```

5. Start the application:
```bash
python src/app.py
```

## Configuration

The application can be configured through environment variables or a config file:

```env
# API Configuration
OPENAI_API_KEY=your_api_key
TTS_ENGINE=openai  # or other supported engines

# Database Configuration
DB_PATH=./data/database.db
CACHE_DIR=./data/cache

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=False
```

## API Documentation

### Authentication

All API endpoints require authentication using JWT tokens.

1. Login to get a token:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

2. Use the token in subsequent requests:
```bash
curl -X GET http://localhost:5000/api/jobs \
  -H "Authorization: Bearer <token>"
```

### Endpoints

#### Jobs

- `POST /api/jobs` - Create a new conversion job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/<job_id>` - Get job status
- `DELETE /api/jobs/<job_id>` - Cancel a job

#### Users

- `POST /api/users` - Create a new user
- `GET /api/users/<user_id>` - Get user information
- `PUT /api/users/<user_id>` - Update user
- `DELETE /api/users/<user_id>` - Delete user

#### Audio

- `GET /api/audio/<job_id>` - Get generated audio files
- `POST /api/audio/bookmark` - Create a bookmark
- `GET /api/audio/bookmarks` - List bookmarks

## Web Interface

The web interface provides a user-friendly way to:

1. Upload and convert documents
2. Configure voice settings
3. Monitor job progress
4. Download generated audio files
5. Manage bookmarks
6. View user settings

## Development

### Running Tests

```bash
python -m unittest discover tests
```

### Code Style

The project follows PEP 8 guidelines. Use flake8 for linting:

```bash
flake8 src tests
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Security

- All passwords are hashed using bcrypt
- JWT tokens are used for authentication
- API endpoints are rate-limited
- Input validation is performed on all endpoints
- File uploads are scanned for malware

## Performance

- TTS caching reduces API calls
- Job queue handles concurrent processing
- Intelligent chunking optimizes TTS generation
- Database indexes improve query performance

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify the API key is correct
   - Check rate limits
   - Ensure proper environment variable setup

2. **File Conversion Errors**
   - Check file format support
   - Verify file integrity
   - Check available disk space

3. **Audio Generation Issues**
   - Verify TTS engine configuration
   - Check network connectivity
   - Review error logs

### Logs

Logs are stored in `logs/` directory:
- `app.log` - Application logs
- `error.log` - Error logs
- `access.log` - Access logs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## Roadmap

### Planned Features

1. Support for more document formats
2. Advanced audio processing
3. Cloud storage integration
4. User analytics
5. Microservices architecture

### Known Issues

1. Limited file format support
2. Memory usage with large documents
3. Network dependency for TTS 