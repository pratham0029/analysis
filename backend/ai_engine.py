import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_semantic_artifact(enriched_metadata):
    prompt = f"""
    You are an expert Database Architect. Look at these tables, their column definitions, and 5 sample rows of data:
    {json.dumps(enriched_metadata, default=str)}
    
    1. Identify which columns are likely Primary Keys.
    2. Identify which columns link the tables together (Foreign Keys), even if the names are slightly different.
    3. Identify likely metrics (numeric/financial columns like revenue, cost, quantity).
    4. Identify likely dimensions (categorical, date, or descriptive columns like region, status, dates).
    5. Write a highly detailed, professional paragraph explaining the business context of these tables based on the data provided.
    
    Output a strict JSON dictionary mapping these exact relationships. Use this exact schema:
    {{
      "description": "Detailed explanation of what this data represents based on the sample rows...",
      "relationships": [
        {{"table_1": "table_name", "col_1": "column_name", "table_2": "other_table", "col_2": "other_column"}}
      ],
      "metrics": ["TOTAL_REVENUE", "QUANTITY_SOLD"],
      "dimensions": ["REGION", "ORDER_DATE"]
    }}
    """
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)


def generate_business_insight(user_query, data_results):
    prompt = f"""User asked: "{user_query}"\nData returned: {json.dumps(data_results)}\nWrite an explicit executive 2-sentence analytics summary."""
    return model.generate_content(prompt).text.strip()