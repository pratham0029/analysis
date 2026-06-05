import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.1-pro-preview')

def generate_semantic_artifact(enriched_metadata):
    prompt = f"""
    You are an elite Enterprise Database Architect and Data Modeler. Your objective is to deeply analyze the provided database schema, column comments, and diverse sample data:
    {json.dumps(enriched_metadata, default=str)}
    
    You must extract a comprehensive, bulletproof "Semantic Blueprint". The downstream SQL generation AI will rely entirely on this blueprint to write perfect, idempotent queries.

    Deeply analyze and extract the following dimensions:
    1. EXECUTIVE SUMMARY: A high-level business overview of what this dataset represents.
    2. TABLE GRAIN (CRITICAL): What does a single, individual row represent in each fact table? (e.g., "1 row = 1 SKU sold at 1 Store on 1 Date"). This prevents double-counting and fan-out joins.
    3. DATE/TIME CONTEXT: How are dates formatted? Are there default "active" dates (like 9999-12-31)? Which column is the primary anchor for time-series analysis?
    4. GEOGRAPHIC CONTEXT: What geographic boundaries exist? How are regions formatted (e.g., abbreviations vs. full names)?
    5. CATEGORICAL HIERARCHY: What is the exact product or business hierarchy? (e.g., Category -> Subcategory -> Manufacturer -> Brand -> Variant).
    6. BUSINESS METHODOLOGY & METRICS: Are metrics gross or net? What are the currencies/units? Identify pre-calculated ratios (like Share of Market) and explicitly state they CANNOT be summed.
    7. DATA QUALITY & ANOMALIES: How are NULLs represented? Are there placeholder values (e.g., -1, 'UNKNOWN')?
    8. SQL GENERATION STRICT RULES: Based on the data, write 2-3 absolute rules for the downstream SQL AI. (e.g., "Always filter where SALES > 0", "Brand names are strictly UPPERCASE").
    
    Output a strict JSON dictionary using this exact schema:
    {{
      "executive_summary": "High-level overview...",
      "table_grain": "Exact definition of what one row represents for the primary tables...",
      "date_time_context": "Temporal data formatting and logic...",
      "geographic_context": "Geo-spatial data constraints and formatting...",
      "categorical_hierarchy": "Product/business segment hierarchies...",
      "business_methodology": "Units of measure, currencies, and calculation logic (especially regarding percentages/shares)...",
      "data_quality_flags": "Anomalies, NULL handling, placeholder values...",
      "sql_generation_rules": [
          "Rule 1 based on the data",
          "Rule 2 based on the data"
      ],
      "column_definitions": {{
          "TABLE_NAME.COL_1": "Precise meaning and how to filter it...",
          "TABLE_NAME.COL_2": "Precise meaning and how to filter it..."
      }},
      "relationships": [
        {{"table_1": "t1", "col_1": "c1", "table_2": "t2", "col_2": "c2", "join_type": "INNER JOIN"}}
      ],
      "metrics": ["REVENUE", "QTY"],
      "dimensions": ["REGION", "DATE"]
    }}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        raw_text = response.text.strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        raise Exception(f"AI Blueprint Generation Failed: {str(e)}\nRaw Output: {response.text if 'response' in locals() else 'No response'}")

def generate_business_insight(user_query, data_results):
    prompt = f"""
    User asked: "{user_query}"
    Data returned: {json.dumps(data_results)}
    
    Write a highly professional, comprehensive executive summary (4-6 sentences). 
    Do not just read the numbers back. Highlight trends, identify anomalies, explain comparisons, and provide actionable business insights based on this specific data.
    Do not use markdown formatting (no asterisks or hash symbols). Write in clear, natural paragraphs.
    """
    return model.generate_content(prompt).text.strip()