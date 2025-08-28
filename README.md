# Cursor View

Cursor View is a local tool to view, search, and export all your Cursor AI chat histories in one place. It works by scanning your local Cursor application data directories and extracting chat data from the SQLite databases.

**Privacy Note**: All data processing happens locally on your machine. No data is sent to any external servers.

<img width="761" alt="Screenshot 2025-05-01 at 8 22 43 AM-min" src="https://github.com/user-attachments/assets/39dbfa63-8630-4287-903c-f87833a9b435" />

## Setup & Running

1. Clone this repository
2. Install Python dependencies:
   ```
   python3 -m pip install -r requirements.txt
   ```
3. Install frontend dependencies and build (optional, pre-built files included):
   ```
   cd frontend
   npm install
   npm run build
   ```
4. Start the server:
   ```
   python3 server.py
   ```
5. Start the server:
   ```
   python3 server.py
   ```
6. Open your browser to the displayed URL (local or LAN)

## Message Sending Features

The application now supports sending messages directly to Cursor AI chat with intelligent project switching and focus management:

### Automatic Cursor Restart
- **First-time sending**: When sending the first message, Cursor will be automatically closed and reopened to ensure proper focus
- **Project switching**: When switching between different projects, Cursor will be restarted to ensure the correct project context
- **Focus management**: The system automatically handles window activation and dialog opening

### How it works
1. When you send a message from the web interface, the system detects if it's the first message or if you're switching projects
2. If needed, Cursor is gracefully closed using platform-specific methods:
   - **macOS**: Uses AppleScript to quit Cursor
   - **Windows/Linux**: Uses psutil to terminate Cursor processes
3. After a brief wait, Cursor is reopened with the correct project context
4. The AI chat dialog is automatically opened and the message is sent

### Requirements
- Cursor must be installed and accessible via command line (`cursor` command)
- For Windows/Linux: `psutil` package is required for process management
- Proper permissions for AppleScript execution on macOS

## Network Access

The server automatically detects and displays both local and LAN access URLs:

- **Local access**: `http://localhost:5004` (for the same machine)
- **LAN access**: `http://192.168.x.x:5004` (for other devices on the same network)

The LAN IP address is automatically detected and displayed in:
- Server startup console output
- Web interface header (as a chip with WiFi icon)
- API endpoint `/api/server/info`

This allows easy access from mobile devices or other computers on the same network.

## Features

- Browse all Cursor chat sessions
- Search through chat history
- Export chats as JSON or standalone HTML
- Organize chats by project
- View timestamps of conversations
- Send messages to Cursor AI chat
- Automatic project switching with Cursor restart
- Smart focus management for reliable message delivery
