import pandas as pd
import numpy as np

# Create expanded founders data
founders_data = {
    'company_name': [
        'EcoHarvest Technologies', 'HealthBridge', 'PayFlow',
        'CyberShield AI', 'EduTech Plus', 'CleanEnergy Solutions',
        'LogisticsPro', 'RetailAI', 'BioTech Innovations', 'SmartCity Solutions'
    ],
    'industry': [
        'AgriTech', 'HealthTech', 'FinTech',
        'Cybersecurity', 'EdTech', 'CleanTech',
        'Logistics', 'Retail', 'BioTech', 'Smart Cities'
    ],
    'verticals': [
        'Sustainable Agriculture, IoT, AI',
        'Telemedicine, AI Diagnostics, Healthcare',
        'Digital Payments, Financial Inclusion, Mobile Money',
        'AI Security, Blockchain, Cloud Security',
        'Online Learning, AI Tutoring, EdTech',
        'Renewable Energy, Smart Grid, Sustainability',
        'Supply Chain, IoT, Analytics',
        'E-commerce, AI, Customer Analytics',
        'Drug Discovery, AI, Healthcare',
        'Urban Planning, IoT, Sustainability'
    ],
    'stage': [
        'Seed', 'Series A', 'Pre-Series A',
        'Seed', 'Series A', 'Pre-Series A',
        'Seed', 'Pre-Seed', 'Series A', 'Seed'
    ],
    'country': [
        'Kenya', 'Nigeria', 'South Africa',
        'Egypt', 'Morocco', 'Ghana',
        'Tunisia', 'Rwanda', 'Uganda', 'Tanzania'
    ],
    'business_model': [
        'B2B SaaS', 'B2B2C', 'B2C',
        'B2B', 'B2C', 'B2B2C',
        'B2B', 'B2C', 'B2B', 'B2G'
    ],
    'description': [
        'Smart farming solution using IoT sensors and AI for crop management',
        'AI-powered telemedicine platform connecting rural patients with urban doctors',
        'Mobile-first digital payment and remittance platform',
        'AI-powered cybersecurity platform for enterprise threat detection',
        'Personalized learning platform using AI for student engagement',
        'Renewable energy management platform for sustainable power',
        'AI-powered logistics optimization platform',
        'Retail analytics and automation platform',
        'AI-driven drug discovery platform',
        'Smart city management and optimization platform'
    ],
    'monthly_revenue': [
        45000, 180000, 250000,
        120000, 200000, 150000,
        80000, 30000, 300000, 175000
    ],
    'growth_rate': [
        '28%', '35%', '42%',
        '30%', '38%', '25%',
        '32%', '40%', '35%', '28%'
    ],
    'funding_amount_sought': [
        2000000, 5000000, 3500000,
        2500000, 4000000, 3000000,
        1500000, 1000000, 6000000, 2800000
    ],
    'equity_offered': [
        '15%', '20%', '18%',
        '16%', '22%', '17%',
        '14%', '12%', '25%', '16%'
    ],
    'previous_funding': [
        500000, 1200000, 800000,
        600000, 1500000, 900000,
        400000, 200000, 2000000, 700000
    ]
}

# Convert to DataFrame
df = pd.DataFrame(founders_data)

# Save to CSV
output_path = '/Users/sasanksasi/Downloads/project/VertexAi/F2F/expanded_founders_data.csv'
df.to_csv(output_path, index=False)

print(f"Expanded founders data saved to: {output_path}")
print("\nFirst few rows of the data:")
print(df.head())