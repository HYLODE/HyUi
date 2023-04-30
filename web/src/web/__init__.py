from pathlib import Path

FONTS_GOOGLE = "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
FONTS_FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
with Path(__file__).parent / "index.html" as f:
    INDEX_STRING = f.open().read()

# URLS to prepopulate redis cache
campus_url = "http://api:8000/baserow/campus?campuses=uclh"
