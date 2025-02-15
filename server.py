from fastapi import FastAPI, HTTPException
import pandas as pd
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional
import logging
from F2F.pipelineF2F import FounderMatcher
from F2I.pipelineF2I import InvestorMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize FastAPI app
app = FastAPI(title="Founder Matching API")

# Initialize matchers
founder_matcher = FounderMatcher(groq_client)
investor_matcher = InvestorMatcher(groq_client)

class FounderInput(BaseModel):
    company_name: str
    industry: str
    verticals: str
    description: str

class MatchResponse(BaseModel):
    matched_company: str
    match_score: float
    industry: str
    verticals: Optional[str]
    explanation: str

class InvestorMatchResponse(BaseModel):
    company_name: str
    investor_type: str
    location: str
    industries: str
    similarity_score: float
    groq_score: float
    explanation: str

@app.post("/match/founder-to-founder", response_model=List[MatchResponse])
async def match_founders(founder: FounderInput):
    try:
        logger.info(f"Processing founder matching request for company: {founder.company_name}")
        
        # Verify founders dataset exists
        founders_path = os.path.join(os.path.dirname(__file__), 'F2F/expanded_founders_data.csv')
        if not os.path.exists(founders_path):
            logger.error(f"Founders dataset not found at: {founders_path}")
            raise HTTPException(
                status_code=500, 
                detail="Founders dataset not found"
            )
            
        # Load founders dataset
        founders_df = pd.read_csv(founders_path)
        logger.info(f"Loaded {len(founders_df)} founders from dataset")
            
        # Process founder matching
        matches = founder_matcher.process_founder({
            "company_name": founder.company_name,
            "industry": founder.industry,
            "verticals": founder.verticals,
            "description": founder.description
        })
        
        if matches is None or matches.empty:
            logger.warning(f"No matches found for company: {founder.company_name}")
            raise HTTPException(status_code=404, detail="No matches found")
        
        # Format matches to match response model
        formatted_matches = []
        for _, match in matches.iterrows():
            formatted_matches.append(MatchResponse(
                matched_company=str(match["Matched Company"]),
                match_score=float(match["Match Score"]),
                industry=str(match["Industry"]),
                verticals=str(match["Verticals"]),
                explanation=str(match["Explanation"])
            ))
        
        logger.info(f"Found {len(formatted_matches)} matches for company: {founder.company_name}")
        return formatted_matches
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match/founder-to-investor", response_model=List[InvestorMatchResponse])
async def match_investors(founder: FounderInput):
    try:
        logger.info(f"Processing investor matching request for company: {founder.company_name}")
        
        # Verify investors dataset exists
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct path to the data file
        investors_path = os.path.join(current_dir, 'F2I', 'dataset.csv')
        if not os.path.exists(investors_path):
            logger.error(f"Investors dataset not found at: {investors_path}")
            raise HTTPException(
                status_code=500, 
                detail="Investors dataset not found"
            )
        
        investors_df = pd.read_csv(investors_path)
        logger.info(f"Loaded {len(investors_df)} investors from dataset")
        
        matches = investor_matcher.process_investors(
            investors_df=investors_df,
            founder_data=founder.model_dump(),  # Using model_dump instead of dict
            batch_size=5
        )
        
        if matches is None or matches.empty:
            logger.warning(f"No investor matches found for company: {founder.company_name}")
            raise HTTPException(status_code=404, detail="No matches found")
        
        # Format matches to match response model
        formatted_matches = []
        for _, match in matches.iterrows():
            formatted_matches.append(InvestorMatchResponse(
                company_name=str(match["company_name"]),
                investor_type=str(match["investor_type"]),
                location=str(match["location"]),
                industries=str(match["industries"]),
                similarity_score=float(match["similarity_score"]),
                groq_score=float(match["groq_score"]),
                explanation=str(match["explanation"])
            ))
        
        logger.info(f"Found {len(formatted_matches)} investor matches for company: {founder.company_name}")
        return formatted_matches
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Welcome to the Founder Matching API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
