import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')

def generate_semantic_artifact(enriched_metadata):
    prompt = f"""
    You are an expert Enterprise Database Architect. Analyze these tables, column definitions, and diverse data samples:
    {json.dumps(enriched_metadata, default=str)}
    
    Extract an exhaustive "Semantic Blueprint" to ensure absolute accuracy for downstream SQL generation.

    Analyze and extract the following:
    1. EXECUTIVE SUMMARY: High-level business overview of the data.
    2. TABLE GRAIN: What does a single, individual row represent? (e.g., "One row represents one SKU sold at one store on a specific day"). This is critical to prevent fan-out joins and double counting.
    3. DATE/TIME CONTEXT: How are dates formatted (YYYY-MM-DD, UNIX, Fiscal)? Which column is the primary filter?
    4. GEOGRAPHIC CONTEXT: Specific regions, country codes, or geographic granularities present.
    5. CATEGORICAL HIERARCHY: How are dimensions grouped? (e.g., Manufacturer -> Brand -> Subbrand).
    6. BUSINESS METHODOLOGY: Inferred currencies, units of measure (KG, Liters, Units), and whether metrics represent gross, net, or percentages.
    7. DATA QUALITY FLAGS: Identify any observed anomalies, default dates (e.g., 9999-12-31), or handling of NULLs.
    8. SCHEMA MAPPING: Primary Keys, Foreign Keys, precise column definitions, metrics, and dimensions.
    
    Output a strict JSON dictionary using this exact schema:
    {{
      "executive_summary": "High-level overview paragraph...",
      "table_grain": "Exact definition of what one row represents...",
      "date_time_context": "Explanation of temporal data formatting and logic...",
      "geographic_context": "Explanation of geo-spatial data and boundaries...",
      "categorical_hierarchy": "Explanation of product or business segment hierarchies...",
      "business_methodology": "Details on units of measure, currencies, and calculation logic...",
      "data_quality_flags": "Noticed anomalies, NULL handling, or specific default values...",
      "column_definitions": {{
          "COL_1": "Meaning and usage...",
          "COL_2": "Meaning and usage..."
      }},
      "relationships": [
        {{"table_1": "t1", "col_1": "c1", "table_2": "t2", "col_2": "c2"}}
      ],
      "metrics": ["REVENUE", "QTY"],
      "dimensions": ["REGION", "DATE"]
    }}
    """
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)

def generate_business_insight(user_query, data_results):
    prompt = f"""
    User asked: "{user_query}"
    Data returned: {json.dumps(data_results)}
    
    Write a highly professional, comprehensive executive summary (4-6 sentences). 
    Do not just read the numbers back. Highlight trends, identify anomalies, explain comparisons, and provide actionable business insights based on this specific data.
    Do not use markdown formatting (no asterisks or hash symbols). Write in clear, natural paragraphs.
    """
    return model.generate_content(prompt).text.strip()