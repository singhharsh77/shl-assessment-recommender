# shl-assessment-recommender
# SHL Assessment Recommendation System

An intelligent AI-powered system that recommends relevant SHL assessments based on job descriptions and natural language queries.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Scrape SHL Catalog
```bash
python shl_scraper.py
```
This will create `shl_assessments.json` with all assessment data (~10-15 minutes).

### 3. Run API Server
```bash
python fastapi_backend.py
```
API available at `http://localhost:8000`

### 4. Test Frontend
Open `index.html` in your browser to use the web interface.
Open server at `http://127.0.0.1:5500` or use LiveServer(in VsCode)

### 5. Generate Test Predictions
```bash
python generate_predictions.py
```
Creates `test_predictions.csv` for submission.

## 📋 Project Structure
```
shl-assessment-recommender/
├── shl_scraper.py              # Web scraper for SHL catalog
├── recommendation_engine.py     # Core recommendation logic
├── fastapi_backend.py          # REST API server
├── index.html                  # Web frontend
├── generate_predictions.py     # Generate test predictions
├── requirements.txt            # Python dependencies
├── APPROACH.md                 # Technical approach document
└── README.md                   # This file
```

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### Get Recommendations
```
POST /recommend
Content-Type: application/json

{
  "query": "I am hiring for Java developers who can collaborate",
  "max_results": 10,
  "time_limit": 60
}
```

## 🌐 Deployment

### Deploy API (Railway)
1. Connect GitHub repo to Railway
2. Railway auto-deploys
3. Copy public URL

### Deploy Frontend (Netlify)
1. Drag & drop `index.html` to Netlify Drop
2. Update API URL in HTML

## 📊 Performance

- **Mean Recall@10**: ~88%
- **Response Time**: <200ms average
- **Balanced Recommendations**: ✅ Handles multi-domain queries

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.9+
- **ML**: Sentence Transformers, FAISS
- **Scraping**: BeautifulSoup4, Requests
- **Frontend**: HTML, CSS, JavaScript

## 📧 Contact

Built for SHL AI Intern Assessment 2025 Nov

## 📄 License

MIT License