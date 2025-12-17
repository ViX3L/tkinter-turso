# Pet Manager

A desktop application for managing pets with offline-first architecture using Tkinter and Turso (LibSQL).

## Features

- **User Authentication**: Register and login with secure password hashing (bcrypt)
- **Pet Management**: Full CRUD operations for pets (name, species, breed, age, weight, notes)
- **Offline-First**: Works completely offline with local SQLite database
- **Cloud Sync**: Automatic synchronization with Turso cloud database when online
- **Session Persistence**: Stay logged in across app restarts
- **Visual Sync Status**: See online/offline status and pending changes

## Project Structure

```
tkinter-turso/
├── main.py              # Application entry point
├── app.py               # Main application controller
├── config.py            # Configuration settings
├── database.py          # Database operations and sync logic
├── auth.py              # Authentication and session management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── ui/
    ├── __init__.py
    ├── styles.py        # UI styling constants
    ├── components.py    # Reusable UI components
    ├── dialogs.py       # Dialog windows
    └── views.py         # Main application views
```

## Setup

### 1. Install Dependencies

```bash
cd tkinter-turso
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Turso (Optional - for cloud sync)

1. Create a free account at [turso.tech](https://turso.tech/)
2. Create a new database
3. Get your database URL and auth token
4. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
TURSO_DATABASE_URL=libsql://your-database-name.turso.io
TURSO_AUTH_TOKEN=your-auth-token-here
```

**Note**: The app works fully offline without Turso configuration. Sync features will simply be disabled.

### 3. Run the Application

```bash
python main.py
```

## Usage

### First Time
1. Click "Register" to create a new account
2. Enter a username (min 3 characters) and password (min 6 characters)
3. After registration, login with your credentials

### Managing Pets
- Click "Add Pet" to add a new pet
- Click on a pet in the table to view details
- Use "Edit" to modify pet information
- Use "Delete" to remove a pet (soft delete)

### Sync
- The status indicator shows online/offline status
- Pending changes are shown in the status
- Click "Sync" to manually sync with the cloud
- Auto-sync runs every 30 seconds when online

## Architecture

### Offline-First Design
- All data is stored locally in SQLite first
- Changes are marked as "pending" until synced
- When online, changes are pushed to Turso cloud
- Conflict resolution uses last-write-wins strategy

### Database Schema
- **users**: User accounts with hashed passwords
- **pets**: Pet records linked to users
- **sync_log**: Tracks changes for synchronization

### Session Management
- Sessions are stored locally in JSON format
- Sessions expire after 7 days
- Session is restored automatically on app start

## Development

### Code Style
- Type hints used throughout
- Docstrings for all classes and public methods
- Separation of concerns (UI, business logic, data)

### Extending
- Add new pet fields in `database.py` and `ui/dialogs.py`
- Add new views in `ui/views.py`
- Modify sync behavior in `database.py`
