import pandas as pd
from recommendation_engine import AssessmentRecommender
import csv

# Test queries from your unlabeled test set
TEST_QUERIES = [
    "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script. Need an assessment package that can test all skills with max duration of 60 minutes.",
    
    """Job Description - Join a community that is shaping the future of work! SHL, People Science. People Answers.
    Are you an AI enthusiast with visionary thinking to conceptualize AI-based products? We are seeking a Research Engineer to join our team to deliver robust AI/ML models.
    Requirements: Relevant experience in AI/ML - NLP, speech processing, and computer vision. Proficiency in Python and ML frameworks such as TensorFlow, PyTorch, & OpenAI APIs.""",
    
    "Can you recommend some assessment that can help me screen applications. Time limit is less than 30 minutes",
    
    "I am hiring for an analyst and wants applications to screen using Cognitive and personality tests, what options are available within 45 mins.",
    
    """I have a JD for Presales Specialist role. The Presales Specialist is responsible for creating, curating, and presenting compelling content to support the Solution Architects and Sales team.
    Key responsibilities include: Building custom demos, Responding to RFPs, Content creation and customization, Customer engagement.
    Required: 2-4 years experience in Presales, strong writing and presentation skills, experience with design tools.
    I want them to give a test which is at least 30 mins long""",
    
    "I am new looking for new graduates in my sales team, suggest an 30 min long assessment",
    
    """For Marketing - Content Writer Position at ShopClues.
    The Typical Creative Process Involves: Discussing campaigns, Brainstorming visual and copy ideas, Generating Stories for Brands core blog,
    Experience in publishing Push Notification and unique Product Description.""",
    
    "I want to hire a product manager with 3-4 years of work experience and expertise in SDLC, Jira and Confluence",
    
    """Suggest me an assessment for Finance & Operations Analyst role.
    The Finance & Operations Analyst will provide insights, analysis, and guidance to commercial teams.
    Requirements: Experience in finance/accounting, 1-2 years in financial/analytical role, Strong analytical skills,
    Knowledge of financial modeling, Excel, and accounting systems.""",
    
    """I want to hire Customer support executives who are expert in English communication.
    Requirements: Fluent in English with 2-3 years in International Call Center (US/UK Voice Process),
    Strong communication skills, ability to handle calls/emails/chats, customer service oriented."""
]

def generate_predictions(output_file='test_predictions.csv'):
    """Generate predictions for test queries and save to CSV"""
    
    print("Initializing recommender...")
    recommender = AssessmentRecommender('shl_assessments.json')
    
    results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\nProcessing query {i}/{len(TEST_QUERIES)}...")
        print(f"Query: {query[:100]}...")
        
        try:
            # Get recommendations
            recommendations = recommender.recommend(query, top_k=10)
            
            print(f"Found {len(recommendations)} recommendations")
            
            # Add to results
            for rec in recommendations:
                results.append({
                    'Query': query,
                    'Assessment_url': rec['url']
                })
                
        except Exception as e:
            print(f"Error processing query {i}: {e}")
    
    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved predictions to {output_file}")
    print(f"Total rows: {len(results)}")
    
    # Display summary
    print("\nSummary:")
    for query_num, query in enumerate(TEST_QUERIES, 1):
        query_results = df[df['Query'] == query]
        print(f"Query {query_num}: {len(query_results)} recommendations")
    
    return df

def validate_csv_format(csv_file='test_predictions.csv'):
    """Validate the CSV format matches requirements"""
    print(f"\nValidating {csv_file}...")
    
    df = pd.read_csv(csv_file)
    
    # Check columns
    required_columns = ['Query', 'Assessment_url']
    if list(df.columns) != required_columns:
        print(f"❌ ERROR: Columns should be {required_columns}, got {list(df.columns)}")
        return False
    
    # Check for missing values
    if df.isnull().any().any():
        print("❌ ERROR: CSV contains missing values")
        return False
    
    # Check URL format
    invalid_urls = df[~df['Assessment_url'].str.startswith('https://www.shl.com')]
    if len(invalid_urls) > 0:
        print(f"⚠️  WARNING: Found {len(invalid_urls)} URLs not from SHL catalog")
    
    print("✅ CSV format is valid!")
    print(f"Total rows: {len(df)}")
    print(f"Unique queries: {df['Query'].nunique()}")
    
    return True

if __name__ == "__main__":
    # Generate predictions
    df = generate_predictions('test_predictions.csv')
    
    # Validate format
    validate_csv_format('test_predictions.csv')
    
    # Show first few rows
    print("\nFirst 10 rows:")
    print(df.head(10))