#!/usr/bin/env python
"""
Simple documentation watcher for Pantheon Agents.
This script provides an alternative to sphinx-autobuild with better file watching.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DocWatcher(FileSystemEventHandler):
    def __init__(self, source_dir, build_dir):
        self.source_dir = source_dir
        self.build_dir = build_dir
        self.last_build_time = 0
        self.build_delay = 1.0  # seconds
        
    def should_rebuild(self, event):
        """Check if we should rebuild based on the event."""
        if event.is_directory:
            return False
            
        path = Path(event.src_path)
        
        # Only watch certain file types
        if path.suffix not in ['.rst', '.md', '.py', '.css', '.js', '.png', '.jpg']:
            return False
            
        # Ignore build directory
        if str(self.build_dir) in str(path):
            return False
            
        # Ignore hidden files and temp files
        if path.name.startswith('.') or path.name.endswith('~'):
            return False
            
        return True
        
    def on_modified(self, event):
        if self.should_rebuild(event):
            self.rebuild(event.src_path)
            
    def on_created(self, event):
        if self.should_rebuild(event):
            self.rebuild(event.src_path)
            
    def rebuild(self, changed_file):
        """Rebuild the documentation."""
        current_time = time.time()
        if current_time - self.last_build_time < self.build_delay:
            return
            
        self.last_build_time = current_time
        
        print(f"\n📝 File changed: {changed_file}")
        print("🔨 Rebuilding documentation...")
        
        try:
            # Run sphinx-build
            result = subprocess.run([
                sys.executable, '-m', 'sphinx',
                '-b', 'html',
                self.source_dir,
                self.build_dir
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Build successful!")
            else:
                print("❌ Build failed!")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error during build: {e}")
            
def main():
    """Main function to start the watcher."""
    source_dir = Path('source')
    build_dir = Path('build/html')
    
    if not source_dir.exists():
        print("❌ Source directory not found. Please run from docs directory.")
        sys.exit(1)
        
    print("👀 Pantheon Docs Watcher")
    print(f"📁 Watching: {source_dir.absolute()}")
    print(f"🎯 Output: {build_dir.absolute()}")
    print("🌐 Please use a separate web server to view the docs")
    print("   e.g., python -m http.server 8080 --directory build/html")
    print("\nPress Ctrl+C to stop\n")
    
    # Initial build
    print("🔨 Initial build...")
    subprocess.run([sys.executable, '-m', 'sphinx', '-b', 'html', str(source_dir), str(build_dir)])
    
    # Set up watcher
    event_handler = DocWatcher(source_dir, build_dir)
    observer = Observer()
    observer.schedule(event_handler, str(source_dir), recursive=True)
    
    # Also watch the Python source code
    pantheon_dir = Path('../pantheon')
    if pantheon_dir.exists():
        observer.schedule(event_handler, str(pantheon_dir), recursive=True)
        print(f"📁 Also watching: {pantheon_dir.absolute()}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 Stopping watcher...")
        
    observer.join()

if __name__ == '__main__':
    main()