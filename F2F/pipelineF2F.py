import pandas as pd
import os
from dotenv import load_dotenv
from groq import Groq
import time
from tqdm import tqdm
import csv

# Load environment variables
load_dotenv()
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class FounderMatcher:
    def __init__(self, groq_client):
        self.groq_client = groq_client

    def prefilter_founders(self, new_founder, founders_df):
        """Pre-filter founders based on simple word matching in industry and verticals."""
        
        filtered_founders = []
        
        # Convert new founder's data to lowercase word sets
        new_industry_words = set(new_founder['industry'].lower().split())
        new_vertical_words = set(word.strip().lower() 
                               for word in new_founder['verticals'].split(',')
                               for word in word.split())
        
        for _, founder in founders_df.iterrows():
            # Convert existing founder's data to lowercase word sets
            existing_industry_words = set(founder['industry'].lower().split())
            existing_vertical_words = set(word.strip().lower() 
                                        for word in founder['verticals'].split(',')
                                        for word in word.split())
            
            # Check for any word matches
            industry_match = bool(new_industry_words & existing_industry_words)
            vertical_match = bool(new_vertical_words & existing_vertical_words)
            
            # If either industry or verticals have matching words
            if industry_match or vertical_match:
                match_score = (1 if industry_match else 0) + (1 if vertical_match else 0)
                filtered_founders.append({
                    'founder': founder,
                    'match_score': match_score
                })
        
        # Sort by match score and convert to DataFrame
        filtered_founders.sort(key=lambda x: x['match_score'], reverse=True)
        return pd.DataFrame([f['founder'] for f in filtered_founders])

    def find_matches(self, new_founder, founders_df, min_score=50):
        """Find matching founders based on similarity analysis."""
        # First apply pre-filtering
        filtered_df = self.prefilter_founders(new_founder, founders_df)
        
        if filtered_df.empty:
            print("No preliminary matches found based on industry and verticals")
            return pd.DataFrame()
        
        matches = []
        print(f"Analyzing {len(filtered_df)} potential matches...")
        
        for _, existing_founder in tqdm(filtered_df.iterrows(), total=len(filtered_df)):
            score, explanation = self.analyze_founder_match(new_founder, existing_founder)
            
            if score >= min_score:
                matches.append({
                    'matched_company': existing_founder['company_name'],
                    'match_score': score,
                    'industry': existing_founder['industry'],
                    'verticals': existing_founder['verticals'],
                    'explanation': explanation
                })
            
            time.sleep(1)  # Rate limiting
        
        return pd.DataFrame(matches) if matches else pd.DataFrame()

    def analyze_founder_match(self, new_founder, existing_founder):
        """Analyze synergy between two founders using Groq."""
        prompt = f"""
        Analyze the potential match between these founders:
    
        New Founder:
        Industry: {new_founder['industry']}
        Verticals: {new_founder['verticals']}
        Description: {new_founder['description']}
    
        Existing Founder:
        Company: {existing_founder['company_name']}
        Industry: {existing_founder['industry']}
        Verticals: {existing_founder['verticals']}
        Description: {existing_founder['description']}
    
        Provide score and explanation in exactly this format:
        <score>|<brief_explanation>
    
        Example:
        85|Strong match due to overlapping healthcare focus and complementary AI technologies in diagnostic solutions.
    
        Score should be 0-100. Keep explanation under 25 words.
        """
    
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=100
            )
            response = completion.choices[0].message.content.strip()
            
            if '|' in response:
                score, explanation = response.split('|', 1)
                return float(score), explanation.strip()
            
            return 0, "Could not parse response"
                
        except Exception as e:
            print(f"Error analyzing match: {str(e)}")
            return 0, "Analysis failed"
    
    def process_founder(self, new_founder_data, save_csv=False):
        """
        Process a single founder and find matches.
        Args:
            new_founder_data (dict): Founder data containing company, industry, verticals info
            save_csv (bool): Optional flag to save results to CSV
        Returns:
            pd.DataFrame: Matches sorted by score
        """
        try:
            # Load founders dataset
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Construct path to the data file
            founders_path = os.path.join(current_dir, 'F2F', 'expanded_founders_data.csv')

            # Read the CSV file
            founders_df = pd.read_csv(founders_path)
            
            # Find matches
            matches = self.find_matches(new_founder_data, founders_df)
            
            if matches.empty:
                print(f"No matching founders found for {new_founder_data['company_name']}")
                return None
            
            # Format matches
            matches_formatted = pd.DataFrame({
                'Matched Company': matches['matched_company'],
                'Match Score': matches['match_score'],
                'Industry': matches['industry'],
                'Verticals': matches['verticals'],
                'Explanation': matches['explanation']
            })
            
            # Sort results
            matches_formatted = matches_formatted.sort_values('Match Score', ascending=False)
            
            # Optionally save to CSV
            if save_csv:
                output_file = f"matches_for_{new_founder_data['company_name'].lower().replace(' ', '_')}.csv"
                matches_formatted.to_csv(output_file, 
                                       index=False,
                                       quoting=csv.QUOTE_ALL,
                                       encoding='utf-8')
                print(f"Results saved to {output_file}")
            
            return matches_formatted
            
        except Exception as e:
            print(f"Error processing founder {new_founder_data['company_name']}: {str(e)}")
            return None
