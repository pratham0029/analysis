import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_snowflake_sql(user_query, raw_metadata, golden_artifact):
    """
    Translates natural language into dynamic chart configurations using Agentic Reasoning.
    """
    prompt = f"""
    You are an autonomous Lead Data Engineer and Business Intelligence Agent.
    Your goal is to dynamically interpret the user's natural language request and design the optimal analytical response using the provided Snowflake schema.

    USER QUESTION: "{user_query}"

    RAW SCHEMA: 
    {json.dumps(raw_metadata, default=str)}

    SEMANTIC BLUEPRINT: 
    {json.dumps(golden_artifact, default=str)}

    AGENTIC REASONING RULES:
    1. AMBIGUITY & CLARIFICATION (CRITICAL): You are an intelligent agent. If the user's request is vague (e.g., "show me trends" but there are multiple date columns, or "show me sales" but there are 5 different sales metrics), DO NOT GUESS. Set "status" to "clarify" and formulate a specific, conversational question in the "message" field asking the user to clarify their intent based on the available schema.
    2. IMPOSSIBLE REQUESTS: If the request asks for data that objectively does not exist in the provided schema (e.g., HR data in a Sales table), set "status" to "impossible" and politely explain what data is actually available in the "message".
    3. DYNAMIC MULTI-CHARTING: If the user's request is broad but answerable, or requires looking at the data from multiple angles, independently decide how many separate charts to build to give them a comprehensive answer. Generate a distinct SQL query and chart configuration for each angle in the JSON array.
    4. TABLE JOINS: Dynamically construct valid SQL JOINs based strictly on the Foreign Keys defined in the Semantic Blueprint whenever a query requires dimensions and metrics that span multiple tables.
    5. CHART TYPES & SORTING: 
       - For chronological/time-series data, assign chart_type "line" and ORDER BY the date column ASC.
       - For categorical rankings/comparisons, assign chart_type "bar" and ORDER BY the metric DESC.
    6. SQL FORMAT: Every SQL query MUST output exactly TWO columns. Column 1: Dimension (X-Axis string/date). Column 2: Aggregated Metric (Y-Axis number). Use LIMIT 15 for readability. Do not include markdown formatting like ```sql.

    Return your response strictly as a JSON object:
    {{
      "status": "success", 
      "message": "Only used if status is clarify or impossible. Leave blank for success.",
      "charts": [
        {{
          "chart_title": "Dynamically Generated Title",
          "chart_type": "line",
          "sql": "SELECT DIMENSION, SUM(METRIC) ... ORDER BY ... LIMIT 15"
        }}
      ]
    }}
    """
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)

def execute_live_sql(conn, sql_query, database, schema):
    """
    Safely locks onto the warehouse and metadata context before executing the query.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('USE ROLE "PUBLIC"')
        cursor.execute('USE WAREHOUSE "VIZ_UTIL_SMALL_WH"')
        cursor.execute(f'USE DATABASE "{database}"')
        cursor.execute(f'USE SCHEMA "{schema}"')
        
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            if row[0] is None:
                continue 
            dim_val = str(row[0])
            try:
                metric_val = float(row[1]) if row[1] is not None else 0
            except ValueError:
                metric_val = 0
                
            data.append({"dimension": dim_val, "metric": metric_val})
            
        return data
        
    except Exception as e:
        raise Exception(f"SQL Execution Failed: {str(e)}")
    finally:
        cursor.close()