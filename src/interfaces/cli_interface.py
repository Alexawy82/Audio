#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

# Import our classes
from core.config_manager import ConfigManager
from core.tts.enhanced import EnhancedTTS
from core.doc2audiobook import DocToAudiobook

def main():
    """Main entry point for the DocToAudiobook CLI."""
    parser = argparse.ArgumentParser(
        description='Convert documents to audiobooks with enhanced TTS capabilities',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Configure API key command
    config_parser = subparsers.add_parser('config', help='Configure tool settings')
    config_parser.add_argument('--api-key', help='Set OpenAI API key')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    
    # Voice settings command
    voice_parser = subparsers.add_parser('voice', help='Configure voice settings')
    voice_parser.add_argument('--model', choices=['tts-1', 'tts-1-hd', 'gpt-4o-mini-tts'], 
                             help='TTS model to use')
    voice_parser.add_argument('--voice-id', help='Voice ID to use')
    voice_parser.add_argument('--speed', type=float, help='Speech rate (0.25 to 4.0)')
    voice_parser.add_argument('--style', help='Voice style (for steerable models)')
    voice_parser.add_argument('--emotion', help='Emotional quality (for steerable models)')
    voice_parser.add_argument('--list', action='store_true', help='List available voice options')
    
    # Output settings command
    output_parser = subparsers.add_parser('output', help='Configure output settings')
    output_parser.add_argument('--format', choices=['mp3', 'wav', 'ogg'], help='Output audio format')
    output_parser.add_argument('--quality', choices=['low', 'medium', 'high'], help='Audio quality')
    output_parser.add_argument('--bitrate', help='Audio bitrate (e.g., "192k")')
    output_parser.add_argument('--chapter-pause', type=int, help='Pause between chapters (ms)')
    output_parser.add_argument('--combine', type=bool, help='Combine chapters into one file')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert document to audiobook')
    convert_parser.add_argument('input_file', help='Input document file (DOCX/PDF)')
    convert_parser.add_argument('--output-dir', help='Output directory')
    convert_parser.add_argument('--max-chapters', type=int, default=30, 
                              help='Maximum chapters to detect')
    convert_parser.add_argument('--use-ocr', type=bool, default=True, 
                              help='Use OCR for PDF text extraction')
    convert_parser.add_argument('--prompt', help='Custom chapter detection prompt')
    
    # Recent files command
    recent_parser = subparsers.add_parser('recent', help='Show recently processed files')
    
    # Parse arguments, skipping the 'cli' argument itself
    args = parser.parse_args(sys.argv[2:])
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return
    
    # Handle configuration command
    if args.command == 'config':
        if args.api_key:
            if config_manager.set_api_key(args.api_key):
                print(f"API key successfully updated")
            else:
                print(f"Failed to update API key")
        
        if args.show:
            config = config_manager._load_config()
            api_key = config.get("api_key", "")
            # Mask API key for security
            if api_key:
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
                print(f"API Key: {masked_key}")
            else:
                print("API Key: Not configured")
            
            voice_settings = config.get("voice_settings", {})
            print("\nVoice Settings:")
            for key, value in voice_settings.items():
                print(f"  {key}: {value}")
            
            output_settings = config.get("output_settings", {})
            print("\nOutput Settings:")
            for key, value in output_settings.items():
                print(f"  {key}: {value}")
    
    # Handle voice settings command
    elif args.command == 'voice':
        converter = DocToAudiobook()
        
        if args.list:
            print("Available TTS Models:")
            for model_id, description in converter.get_available_models().items():
                print(f"  {model_id}: {description}")
            
            print("\nAvailable Voices:")
            for voice_id, description in converter.get_available_voices().items():
                print(f"  {voice_id}: {description}")
            
            print("\nVoice Style Presets:")
            for style_id, description in converter.get_voice_style_presets().items():
                print(f"  {style_id}: {description}")
            return
        
        # Create a settings dictionary for updating
        settings = {}
        if args.model:
            settings["model"] = args.model
        if args.voice_id:
            settings["voice_id"] = args.voice_id
        if args.speed is not None:
            settings["speed"] = max(0.25, min(4.0, args.speed))  # Clamp to valid range
        if args.style:
            settings["style"] = args.style
        if args.emotion:
            settings["emotion"] = args.emotion
        
        # Update settings if any were provided
        if settings:
            if converter.update_voice_settings(settings):
                print("Voice settings updated successfully")
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print("Failed to update voice settings")
    
    # Handle output settings command
    elif args.command == 'output':
        converter = DocToAudiobook()
        
        # Create a settings dictionary for updating
        settings = {}
        if args.format:
            settings["format"] = args.format
        if args.quality:
            settings["quality"] = args.quality
        if args.bitrate:
            settings["bitrate"] = args.bitrate
        if args.chapter_pause is not None:
            settings["pause_between_chapters"] = args.chapter_pause
        if args.combine is not None:
            settings["combine_chapters"] = args.combine
        
        # Update settings if any were provided
        if settings:
            if converter.update_output_settings(settings):
                print("Output settings updated successfully")
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print("Failed to update output settings")
    
    # Handle convert command
    elif args.command == 'convert':
        # Check if input file exists
        if not os.path.exists(args.input_file):
            print(f"Error: Input file not found: {args.input_file}")
            return
        
        # Initialize converter
        converter = DocToAudiobook()
        
        # Check API key
        if not converter.api_key:
            print("Error: No API key configured. Run 'config --api-key=YOUR_KEY' first.")
            return
        
        # Run conversion
        print(f"Converting {args.input_file} to audiobook...")
        success, audio_files = converter.create_audiobook(
            args.input_file,
            output_dir=args.output_dir,
            max_chapters=args.max_chapters,
            use_ocr=args.use_ocr,
            chapter_detection_prompt=args.prompt
        )
        
        if success:
            print("\nConversion completed successfully!")
            print(f"Created {len(audio_files)} audio files:")
            for audio_file in audio_files:
                print(f"  {audio_file}")
        else:
            print("\nConversion failed.")
    
    # Handle recent files command
    elif args.command == 'recent':
        recent_files = config_manager.get_recent_files()
        if recent_files:
            print("Recently processed files:")
            for i, file_path in enumerate(recent_files, 1):
                print(f"  {i}. {file_path}")
        else:
            print("No recently processed files found.")

if __name__ == "__main__":
    main() 