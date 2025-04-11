#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Import our classes
from core.config_manager import ConfigManager
from core.tts.enhanced import EnhancedTTS
from core.doc2audiobook import DocToAudiobook

class AudiobookConverterApp:
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("DocToAudiobook Converter")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Initialize converter
        self.config_manager = ConfigManager()
        self.converter = DocToAudiobook()
        
        # Create main interface
        self.create_widgets()
        
        # Check API key on startup
        self.check_api_key()
        
        # Load voice and model options
        self.load_voice_options()
        
        # Initialize with current settings
        self.load_current_settings()
    
    def check_api_key(self):
        """Check if API key is configured."""
        if not self.converter.api_key:
            result = messagebox.askyesno(
                "API Key Required",
                "No OpenAI API key found. Would you like to configure it now?"
            )
            if result:
                self.show_api_key_dialog()
            else:
                messagebox.showwarning(
                    "API Key Required",
                    "An OpenAI API key is required to use this tool."
                )
    
    def show_api_key_dialog(self):
        """Show dialog to configure API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure API Key")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog on parent window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Create dialog contents
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame, 
            text="Enter your OpenAI API key:"
        ).pack(pady=(0, 5), anchor=tk.W)
        
        api_key_var = tk.StringVar(value=self.converter.api_key or "")
        api_key_entry = ttk.Entry(frame, textvariable=api_key_var, width=50, show="*")
        api_key_entry.pack(pady=5, fill=tk.X)
        
        show_key_var = tk.BooleanVar(value=False)
        show_key_check = ttk.Checkbutton(
            frame, 
            text="Show API key", 
            variable=show_key_var,
            command=lambda: api_key_entry.config(show="" if show_key_var.get() else "*")
        )
        show_key_check.pack(pady=5, anchor=tk.W)
        
        # Create buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="Save", 
            command=lambda: self.save_api_key(api_key_var.get(), dialog)
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def save_api_key(self, api_key, dialog):
        """Save API key to config."""
        if not api_key:
            messagebox.showerror("Error", "API key cannot be empty")
            return
        
        if self.converter.set_api_key(api_key):
            messagebox.showinfo("Success", "API key saved successfully")
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to save API key")
    
    def load_voice_options(self):
        """Load available voice and model options."""
        # Get available voice options
        self.voice_options = list(self.converter.get_available_voices().keys())
        self.voice_combobox['values'] = self.voice_options
        
        # Get available model options
        self.model_options = list(self.converter.get_available_models().keys())
        self.model_combobox['values'] = self.model_options
        
        # Get available style presets
        self.style_presets = list(self.converter.get_voice_style_presets().keys())
        self.style_combobox['values'] = ['custom'] + self.style_presets
    
    def load_current_settings(self):
        """Load current settings into UI."""
        # Load voice settings
        voice_settings = self.converter.voice_settings
        
        if voice_settings.get("voice_id") in self.voice_options:
            self.voice_var.set(voice_settings.get("voice_id"))
        
        if voice_settings.get("model") in self.model_options:
            self.model_var.set(voice_settings.get("model"))
        
        self.speed_var.set(str(voice_settings.get("speed", 1.0)))
        
        # Style handling
        style = voice_settings.get("style", "neutral")
        if style in self.style_presets:
            self.style_var.set(style)
        else:
            self.style_var.set("custom")
            self.custom_style_var.set(style)
        
        # Emotion handling
        self.emotion_var.set(voice_settings.get("emotion", ""))
        
        # Load output settings
        output_settings = self.converter.output_settings
        
        self.format_var.set(output_settings.get("format", "mp3"))
        self.quality_var.set(output_settings.get("quality", "high"))
        self.chapter_pause_var.set(str(output_settings.get("pause_between_chapters", 1000)))
        self.combine_chapters_var.set(output_settings.get("combine_chapters", True))
        
        # Update UI based on model selection
        self.on_model_change()
    
    def on_model_change(self, *args):
        """Update UI based on selected model."""
        model = self.model_var.get()
        
        # Enable/disable style options based on model
        steerable = model == "gpt-4o-mini-tts"
        
        state = "normal" if steerable else "disabled"
        self.style_combobox.config(state=state)
        self.emotion_entry.config(state=state)
        
        # Update custom style field state
        self.on_style_change()
    
    def on_style_change(self, *args):
        """Update custom style field based on style selection."""
        style = self.style_var.get()
        model = self.model_var.get()
        
        # Enable custom style field if "custom" is selected and model supports it
        steerable = model == "gpt-4o-mini-tts"
        custom_selected = style == "custom"
        
        state = "normal" if steerable and custom_selected else "disabled"
        self.custom_style_entry.config(state=state)
    
    def create_widgets(self):
        """Create UI widgets."""
        # Create notebook with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main tab
        self.main_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.main_frame, text="Convert")
        
        # Create voice settings tab
        self.voice_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.voice_frame, text="Voice Settings")
        
        # Create output settings tab
        self.output_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.output_frame, text="Output Settings")
        
        # Create advanced settings tab
        self.advanced_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.advanced_frame, text="Advanced")
        
        # Configure Main tab
        self.create_main_tab()
        
        # Configure Voice Settings tab
        self.create_voice_tab()
        
        # Configure Output Settings tab
        self.create_output_tab()
        
        # Configure Advanced Settings tab
        self.create_advanced_tab()
        
        # Create status bar
        self.status_bar = ttk.Label(
            self.root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_main_tab(self):
        """Create main conversion tab."""
        # Input file section
        input_frame = ttk.LabelFrame(self.main_frame, text="Input Document", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_file_var = tk.StringVar()
        ttk.Entry(
            input_frame, 
            textvariable=self.input_file_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            input_frame, 
            text="Browse", 
            command=self.browse_input_file
        ).pack(side=tk.RIGHT)
        
        # Output directory section
        output_frame = ttk.LabelFrame(self.main_frame, text="Output Directory", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir_var = tk.StringVar()
        ttk.Entry(
            output_frame, 
            textvariable=self.output_dir_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            output_frame, 
            text="Browse", 
            command=self.browse_output_dir
        ).pack(side=tk.RIGHT)
        
        # Recent files section
        recent_frame = ttk.LabelFrame(self.main_frame, text="Recent Files", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create listbox with scrollbar
        recent_scrollbar = ttk.Scrollbar(recent_frame)
        recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recent_listbox = tk.Listbox(
            recent_frame, 
            height=5,
            yscrollcommand=recent_scrollbar.set
        )
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recent_scrollbar.config(command=self.recent_listbox.yview)
        
        # Load recent files
        self.load_recent_files()
        
        # Bind double-click on recent files
        self.recent_listbox.bind("<Double-1>", self.select_recent_file)
        
        # Conversion button
        convert_button = ttk.Button(
            self.main_frame, 
            text="Convert to Audiobook", 
            command=self.start_conversion,
            style="Accent.TButton"
        )
        convert_button.pack(pady=10, padx=50, ipady=5)
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.main_frame, 
            variable=progress_var, 
            mode="indeterminate",
            length=300
        )
        progress_bar.pack(pady=5)
        
        # Progress Label
        self.progress_label = ttk.Label(self.main_frame, text="Initializing...")
        self.progress_label.pack(pady=5)
    
    def create_voice_tab(self):
        """Create voice settings tab."""
        # Create form layout
        form_frame = ttk.Frame(self.voice_frame, padding=5)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # TTS Model
        ttk.Label(form_frame, text="TTS Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            form_frame, 
            textvariable=self.model_var, 
            state="readonly",
            width=20
        )
        self.model_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_change)
        
        ttk.Label(
            form_frame, 
            text="Select the TTS model to use", 
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Voice ID
        ttk.Label(form_frame, text="Voice:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar()
        self.voice_combobox = ttk.Combobox(
            form_frame, 
            textvariable=self.voice_var, 
            state="readonly",
            width=20
        )
        self.voice_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Select the voice identity", 
            foreground="gray"
        ).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Speed
        ttk.Label(form_frame, text="Speed:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.StringVar(value="1.0")
        speed_entry = ttk.Spinbox(
            form_frame, 
            from_=0.25, 
            to=4.0, 
            increment=0.05,
            textvariable=self.speed_var,
            width=10
        )
        speed_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Speech rate (0.25 to 4.0)", 
            foreground="gray"
        ).grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Style
        ttk.Label(form_frame, text="Style:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.style_var = tk.StringVar(value="neutral")
        self.style_combobox = ttk.Combobox(
            form_frame, 
            textvariable=self.style_var, 
            state="readonly",
            width=20
        )
        self.style_combobox.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.style_combobox.bind("<<ComboboxSelected>>", self.on_style_change)
        
        ttk.Label(
            form_frame, 
            text="Voice style preset (for steerable models)", 
            foreground="gray"
        ).grid(row=3, column=2, sticky=tk.W, padx=5)
    
    def create_output_tab(self):
        """Create output settings tab."""
        # Create form layout
        form_frame = ttk.Frame(self.output_frame, padding=5)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Format
        ttk.Label(form_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mp3")
        format_combobox = ttk.Combobox(
            form_frame, 
            textvariable=self.format_var, 
            state="readonly",
            width=20
        )
        format_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Select the output format", 
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Quality
        ttk.Label(form_frame, text="Quality:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="high")
        quality_combobox = ttk.Combobox(
            form_frame, 
            textvariable=self.quality_var, 
            state="readonly",
            width=20
        )
        quality_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Select the output quality", 
            foreground="gray"
        ).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Chapter pause
        ttk.Label(form_frame, text="Chapter Pause:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.chapter_pause_var = tk.StringVar(value="1000")
        chapter_pause_entry = ttk.Entry(
            form_frame, 
            textvariable=self.chapter_pause_var, 
            width=20
        )
        chapter_pause_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Pause between chapters (ms)", 
            foreground="gray"
        ).grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Combine chapters
        ttk.Label(form_frame, text="Combine Chapters:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.combine_chapters_var = tk.BooleanVar(value=True)
        combine_chapters_check = ttk.Checkbutton(
            form_frame, 
            text="Combine chapters", 
            variable=self.combine_chapters_var
        )
        combine_chapters_check.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
    
    def create_advanced_tab(self):
        """Create advanced settings tab."""
        # Create form layout
        form_frame = ttk.Frame(self.advanced_frame, padding=5)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Emotion
        ttk.Label(form_frame, text="Emotion:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.emotion_var = tk.StringVar()
        emotion_entry = ttk.Entry(
            form_frame, 
            textvariable=self.emotion_var, 
            width=20
        )
        emotion_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Enter emotion description", 
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Custom style
        ttk.Label(form_frame, text="Custom Style:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.custom_style_var = tk.StringVar()
        custom_style_entry = ttk.Entry(
            form_frame, 
            textvariable=self.custom_style_var, 
            width=20
        )
        custom_style_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            form_frame, 
            text="Enter custom style description", 
            foreground="gray"
        ).grid(row=1, column=2, sticky=tk.W, padx=5)
    
    def browse_input_file(self):
        """Open file dialog to select input file."""
        file_path = filedialog.askopenfilename(
            title="Select Input Document",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.input_file_var.set(file_path)
    
    def browse_output_dir(self):
        """Open directory dialog to select output directory."""
        dir_path = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if dir_path:
            self.output_dir_var.set(dir_path)
    
    def load_recent_files(self):
        """Load recent files from config."""
        recent_files = self.config_manager.get_recent_files()
        self.recent_listbox.delete(0, tk.END)
        for file in recent_files:
            self.recent_listbox.insert(tk.END, file)
    
    def select_recent_file(self, event):
        """Select a recent file from the listbox."""
        if event.widget.curselection():
            selected_file = event.widget.get(event.widget.curselection()[0])
            self.input_file_var.set(selected_file)
    
    def start_conversion(self):
        """Start the conversion process."""
        input_file = self.input_file_var.get()
        output_dir = self.output_dir_var.get()
        
        if not input_file or not output_dir:
            messagebox.showerror("Error", "Please specify both input file and output directory")
            return
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.main_frame, 
            variable=progress_var, 
            mode="indeterminate",
            length=300
        )
        progress_bar.pack(pady=5)
        
        status_label = ttk.Label(self.main_frame, text="Initializing...")
        status_label.pack(pady=5)
        
        cancel_button = ttk.Button(
            self.main_frame, 
            text="Cancel", 
            command=self.progress_dialog.destroy
        )
        cancel_button.pack(pady=10)
        
        # Update UI
        self.root.update()
        
        # Define update callback for progress (simplified)
        def update_status_display(message):
            status_label.config(text=message)
            self.root.update() # Keep UI responsive
        
        # Run conversion in a separate thread
        import threading
        
        def conversion_thread():
            # Start indeterminate progress bar
            progress_bar.start(10)
            update_status_display("Extracting text...")
            try:
                # Update original DocToAudiobook class to support progress callback
                success, audio_files = self.converter.create_audiobook(
                    input_file,
                    output_dir=output_dir,
                    max_chapters=max_chapters,
                    use_ocr=use_ocr,
                    chapter_detection_prompt=chapter_prompt if chapter_prompt else None
                    # No progress callback needed for simplified version
                )
                
                # Stop progress bar
                progress_bar.stop()
                self.progress_dialog.destroy()
                
                if success:
                    # Show success message
                    messagebox.showinfo(
                        "Conversion Complete", 
                        f"Successfully created audiobook with {len(audio_files)} files in {output_dir}"
                    )
                    
                    # Ask if user wants to open output directory
                    if messagebox.askyesno(
                        "Open Folder", 
                        "Would you like to open the output folder?"
                    ):
                        self.open_folder(output_dir)
                    
                    # Refresh recent files list
                    self.load_recent_files()
                else:
                    messagebox.showerror(
                        "Conversion Failed", 
                        "Failed to convert document to audiobook. Check console for errors."
                    )
            except Exception as e:
                progress_bar.stop()
                self.progress_dialog.destroy()
                messagebox.showerror(
                    "Error", 
                    f"An error occurred during conversion: {str(e)}"
                )
                print(f"Conversion Error Traceback:", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        # Start conversion thread
        threading.Thread(target=conversion_thread, daemon=True).start()
    
    def update_status(self, message):
        """Update the status bar with a message."""
        self.status_bar.config(text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudiobookConverterApp(root)
    root.mainloop() 