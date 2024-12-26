#!/usr/bin/env python3

"""
AVR (Audio Visual Recorder)
A background service to detect keyboard shortcuts and trigger actions.

This module provides functionality to:
1. Detect keyboard shortcuts (configurable)
2. Capture screenshots (using pyscreenshot)
3. Analyze images using OpenAI's Vision API (gpt-4o)
4. Save analysis to knowledge base (if configured)
5. Provide audio feedback on action events (start, complete, error)

Author: Aditya Patange
Project: The Hackers Playbook, Valuable Internal Tools (VIT)
"""

from pynput import keyboard
import argparse
import sys
from typing import Callable, Optional, Literal
import pyscreenshot
import base64
from io import BytesIO
from openai import OpenAI
import os
import dotenv
from datetime import datetime
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading
import queue
import pyperclip

dotenv.load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
knowledge_source_path = os.getenv("KNOWLEDGE_SOURCE_PATH")

SYSTEM_PROMPT = """You are an expert at extracting and organizing information from images.
Extract and format the following in markdown, treating each visually distinct section as a separate block:

0. ID: "{ID_in_underscore_case}"
1. Blocks: Identify and number each visually distinct section/block in the image
2. Main Text Content: Filter out noise and extract only important text for each block
3. Metadata: Details like post counts, likes, dates, etc.
4. URLs: Any links found in the image
5. Include the context of the image in your response, describe what the screenshot is about

Format your response as:

# ID
[ID_in_underscore_case]

# Blocks

## Block 1
[Description of what this block represents (e.g., "Header Section", "Main Content", "Comments Section")]

### Content
[Main text content for this block]

### Metadata
- [metadata point 1]
- [metadata point 2]

## Block 2
[Description of block 2]

### Content
[Content for block 2]

### Metadata
- [metadata for block 2]

[... repeat for all blocks ...]

# Overall

## URLs
- [url 1]
- [url 2]

## Context
[Overall context of the image, how blocks relate to each other]
"""

if platform.system() == "Windows":
    import winsound


class HotkeyService:
    """
    A service that listens for keyboard shortcuts and triggers actions.

    This class manages keyboard event detection, screenshot capture,
    image analysis, and knowledge base storage.

    Attributes:
        hotkey (set): Set of keys that trigger the action
        callback (Callable): Function to call when hotkey is pressed
        current_keys (set): Currently pressed keys
    """

    def __init__(self, hotkey: str = "command+x", callback: Optional[Callable] = None):
        """
        Initialize the hotkey service.

        Args:
            hotkey (str): Keyboard shortcut to listen for (default: command+x)
            callback (Optional[Callable]): Function to call when hotkey is pressed
        """
        self.hotkey = self._parse_hotkey(hotkey)
        self.current_keys = set()
        self.last_trigger_time = 0
        self.TRIGGER_COOLDOWN = 0.5

        # Queue configuration
        self.MAX_QUEUE_SIZE = 10
        self.processing_queue = Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.processing_thread = threading.Thread(
            target=self._process_queue, daemon=True
        )
        self.processing_thread.start()

        if knowledge_source_path:
            os.makedirs(knowledge_source_path, exist_ok=True)

        # Set up hotkeys
        self.screenshot_hotkey = self._parse_hotkey(hotkey)
        self.clipboard_hotkey = self._parse_hotkey("cmd+z")

    def _parse_hotkey(self, hotkey: str) -> set:
        """
        Convert hotkey string to set of keys.

        Args:
            hotkey (str): String representation of hotkey (e.g., "cmd+x")

        Returns:
            set: Set of individual keys
        """
        return set(hotkey.lower().replace("command+", "cmd+").split("+"))

    def _take_screenshot(self) -> str:
        """
        Capture screen and convert to base64.

        Returns:
            str: Base64 encoded PNG image
        """
        try:
            screenshot = pyscreenshot.grab()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            print(f"❌ Failed to take screenshot: {str(e)}")
            return ""

    def _analyze_image(self, base64_img: str) -> str:
        """
        Analyze image using OpenAI's Vision API.

        Args:
            base64_img (str): Base64 encoded image

        Returns:
            str: Analysis in markdown format
        """
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": SYSTEM_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_img}"
                                },
                            },
                        ],
                    }
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Failed to analyze image: {str(e)}"

    def _get_knowledge_file(self) -> str:
        """
        Get path to today's knowledge file.

        Returns:
            str: Path to knowledge file

        Raises:
            ValueError: If KNOWLEDGE_SOURCE_PATH not set
        """
        if not knowledge_source_path:
            raise ValueError("KNOWLEDGE_SOURCE_PATH not set in environment")

        today = datetime.now().strftime("%Y%m%d")
        return os.path.join(knowledge_source_path, f"running_knowledge_{today}.md")

    def _append_to_knowledge(self, analysis: str) -> None:
        """
        Append analysis to knowledge file with timestamp.

        Args:
            analysis (str): Analysis to append
        """
        try:
            knowledge_file = self._get_knowledge_file()
            timestamp = datetime.now().strftime("%H:%M:%S")

            with open(knowledge_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## Captured at {timestamp}\n\n")
                f.write(analysis)
                f.write("\n\n---\n")

            print(f"📝 Analysis appended to {knowledge_file}")
        except Exception as e:
            print(f"❌ Failed to save analysis: {str(e)}")

    def play_sound(self, sound_type: str) -> None:
        """
        Play system sound based on event type.

        Args:
            sound_type (str): Type of sound ("start", "complete", or "error")
        """
        try:
            if platform.system() == "Darwin":  # macOS
                if sound_type == "start":
                    os.system("afplay /System/Library/Sounds/Ping.aiff")
                elif sound_type == "complete":
                    os.system("afplay /System/Library/Sounds/Glass.aiff")
                elif sound_type == "error":
                    os.system("afplay /System/Library/Sounds/Basso.aiff")
            elif platform.system() == "Windows":
                if sound_type == "start":
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                elif sound_type == "complete":
                    winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)
                elif sound_type == "error":
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except Exception as e:
            print(f"Failed to play sound: {e}")

    def _process_queue(self):
        """Process items from the queue."""
        while True:
            try:
                content, source = self.processing_queue.get(timeout=1)
                if content:
                    future = self.executor.submit(
                        self._process_content_item, content, source
                    )
                    future.add_done_callback(self._on_analysis_complete)
                    self.processing_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing queue: {e}")
                time.sleep(1)

    def _process_content_item(self, content: str, source: str) -> tuple[str, bool]:
        """Process a single content item."""
        try:
            print(f"📝 Processing {source}...")
            if source == "screenshot":
                analysis = self._analyze_image(content)
            else:  # clipboard
                # Just format the clipboard content with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                analysis = f"""# Clipboard Content ({timestamp})

{content}

---"""
            success = True  # Always true for clipboard content
            return analysis, success
        except Exception as e:
            print(f"Error processing {source}: {e}")
            return str(e), False

    def _analyze_text(self, text: str) -> str:
        """Analyze clipboard text content."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"{SYSTEM_PROMPT}\n\nAnalyze this text:\n{text}",
                    }
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Failed to analyze text: {str(e)}"

    def _process_content(
        self, content: str, source: Literal["screenshot", "clipboard"]
    ) -> None:
        """Process content from either screenshot or clipboard."""
        try:
            self.processing_queue.put((content, source), timeout=1)
            queue_size = self.processing_queue.qsize()
            print(
                f"📥 {source.title()} content added to processing queue... ({queue_size}/{self.MAX_QUEUE_SIZE})"
            )
        except queue.Full:
            print(
                "⚠️ Processing queue is full! Please wait for current tasks to complete."
            )
            self.play_sound("error")

    def _clipboard_callback(self) -> None:
        """Handle clipboard content processing."""
        print(f"\n📋 Clipboard processing triggered!")
        self.play_sound("start")

        try:
            content = pyperclip.paste()
            if content.strip():
                self._process_content(content, "clipboard")
            else:
                print("❌ Clipboard is empty!")
                self.play_sound("error")
        except Exception as e:
            print(f"❌ Failed to read clipboard: {e}")
            self.play_sound("error")

    def _screenshot_callback(self) -> None:
        """Handle screenshot processing."""
        print(f"\n🎯 Screenshot triggered!")
        self.play_sound("start")

        base64_img = self._take_screenshot()
        if base64_img:
            self._process_content(base64_img, "screenshot")

    def _on_press(self, key) -> None:
        """
        Handle key press events.

        Args:
            key: The key that was pressed
        """
        try:
            current_time = time.time()

            if hasattr(key, "char"):
                self.current_keys.add(key.char)
            elif key == keyboard.Key.cmd:
                self.current_keys.add("cmd")

            # Check both hotkeys
            if current_time - self.last_trigger_time > self.TRIGGER_COOLDOWN:
                if self.current_keys == self.screenshot_hotkey:
                    self._screenshot_callback()
                    self.last_trigger_time = current_time
                    self.current_keys.clear()
                elif self.current_keys == self.clipboard_hotkey:
                    self._clipboard_callback()
                    self.last_trigger_time = current_time
                    self.current_keys.clear()
        except AttributeError:
            pass

    def _on_release(self, key) -> None:
        """
        Handle key release events.

        Args:
            key: The key that was released
        """
        try:
            # Remove released key
            if hasattr(key, "char"):
                self.current_keys.discard(key.char)
            elif key == keyboard.Key.cmd:
                self.current_keys.discard("cmd")

            # If all hotkey keys are released, clear the set
            if not any(k in self.current_keys for k in self.hotkey):
                self.current_keys.clear()
        except AttributeError:
            pass

    def start(self) -> None:
        """Start listening for keyboard events."""
        try:
            print(f"🚀 AVR is running... Listening for '{'+'.join(self.hotkey)}'")
            print("Press Ctrl+C to exit")

            with keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            ) as listener:
                listener.join()

        except KeyboardInterrupt:
            print("\n👋 Shutting down AVR...")
            self.executor.shutdown(wait=False)  # Shutdown thread pool
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.executor.shutdown(wait=False)
            sys.exit(1)

    def _on_analysis_complete(self, future) -> None:
        """
        Handle completed analysis.

        Args:
            future: Future object containing analysis result
        """
        try:
            analysis, success = future.result()

            if not success:
                self.play_sound("error")
            else:
                self.play_sound("complete")

            print("\n" + "=" * 50 + "\n")
            print(analysis)
            print("\n" + "=" * 50)

            if knowledge_source_path:
                self._append_to_knowledge(analysis)
                self.play_sound("complete")
            else:
                self.play_sound("error")
        except Exception as e:
            print(f"Error handling analysis completion: {e}")
            self.play_sound("error")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="AVR - Audio Visual Recorder")
    parser.add_argument(
        "-s",
        "--shortcut",
        default="cmd+x",
        help="Keyboard shortcut to trigger the action (default: cmd+x)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the application."""
    args = parse_args()
    service = HotkeyService(hotkey=args.shortcut)
    service.start()


if __name__ == "__main__":
    main()
