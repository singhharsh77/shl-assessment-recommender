import json
import re
from typing import List, Dict

class SimpleAssessmentRecommender:
    def __init__(self, assessments_file='shl_assessments.json'):
        """Initialize with simple keyword matching"""
        with open(assessments_file, 'r') as f:
            self.assessments = json.load(f)
        print(f"Loaded {len(self.assessments)} assessments")
    
    def recommend(self, query: str, top_k: int = 10, time_limit: int = None) -> List[Dict]:
        """Simple keyword-based recommendation"""
        query_lower = query.lower()
        requirements = self.parse_query(query_lower)
        
        if time_limit is None:
            time_limit = requirements.get('time_limit', 120)
        
        # Score each assessment
        scored = []
        for assessment in self.assessments:
            if assessment['duration_minutes'] > time_limit:
                continue
            
            score = 0
            text = f"{assessment['name']} {assessment['description']} {' '.join(assessment['skills'])}".lower()
            
            # Keyword matching
            for word in query_lower.split():
                if len(word) > 3 and word in text:
                    score += 1
            
            # Boost for matching skills
            for skill in requirements['skills']:
                if skill in assessment['skills']:
                    score += 3
            
            # Boost for test type match
            if requirements['test_types'] and assessment['test_type'] in requirements['test_types']:
                score += 2
            
            if score > 0:
                assessment_copy = assessment.copy()
                assessment_copy['final_score'] = score
                scored.append(assessment_copy)
        
        # Sort by score
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Balance if needed
        if len(requirements['test_types']) > 1:
            scored = self.balance_recommendations(scored, requirements, top_k)
        
        return scored[:top_k]
    
    def parse_query(self, query: str) -> Dict:
        """Extract requirements from query"""
        requirements = {
            'skills': [],
            'test_types': set(),
            'time_limit': 120,
        }
        
        # Extract time limit
        time_patterns = [
            (r'(\d+)\s*minutes?', 1),
            (r'(\d+)\s*mins?', 1),
            (r'(\d+)\s*hours?', 60),
        ]
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, query)
            if match:
                requirements['time_limit'] = int(match.group(1)) * multiplier
                break
        
        # Extract skills
        skill_keywords = ['java', 'python', 'sql', 'javascript', 'excel', 'tableau',
                         'leadership', 'communication', 'sales', 'analytical', 'english',
                         'collaboration', 'teamwork', 'management', 'marketing', 'finance']
        for skill in skill_keywords:
            if skill in query:
                requirements['skills'].append(skill)
        
        # Determine test types
        if any(word in query for word in ['personality', 'behavior', 'cultural']):
            requirements['test_types'].add('P')
        if any(word in query for word in ['cognitive', 'reasoning', 'aptitude']):
            requirements['test_types'].add('C')
        if any(word in query for word in ['technical', 'skill', 'programming', 'knowledge']):
            requirements['test_types'].add('K')
        
        has_technical = any(s in requirements['skills'] for s in ['java', 'python', 'sql', 'javascript'])
        has_soft = any(s in requirements['skills'] for s in ['communication', 'leadership', 'collaboration'])
        
        if has_technical and has_soft:
            requirements['test_types'].update(['K', 'P'])
        elif has_technical:
            requirements['test_types'].add('K')
        elif has_soft:
            requirements['test_types'].add('P')
        
        return requirements
    
    def balance_recommendations(self, candidates: List[Dict], requirements: Dict, top_k: int) -> List[Dict]:
        """Balance different test types"""
        if len(requirements['test_types']) <= 1:
            return candidates
        
        by_type = {}
        for candidate in candidates:
            test_type = candidate['test_type']
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(candidate)
        
        balanced = []
        slots_per_type = top_k // len(requirements['test_types'])
        
        for test_type in requirements['test_types']:
            if test_type in by_type:
                balanced.extend(by_type[test_type][:slots_per_type])
        
        remaining = top_k - len(balanced)
        for candidate in candidates:
            if candidate not in balanced and remaining > 0:
                balanced.append(candidate)
                remaining -= 1
        
        return balanced

# For backwards compatibility
AssessmentRecommender = SimpleAssessmentRecommender