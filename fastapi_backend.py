from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from recommendation_engine import AssessmentRecommender
import os
# Initialize FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for recommending SHL assessments based on job descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 allow everything during local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize recommender (loaded once at startup)
recommender = None

@app.on_event("startup")
async def startup_event():
    """Load the recommendation model on startup"""
    global recommender
    print("Loading recommendation engine...")
    recommender = AssessmentRecommender('shl_assessments.json')
    print("Recommendation engine ready!")

# Request/Response Models
class RecommendRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    time_limit: Optional[int] = None

class Assessment(BaseModel):
    assessment_name: str
    assessment_url: str
    test_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    skills: Optional[List[str]] = None
    relevance_score: Optional[float] = None

class RecommendResponse(BaseModel):
    status: str
    query: str
    recommendations: List[Assessment]
    total_results: int

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {
        "status": "healthy",
        "message": "SHL Assessment Recommendation API is running",
        "version": "1.0.0"
    }

@app.post("/recommend", response_model=RecommendResponse)
async def recommend_assessments(request: RecommendRequest):
    """
    Recommend assessments based on job description or query
    
    Args:
        query: Natural language query or job description text
        max_results: Maximum number of recommendations (1-10, default 10)
        time_limit: Maximum assessment duration in minutes (optional)
    
    Returns:
        List of recommended assessments with metadata
    """
    try:
        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate max_results
        max_results = min(max(request.max_results, 1), 10)
        
        # Get recommendations
        recommendations = recommender.recommend(
            query=request.query,
            top_k=max_results,
            time_limit=request.time_limit
        )
        
        # Format response
        assessments = [
            Assessment(
                assessment_name=rec['name'],
                assessment_url=rec['url'],
                test_type=rec.get('test_type'),
                duration_minutes=rec.get('duration_minutes'),
                skills=rec.get('skills'),
                relevance_score=rec.get('final_score')
            )
            for rec in recommendations
        ]
        
        return RecommendResponse(
            status="success",
            query=request.query,
            recommendations=assessments,
            total_results=len(assessments)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SHL Assessment Recommendation API",
        "endpoints": {
            "health": "/health",
            "recommend": "/recommend (POST)"
        },
        "documentation": "/docs"
    }

# For testing locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use 8000 as fallback for local testing
    uvicorn.run(app, host="0.0.0.0", port=port)