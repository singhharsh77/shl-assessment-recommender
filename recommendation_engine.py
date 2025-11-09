import json
import numpy as np
import faiss
from typing import List, Dict
import re

# Handle sentence-transformers import with auto-fix
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Error importing sentence_transformers: {e}")
    print("Attempting to fix by upgrading packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', '--upgrade', 'sentence-transformers>=3.0.0', 'huggingface-hub>=0.20.0'])
    from sentence_transformers import SentenceTransformer

class AssessmentRecommender:
    def __init__(self, assessments_file='shl_assessments.json'):
        """Initialize the recommendation system"""
        # Load assessments
        with open(assessments_file, 'r') as f:
            self.assessments = json.load(f)
        
        # Load embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create embeddings for all assessments
        print("Creating embeddings for assessments...")
        self.assessment_texts = [
            f"{a['name']} {a['description']} {' '.join(a['skills'])}"
            for a in self.assessments
        ]
        self.embeddings = self.model.encode(self.assessment_texts)
        
        # Create FAISS index
        self.dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
        
        print(f"Indexed {len(self.assessments)} assessments")
    
    def recommend(self, query: str, top_k: int = 10, 
                  time_limit: int = None) -> List[Dict]:
        """
        Recommend assessments based on query
        
        Args:
            query: Natural language query or job description
            top_k: Number of recommendations to return (5-10)
            time_limit: Maximum duration in minutes (optional)
        
        Returns:
            List of recommended assessments with scores
        """
        # Parse query for requirements
        requirements = self.parse_query(query)
        
        # Get time limit from query if not provided
        if time_limit is None:
            time_limit = requirements.get('time_limit', 120)
        
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search for similar assessments (get more than needed for filtering)
        k = min(50, len(self.assessments))
        scores, indices = self.index.search(query_embedding, k)
        
        # Filter and rank results
        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            assessment = self.assessments[idx].copy()
            assessment['similarity_score'] = float(score)
            
            # Filter by time limit
            if assessment['duration_minutes'] <= time_limit:
                # Boost score based on requirements match
                boost = self.calculate_boost(assessment, requirements)
                assessment['final_score'] = float(score) * boost
                candidates.append(assessment)
        
        # Sort by final score
        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Ensure balanced recommendations
        balanced_results = self.balance_recommendations(
            candidates, requirements, top_k
        )
        
        return balanced_results[:top_k]
    
    def parse_query(self, query: str) -> Dict:
        """Extract requirements from query"""
        query_lower = query.lower()
        requirements = {
            'skills': [],
            'test_types': set(),
            'time_limit': 120,
            'experience_level': 'mid'
        }
        
        # Extract time limit
        time_patterns = [
            (r'(\d+)\s*minutes?', 1),
            (r'(\d+)\s*mins?', 1),
            (r'(\d+)\s*hours?', 60),
            (r'less than (\d+)', 1)
        ]
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                requirements['time_limit'] = int(match.group(1)) * multiplier
                break
        
        # Extract experience level
        if any(word in query_lower for word in ['entry', 'graduate', 'junior', 'new']):
            requirements['experience_level'] = 'entry'
        elif any(word in query_lower for word in ['senior', 'lead', 'principal']):
            requirements['experience_level'] = 'senior'
        
        # Extract skills
        skill_keywords = {
            'java', 'python', 'sql', 'javascript', 'excel', 'tableau',
            'leadership', 'communication', 'sales', 'analytical', 'english',
            'collaboration', 'teamwork', 'management', 'marketing', 'finance'
        }
        for skill in skill_keywords:
            if skill in query_lower:
                requirements['skills'].append(skill)
        
        # Determine test types needed
        if any(word in query_lower for word in ['personality', 'behavior', 'cultural fit']):
            requirements['test_types'].add('P')
        if any(word in query_lower for word in ['cognitive', 'reasoning', 'aptitude']):
            requirements['test_types'].add('C')
        if any(word in query_lower for word in ['technical', 'skill', 'programming', 'knowledge']):
            requirements['test_types'].add('K')
        
        # If multiple skill types mentioned, need balanced recommendations
        has_technical = any(s in requirements['skills'] for s in ['java', 'python', 'sql', 'javascript'])
        has_soft = any(s in requirements['skills'] for s in ['communication', 'leadership', 'collaboration'])
        
        if has_technical and has_soft:
            requirements['test_types'].update(['K', 'P'])
        elif has_technical:
            requirements['test_types'].add('K')
        elif has_soft:
            requirements['test_types'].add('P')
        
        return requirements
    
    def calculate_boost(self, assessment: Dict, requirements: Dict) -> float:
        """Calculate boost factor based on requirements match"""
        boost = 1.0
        
        # Boost for matching skills
        if requirements['skills']:
            matched_skills = set(assessment['skills']) & set(requirements['skills'])
            if matched_skills:
                boost *= (1.0 + 0.2 * len(matched_skills))
        
        # Boost for matching test type
        if requirements['test_types'] and assessment['test_type'] in requirements['test_types']:
            boost *= 1.3
        
        return boost
    
    def balance_recommendations(self, candidates: List[Dict], 
                               requirements: Dict, top_k: int) -> List[Dict]:
        """
        Ensure balanced mix of assessment types if query requires it
        """
        # If multiple test types required, ensure balance
        if len(requirements['test_types']) > 1:
            balanced = []
            by_type = {}
            
            # Group by test type
            for candidate in candidates:
                test_type = candidate['test_type']
                if test_type not in by_type:
                    by_type[test_type] = []
                by_type[test_type].append(candidate)
            
            # Distribute slots among types
            slots_per_type = top_k // len(requirements['test_types'])
            
            for test_type in requirements['test_types']:
                if test_type in by_type:
                    balanced.extend(by_type[test_type][:slots_per_type])
            
            # Fill remaining slots with top candidates
            remaining = top_k - len(balanced)
            if remaining > 0:
                for candidate in candidates:
                    if candidate not in balanced:
                        balanced.append(candidate)
                        if len(balanced) >= top_k:
                            break
            
            return balanced
        
        return candidates
    
    def format_response(self, recommendations: List[Dict]) -> Dict:
        """Format recommendations for API response"""
        return {
            'recommendations': [
                {
                    'assessment_name': r['name'],
                    'assessment_url': r['url'],
                    'test_type': r['test_type'],
                    'duration_minutes': r['duration_minutes'],
                    'skills': r['skills'],
                    'relevance_score': round(r['final_score'], 3)
                }
                for r in recommendations
            ],
            'total_results': len(recommendations)
        }

# Usage
if __name__ == "__main__":
    # Test the recommender
    recommender = AssessmentRecommender()
    
    # Test query
    query = "I am hiring for Java developers who can also collaborate effectively with my business teams."
    results = recommender.recommend(query, top_k=10)
    
    print("\nRecommendations:")
    for i, rec in enumerate(results, 1):
        print(f"{i}. {rec['name']}")
        print(f"   URL: {rec['url']}")
        print(f"   Score: {rec['final_score']:.3f}")
        print()