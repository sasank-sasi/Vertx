import os
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import csv
from datetime import datetime
import groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data Models
@dataclass
class Founder:
    name: str
    company_name: str
    industry: str
    stage: str
    pitch: str
    metrics: Dict[str, str]

@dataclass
class Investor:
    name: str
    firm: str
    investment_focus: List[str]
    preferred_stages: List[str]
    email: str

class EmailVariant(Enum):
    BUSINESS = "business"
    PERSONAL = "personal"
    METRICS = "metrics"
    VISION = "vision"
    CUSTOM = "custom"

@dataclass
class EmailTemplate:
    subject: str
    body: str
    variant: EmailVariant

@dataclass
class CustomPrompt:
    instruction: str
    tone: Optional[str] = None
    focus_points: Optional[List[str]] = None
    custom_template: Optional[str] = None

class EmailPipeline:
    def __init__(self):
        # Get credentials from environment variables
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        if not self.groq_api_key:
            raise ValueError("GROQ API key not found in environment variables")
            
        try:
            self.groq_client = groq.Client(api_key=self.groq_api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize GROQ client: {str(e)}")

    def generate_system_prompt(self) -> str:
        return """You are an expert at crafting professional investor emails.
        Remember this is the first time you are sending mails to them
        Always format your response with:
        Subject: [Clear, concise subject line]
        
        Body: [Professional email body]
        
        End every email with:
        Best regards,
        [Founder Name]
        [Company Name]"""

    def generate_custom_context(self, founder: Founder, investor: Investor, 
                              custom_prompt: CustomPrompt) -> str:
        """Generate context for custom prompt"""
        base_context = f"""
        Founder Details:
        - Name: {founder.name}
        - Company: {founder.company_name}
        - Industry: {founder.industry}
        - Stage: {founder.stage}
        - Pitch: {founder.pitch}
        - Metrics: 
          - MRR: {founder.metrics.get('mrr', 'N/A')}
          - Growth: {founder.metrics.get('growth', 'N/A')}
          - Customers: {founder.metrics.get('customers', 'N/A')}
        
        Investor Details:
        - Name: {investor.name}
        - Firm: {investor.firm}
        - Focus Areas: {', '.join(investor.investment_focus)}
        - Stage Preference: {', '.join(investor.preferred_stages)}
        
        Instructions:
        {custom_prompt.instruction}
        """
        
        if custom_prompt.tone:
            base_context += f"\nTone: {custom_prompt.tone}"
            
        if custom_prompt.focus_points:
            base_context += f"\nKey Focus Points:\n" + "\n".join(f"- {point}" for point in custom_prompt.focus_points)
            
        if custom_prompt.custom_template:
            base_context += f"\nTemplate Structure:\n{custom_prompt.custom_template}"
            
        return base_context

    def generate_email_variants(self, founder: Founder, investor: Investor, 
                              custom_prompt: Optional[CustomPrompt] = None) -> List[EmailTemplate]:
        """Generate email variants using GROQ API with optional custom prompt"""
        try:
            base_context = f"""
            Founder Details:
            - Name: {founder.name}
            - Company: {founder.company_name}
            - Industry: {founder.industry}
            - Stage: {founder.stage}
            - Pitch: {founder.pitch}
            - Metrics: 
              - MRR: {founder.metrics.get('mrr', 'N/A')}
              - Growth: {founder.metrics.get('growth', 'N/A')}
              - Customers: {founder.metrics.get('customers', 'N/A')}
            
            Investor Details:
            - Name: {investor.name}
            - Firm: {investor.firm}
            - Focus Areas: {', '.join(investor.investment_focus)}
            - Stage Preference: {', '.join(investor.preferred_stages)}
            """
            
            variants = []
            
            prompts = {
                EmailVariant.BUSINESS: "Generate a direct, business-focused email highlighting metrics and market opportunity.",
                EmailVariant.PERSONAL: "Generate a personal email focusing on founder journey and vision alignment.",
                EmailVariant.METRICS: "Generate a data-driven email emphasizing traction and growth metrics.",
                EmailVariant.VISION: "Generate a visionary email focusing on industry impact and future potential."
            }
            
            # Add custom prompt if provided
            if custom_prompt:
                try:
                    context = self.generate_custom_context(founder, investor, custom_prompt)
                    response = self.groq_client.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[
                            {"role": "system", "content": self.generate_system_prompt()},
                            {"role": "user", "content": context}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    email_content = response.choices[0].message.content
                    subject = email_content.split("Subject:")[1].split("Body:")[0].strip()
                    body = email_content.split("Body:")[1].strip()
                    
                    variants.append(EmailTemplate(
                        subject=subject,
                        body=body,
                        variant=EmailVariant.CUSTOM
                    ))
                except Exception as e:
                    print(f"Error generating custom variant: {str(e)}")
            
            # Generate standard variants
            for variant, instruction in prompts.items():
                try:
                    response = self.groq_client.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[
                            {"role": "system", "content": self.generate_system_prompt()},
                            {"role": "user", "content": f"{base_context}\n\n{instruction}"}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    email_content = response.choices[0].message.content
                    
                    try:
                        subject = email_content.split("Subject:")[1].split("Body:")[0].strip()
                        body = email_content.split("Body:")[1].strip()
                    except IndexError:
                        print(f"Error parsing response for {variant.value} variant. Using default format.")
                        subject = f"{founder.company_name} - Investment Opportunity"
                        body = email_content
                    
                    variants.append(EmailTemplate(subject=subject, body=body, variant=variant))
                    
                except Exception as e:
                    print(f"Error generating {variant.value} variant: {str(e)}")
                    continue
            
            return variants
            
        except Exception as e:
            raise Exception(f"Failed to generate email variants: {str(e)}")

    def verify_email(self, email: EmailTemplate) -> Dict[str, bool]:
        """Verify email content with more flexible criteria"""
        try:
            # Define verification criteria
            verifications = {
                "has_greeting": any(greeting in email.body.lower() 
                                  for greeting in ["dear", "hi", "hello"]),
                "has_signature": any(sign in email.body.lower() 
                                   for sign in ["best regards", "sincerely", "regards"]),
                "proper_length": 100 <= len(email.body) <= 2000,
                "has_call_to_action": any(phrase in email.body.lower() 
                                        for phrase in ["let's connect", "would love to", 
                                                     "looking forward", "please let me know"])
            }
            
            # Print detailed verification results
            print("\nDetailed Verification Results:")
            for criterion, result in verifications.items():
                print(f"- {criterion}: {'✓' if result else '✗'}")
            
            return verifications
            
        except Exception as e:
            print(f"Email verification failed: {str(e)}")
            return {"error": False}

    def send_email(self, email: EmailTemplate, recipient: str) -> bool:
        """Send the email using SMTP"""
        if not self.email_sender or not self.email_password:
            raise ValueError("Email credentials not found in environment variables")
            
        msg = MIMEMultipart()
        msg['From'] = self.email_sender
        msg['To'] = recipient
        msg['Subject'] = email.subject
        
        msg.attach(MIMEText(email.body, 'plain'))
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def log_communication(self, founder: Founder, investor: Investor, 
                         email: EmailTemplate, success: bool) -> None:
        """Log the communication details to CSV and JSON"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "founder_name": founder.name,
                "company_name": founder.company_name,
                "investor_name": investor.name,
                "investor_firm": investor.firm,
                "email_variant": email.variant.value,
                "email_subject": email.subject,
                "success": success
            }
            
            # Ensure log directories exist
            os.makedirs('logs', exist_ok=True)
            
            # JSON logging
            json_path = 'logs/email_logs.json'
            try:
                with open(json_path, 'a') as f:
                    json.dump(log_entry, f)
                    f.write('\n')
            except Exception as e:
                print(f"Failed to write JSON log: {str(e)}")
                
            # CSV logging
            csv_path = 'logs/email_logs.csv'
            try:
                file_exists = os.path.isfile(csv_path)
                with open(csv_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=log_entry.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(log_entry)
            except Exception as e:
                print(f"Failed to write CSV log: {str(e)}")
                
        except Exception as e:
            print(f"Logging failed: {str(e)}")

def main():
    try:
        print("Initializing Email Pipeline...")
        pipeline = EmailPipeline()
        
        # Example data
        founder = Founder(
            name="John Doe",
            company_name="TechStartup Inc.",
            industry="AI/ML",
            stage="Seed",
            pitch="Building next-gen AI infrastructure",
            metrics={
                "mrr": "$50k",
                "growth": "15% MoM",
                "customers": "100+"
            }
        )
        
        investor = Investor(
            name="Jane Smith",
            firm="VC Partners",
            investment_focus=["AI", "SaaS"],
            preferred_stages=["Seed", "Series A"],
            email="jane@vcpartners.com"
        )
        
        print("\nGenerating AI email variants...")
        # First generate standard AI variants
        email_variants = pipeline.generate_email_variants(founder, investor)
        
        # Display AI-generated variants
        print("\nAI-Generated Email Variants:")
        for i, variant in enumerate(email_variants, 1):
            print(f"\n{'='*50}")
            print(f"Variant {i}: {variant.variant.value.upper()}")
            print(f"{'='*50}")
            print(f"Subject: {variant.subject}")
            print(f"\nBody:\n{variant.body}")
            print(f"\n{'='*50}")
        
        # Now ask if user wants to create a custom prompt
        print("\nOptions:")
        print("1-4: Select from AI-generated variants above")
        print("5: Write a custom email")
        print("0: Exit")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (0-5): "))
                if choice == 0:
                    print("Exiting program...")
                    return
                elif choice == 5:
                    # Handle custom email
                    subject = input("\nEnter the email subject: ")
                    body = input("Enter the email body: ")
                    
                    custom_email = EmailTemplate(
                        subject=subject,
                        body=body,
                        variant=EmailVariant.CUSTOM
                    )
                    
                    print("\nCustom Email:")
                    print(f"{'='*50}")
                    print(f"Subject: {custom_email.subject}")
                    print(f"\nBody:\n{custom_email.body}")
                    print(f"{'='*50}")
                    
                    # Ask if user wants to enhance the email using AI
                    enhance = input("\nDo you want to enhance this email using AI? (yes/no): ").lower()
                    if enhance == 'yes':
                        custom_prompt = CustomPrompt(
                            instruction="Enhance the following email:",
                            custom_template=f"Subject: {custom_email.subject}\n\nBody: {custom_email.body}"
                        )
                        
                        print("\nEnhancing custom email...")
                        enhanced_variants = pipeline.generate_email_variants(founder, investor, custom_prompt)
                        
                        if enhanced_variants:
                            selected_email = enhanced_variants[0]  # Get the enhanced variant
                        else:
                            print("Failed to enhance the email. Using the original custom email.")
                            selected_email = custom_email
                    else:
                        selected_email = custom_email
                    break
                        
                elif 1 <= choice <= len(email_variants):
                    selected_email = email_variants[choice-1]
                    break
                else:
                    print(f"Please enter a number between 0 and {max(5, len(email_variants))}")
            except ValueError:
                print("Please enter a valid number")
        
        # Display selected or custom email for confirmation
        print("\nSelected Email:")
        print(f"{'='*50}")
        print(f"Variant: {selected_email.variant.value.upper()}")
        print(f"Subject: {selected_email.subject}")
        print(f"\nBody:\n{selected_email.body}")
        print(f"{'='*50}")
        
        # Verify selected email
        verification_results = pipeline.verify_email(selected_email)
        
        if all(verification_results.values()):
            print("\nEmail passed all verification checks!")
            
            # Confirm sending
            if input("\nSend this email? (yes/no): ").lower() == 'yes':
                print("\nSending email...")
                success = pipeline.send_email(selected_email, investor.email)
                
                # Log the communication
                pipeline.log_communication(founder, investor, selected_email, success)
                
                if success:
                    print("Email sent successfully!")
                else:
                    print("Failed to send email.")
            else:
                print("Email sending cancelled.")
        else:
            print("\nEmail failed some verification checks. Please review the results above.")
            
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()
