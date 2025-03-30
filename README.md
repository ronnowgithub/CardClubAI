# User Statistics App

A simple Flask application that tracks user statistics (wins and losses) with a basic login system.

## Features

- Simple username-based login (no password required)
- Display of user statistics in a table format
- SQLite database for data storage
- Responsive design

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Deployment on Render.com

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Configure the service with the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Python Version: 3.8 or higher

The application will be automatically deployed and you'll get a URL where it's accessible.

## Database

The application uses SQLite for data storage. The database file (`users.db`) will be created automatically when you first run the application.

## Security Note

This is a basic implementation for demonstration purposes. It uses a simple username-based login system without password protection. For production use, you should implement proper authentication and security measures. 