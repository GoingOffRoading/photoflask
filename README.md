# photoflask

A web-based photo slideshow application with database management and sharing capabilities.

## Getting Started

### Local Development

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install Flask==3.0.0 Werkzeug==3.0.1
   ```
3. Run the app:
   ```bash
   cd src
   python app.py
   ```
4. Open http://127.0.0.1:5000 in your browser

### Docker

Build the image:
```bash
docker build -t photoflask .
```

Run the container:
```bash
docker run -p 5000:5000 photoflask
```

The app will be available at http://localhost:5000

To mount a local photos directory:
```bash
docker run -p 5000:5000 -v /path/to/photos:/data photoflask
```

To persist the database across runs:
```bash
docker run -p 5000:5000 -v photoflask-db:/app/src photoflask
```