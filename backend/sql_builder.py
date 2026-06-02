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
    # Safely extract JSON strings before injecting into the f-string to prevent syntax errors
    raw_schema_str = json.dumps(raw_metadata, default=str)
    blueprint_str = json.dumps(golden_artifact, default=str)

    prompt = f"""
    You are an autonomous Lead Data Engineer and Business Intelligence Agent.
    Your goal is to dynamically interpret the user's natural language request and design the optimal analytical response using the provided Snowflake schema.

    USER QUESTION: "{user_query}"

    RAW SCHEMA: 
    {raw_schema_str}

    SEMANTIC BLUEPRINT: 
    {blueprint_str}

    AGENTIC REASONING RULES:
    1. CHAIN OF THOUGHT: You MUST write out your step-by-step reasoning in the "thought_process" field first. Analyze what the user is asking, identify the exact tables and columns needed, and explicitly state how you will group and sort the data.
    2. AMBIGUITY & CLARIFICATION: If the user's request is vague, DO NOT GUESS. Set "status" to "clarify" and formulate a specific, conversational question in the "message" field asking the user to clarify.
    3. IMPOSSIBLE REQUESTS: If the request asks for data that objectively does not exist in the schema, set "status" to "impossible" and politely explain what data is actually available.
    4. DYNAMIC MULTI-CHARTING: If the user's request requires looking at the data from multiple angles (e.g. daily vs weekly), independently decide how many separate charts to build. Generate a distinct SQL query and chart configuration for each angle.
    5. TRANSACTIONAL DATA TRAP (CRITICAL): These tables contain transactional data. You MUST aggregate (GROUP BY) the data FIRST, before applying any LIMITs.
    6. TIME-SERIES SQL STRUCTURE: To get the most recent trend data while avoiding future zero-placeholder rows and avoiding the transactional trap, use this EXACT SQL pattern:
       SELECT dim, metric FROM (
           SELECT date_column AS dim, SUM(metric_column) AS metric
           FROM table_name
           WHERE date_column <= (SELECT MAX(date_column) FROM table_name WHERE metric_column > 0)
           GROUP BY date_column
           ORDER BY date_column DESC
           LIMIT 15
       ) subquery
       ORDER BY dim ASC
    7. CHART TYPES: For rankings/comparisons, use "bar". For chronological trends, use "line".
    8. SQL FORMAT: Every query MUST output exactly TWO columns: Dimension (X-Axis) and Metric (Y-Axis). Do NOT wrap the JSON output in markdown blocks.

    Return your response strictly as a JSON object:
    {{
      "thought_process": "...",
      "status": "success", 
      "message": "",
      "charts": [
        {{
          "chart_title": "Dynamically Generated Title",
          "chart_type": "line",
          "sql": "SELECT dim, metric FROM ( ... ) subquery ORDER BY dim ASC"
        }}
      ]
    }}
    """
    
    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    # --- THE ULTIMATE JSON EXTRACTOR ---
    try:
        raw_text = response.text.strip()
    except Exception as e:
        raise Exception(f"AI API Blocked the response (likely safety filter). Details: {str(e)}")
        
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        clean_json = raw_text[start_idx:end_idx+1]
        try:
            return json.loads(clean_json)
        except Exception as e:
            # If it's malformed JSON, show us what Gemini actually wrote
            raise Exception(f"Malformed JSON from AI. Raw output: \n{clean_json}")
    else:
        # If there are no curly braces at all, show the exact string
        raise Exception(f"AI returned no JSON. Raw output: \n'{raw_text}'")


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