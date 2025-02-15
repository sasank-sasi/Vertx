import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
from groq import Groq
import time
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import csv

# Load environment variables and initialize Groq
load_dotenv()
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class InvestorMatcher:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,            # Changed from default
            max_df=1.0           # Changed from 0.9
        )
    
    def calculate_similarities(self, founder_desc, investors_df):
        # Ensure text fields are strings
        investors_df['description'] = investors_df['description'].fillna('')
        investors_df['industries'] = investors_df['industries'].fillna('')
        
        # Combine descriptions and industries
        investors_df['combined_text'] = investors_df['description'].astype(str) + ' ' + investors_df['industries'].astype(str)
        documents = investors_df['combined_text'].tolist()
        documents.append(founder_desc)
        
        # Calculate TF-IDF similarities
        try:
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            return similarities
        except ValueError as e:
            print(f"Error in similarity calculation: {e}")
            return np.zeros(len(investors_df))
    
    def analyze_with_groq(self, founder_data, investor, similarity_score):
        prompt = f"""
        As an investment matching expert, analyze the compatibility between:
    
        Founder:
        Description: {founder_data['description']}
        Industry: {founder_data['industry']}
    
        Investor:
        Company: {investor['company_name']}
        Type: {investor['investor_type']}
        Description: {investor['description']}
        Industries: {investor['industries']}
        Location: {investor['location']}
        Initial Similarity Score: {similarity_score:.2f}
    
        Provide:
        1. A score from 0 to 100 based on:
           - Industry alignment
           - Investment stage fit
           - Technology focus
           - Geographic compatibility
        2. A brief explanation
    
        Response format must be exactly:
        <numerical_score>|<brief_explanation>
        Example: 85|Strong industry alignment and technology focus match
        """
    
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                model="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=150
            )
            response = completion.choices[0].message.content.strip()
            
            # Handle different response formats
            if '|' not in response:
                # Extract first number found in response
                import re
                numbers = re.findall(r'\d+', response)
                if numbers:
                    score = min(float(numbers[0]), 100)
                    explanation = response
                else:
                    score = 0
                    explanation = response
            else:
                parts = response.split('|', 1)
                score = float(parts[0].strip())
                explanation = parts[1].strip()
            
            return min(max(score, 0), 100), explanation
    
        except Exception as e:
            print(f"Error analyzing {investor['company_name']}: {str(e)}")
            return 0, f"Analysis failed: {str(e)}"
    
    def process_investors(self, investors_df, founder_data, batch_size=5, save_csv=False):
        """
        Process investors to find matches for a founder.
        Args:
            investors_df (pd.DataFrame): Investors dataset
            founder_data (dict): Founder information
            batch_size (int): Number of investors to process in each batch
            save_csv (bool): Optional flag to save results to CSV
        Returns:
            pd.DataFrame: Matches with scores and explanations
        """
        # Initial filtering
        filtered_df = investors_df[
            investors_df['industries'].str.contains(founder_data['industry'], case=False, na=False)
        ].copy()
        
        # Calculate similarity scores
        similarities = self.calculate_similarities(founder_data['description'], filtered_df)
        filtered_df['similarity_score'] = similarities
        
        results = []
        # Process in batches
        for i in range(0, len(filtered_df), batch_size):
            batch = filtered_df.iloc[i:i+batch_size]
            
            for _, investor in batch.iterrows():
                groq_score, explanation = self.analyze_with_groq(
                    founder_data,
                    investor,
                    investor['similarity_score']
                )
                
                results.append({
                    'company_name': investor['company_name'],
                    'investor_type': investor['investor_type'],
                    'location': investor['location'],
                    'industries': investor['industries'],
                    'similarity_score': investor['similarity_score'],
                    'groq_score': groq_score,
                    'explanation': explanation
                })
            
            time.sleep(2)  # Rate limiting
        
        results_df = pd.DataFrame(results)
        
        # Optionally save to CSV
        if save_csv and not results_df.empty:
            output_file = f"investor_matches_for_{founder_data['company_name'].lower().replace(' ', '_')}.csv"
            results_df.to_csv(output_file, 
                             index=False,
                             quoting=csv.QUOTE_ALL,
                             encoding='utf-8')
            print(f"Results saved to {output_file}")
        
        return results_df

