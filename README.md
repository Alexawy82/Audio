# DocToAudiobook

A web application for converting documents (PDF, DOCX) to audiobooks using OpenAI's Text-to-Speech API.

## Features

- Upload PDF or DOCX files and convert them to high-quality audiobooks
- Configurable voice settings (model, voice, speed, style)
- Audio enhancements (normalization, compression, equalization)
- Automatic chapter detection and bookmark generation
- Download individual chapter files or complete audiobooks as ZIP
- Job management system with status tracking
- Multiple voices and style options

## Installation

### Docker Installation (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Audio
   ```

2. Create .env file from example:
   ```bash
   cp .env.example .env
   ```

3. Edit the .env file to add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_random_secret_key
   ```

4. Build and run using Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at http://localhost:5000

### Manual Installation

#### Prerequisites

- Python 3.10 or higher
- FFmpeg (required for audio processing)
- libmagic1 (for file type detection)

#### Installing System Dependencies

FFmpeg and libmagic are required for proper operation:

**Windows:**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the files and place the bin directory in your PATH
3. Restart your system

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg libmagic1
```

#### Application Setup

1. Clone the repository
```bash
git clone <repository-url>
cd Audio
```

2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install the dependencies
```bash
pip install -r requirements.txt
```

4. Create necessary directories
```bash
mkdir -p data/uploads data/output data/temp data/cache data/logs
```

5. Create .env file with configuration
```bash
cp .env.example .env
# Edit the .env file with your settings
```

6. Run diagnostics to check your setup
```bash
python src/diagnose.py --all
```

7. Run the application
```bash
python src/app.py
```

8. If you encounter any issues, run the cleanup script
```bash
python src/cleanup.py --all
```

## Configuration

### Environmental Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | Your OpenAI API key | (Required) |
| SECRET_KEY | Flask session encryption key | (Random generated) |
| PORT | Port for the web server | 5000 |
| HOST | Host to bind | 0.0.0.0 |
| DEBUG | Enable debug mode | false |
| MAX_UPLOAD_SIZE | Max upload file size in bytes | 50MB (52428800) |
| DATA_DIR | Main data directory | ./data |

### OpenAI API Key

To use the application, you need an OpenAI API key with access to the TTS API:

1. Sign up for an OpenAI account at [openai.com](https://openai.com)
2. Generate an API key in your OpenAI dashboard
3. Enter the API key in the application's configuration page or set it in the .env file

### Voice Settings

The following voice options are available:
- Models:
  - tts-1: Standard quality voice
  - tts-1-hd: Higher quality voice (more expensive)
- Voices:
  - alloy: Balanced, versatile voice
  - echo: Soft, conversational voice
  - fable: Narrative, storytelling voice
  - onyx: Deep, powerful voice
  - nova: Friendly, warm voice
  - shimmer: Clear, precise voice
- Speed: 0.5-2.0x
- Styles: neutral, cheerful, serious, excited, sad, custom

## Usage

1. Start the application using Docker or manually
2. Open your browser and navigate to: `http://localhost:5000`
3. Configure your OpenAI API key if not already set via environment variable
4. Upload a document (PDF or DOCX)
5. Configure voice settings:
   - Select voice (alloy, echo, fable, onyx, nova, shimmer)
   - Select model (tts-1, tts-1-hd)
   - Adjust speed (0.5-2.0)
   - Choose style (neutral, cheerful, serious, excited, sad)
6. Configure output settings:
   - Format (mp3)
   - Bitrate (128k, 192k, 256k)
   - Enable/disable normalization
7. Submit the job and monitor progress on the job status page
8. Download individual chapter files or the complete audiobook as a ZIP archive

## Architecture & Project Structure

The application consists of the following components:

- `src/` - Application source code
  - `app.py` - Main web application (Flask)
  - `core/` - Core functionality
    - `doc2audiobook.py` - Main conversion orchestrator
    - `document_processor.py` - Document text extraction
    - `audio_processor.py` - Audio processing and enhancement
    - `chapter_manager.py` - Chapter detection and organization
    - `bookmark_manager.py` - Creates audio bookmarks for navigation
    - `job_manager.py` - Manages conversion jobs and cleanup
    - `tts/` - Text-to-speech implementation
      - `enhanced.py` - Audio enhancements (normalization, compression)
      - `models.py` - TTS data models
      - `engine.py` - TTS core functionality
    - `utils/` - Utility functions
      - `openai_helper.py` - OpenAI API client utilities
      - `error.py` - Error handling

- `data/` - Data directories
  - `uploads/` - Uploaded documents
  - `output/` - Generated audiobooks
  - `temp/` - Temporary files
  - `cache/` - Cache for TTS outputs
  - `logs/` - Application logs

## Development

### Running Tests

Run tests with pytest:
```bash
pytest tests/
```

### Code Formatting

Format code with black:
```bash
black src/
```

### Building Docker Image

```bash
docker build -t doctoaudiobook .
```

## Troubleshooting

### FFmpeg errors
If you see warnings about FFmpeg not being found, make sure it's properly installed:
- Check your system PATH to ensure FFmpeg is accessible
- In Docker, verify the FFmpeg installation in the container

### API Key issues
If you encounter OpenAI API key errors:
- Ensure your OpenAI API key is valid and has permission for the TTS API
- Check that API key is properly configured in environment or application settings
- Verify your OpenAI account has sufficient credits/billing setup

### Proxy issues
If you're behind a proxy and encounter connection issues:
- The application is configured to ignore proxy settings when calling OpenAI
- If needed, update the OpenAI client configuration in `openai_helper.py`

### Large file processing
For large documents:
- Consider adjusting the max_chapters parameter in the code
- Split very large documents into smaller parts
- Increase the memory allocated to containers if using Docker

## License

This project is licensed under the MIT License - see the LICENSE file for details. 