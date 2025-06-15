# Postcard Lister

A Python application for processing and listing postcards on eBay.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/postcard-lister.git
cd postcard-lister
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the settings template and configure your settings:
```bash
cp config/settings.template.json config/settings.json
```
Edit `config/settings.json` with your:
- AWS credentials
- OpenAI API key
- Default price
- Branding image path
- Other settings

## Usage

Run the application:
```bash
python app.py
```

## Features

- Process postcard images (front and back)
- Upload images to AWS S3
- Generate eBay-compatible CSV listings
- AI-powered metadata extraction
- Custom HTML description templates
- Configurable default price
- Custom branding image support

## Requirements

- Python 3.8+
- AWS S3 account
- OpenAI API key
- Required Python packages (see requirements.txt)

[Your chosen license] 