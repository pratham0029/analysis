import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import math
import re
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_snowflake_sql(user_query, raw_metadata, golden_artifact, history=None):
    raw_schema_str = json.dumps(raw_metadata, default=str)
    blueprint_str = json.dumps(golden_artifact, default=str)
    
    history_str = ""
    if history and len(history) > 0:
        history_str = "PREVIOUS CONVERSATION CONTEXT:\n"
        for msg in history:
            history_str += f"{msg['role'].upper()}: {msg['content']}\n"

    prompt = f"""
    You are an autonomous Lead Data Engineer and Business Intelligence Agent.
    Your goal is to dynamically interpret the user's natural language request and design the optimal analytical response using the provided Snowflake schema.

    {history_str}
    
    CURRENT USER QUESTION: "{user_query}"
    RAW SCHEMA: {raw_schema_str}
    SEMANTIC BLUEPRINT: {blueprint_str}

    CRITICAL JSON FORMATTING RULES:
    1. ZERO OUTSIDE TEXT: You MUST output ONLY a valid JSON object. Do not output conversational pre-text.
    2. BRAIN TRACE: Put absolutely all of your reasoning and "thinking out loud" inside the "thought_process" key.

    AGENTIC BEHAVIOR & FALLBACKS:
    3. GREETINGS & CHAT: If the user just says "hello", or asks a general data question that does NOT require a SQL query, set "status" to "chat" and write your response in the "message" field. Leave "charts" empty.
    4. AMBIGUITY: If the request is confusing or vague, set "status" to "clarify" and ask a clarifying question in "message".
    5. UNSUPPORTED CHARTS: We ONLY support the 7 charts listed below. If a user asks for a Radar, Pie, or other chart, map it to the closest supported chart (like 'bar' or 'stacked_bar_100'), set "status" to "success", and you MUST clearly explain in the "message" field: "I have adapted your request for a [requested chart] into a [supported chart] as radar/pie visuals are currently optimized as multi-series bar trends."
    
    6. RELATIVE DATES (FUTURE DATA TRAP - CRITICAL): Your tables contain future calendar rows padded with 0 or NULL sales. If a user asks for "this year", "last 30 days", "recent", or "last year", NEVER use CURRENT_DATE(). You MUST dynamically anchor to the maximum date in the table WHERE THE METRIC IS GREATER THAN ZERO OR NOT NULL.

    7. FLEXIBLE PRODUCT/BRAND TEXT MATCHING: Dev tables often have mismatched or nested string names (e.g., 'Colgate Total' might be Brand='COLGATE' and Item Desc='TOTAL'). If the user provides a multi-word or specific brand/product name, utilize case-insensitive `ILIKE` operators or split the text across both brand and product description matching parameters.

    THE 7 SUPPORTED CHARTS & EXACT SQL STRUCTURE RULES:
    You MUST alias your SQL columns EXACTLY as requested below so our frontend parser can read them.
    
    1. "line": (For chronological trends). Columns: `dim` (Date), `metric` (Y-axis). Optional: `series`.
    2. "bar": (For comparisons, category rankings). Columns: `dim` (Category), `metric` (Value). Optional: `series`.
    3. "scatter": (For correlation). Columns: `dim` (Name), `x_metric`, `y_metric`. Optional: `series`.
    4. "histogram": (For distributions). Columns: `dim` (Calculated Bucket), `metric` (Count).
    5. "boxplot": (For statistical ranges). Columns: `dim` (Category), `min_val`, `q1_val`, `median_val`, `q3_val`, `max_val`.
    6. "stacked_bar_100": (For part-to-whole compositions). Columns: `dim` (Category/Date), `metric` (Raw Value), `series` (Segment).
    7. "choropleth": (For geographic mapping). 
       - Columns: `dim` (Country/State Name), `metric` (Value).
       - EXPLICIT TARGET: You MUST include a new key "target_map" in your JSON specifying the country.
       - ALLOWED MAPS: "USA", "Brazil", "India", "Canada", "Mexico", "UK", "Germany", "France", "Italy", "Spain", "Australia", "China", "Japan", "SouthAfrica", "Argentina", or "World".
       - STANDARD NAMES ONLY: The `dim` column MUST contain standard state/country names. If the database uses aggregated custom regions (e.g., 'RJ State+MG+ES', 'NORTE', 'NE'), standard maps cannot draw them. In this case, fallback to a "bar" chart and explain in "message" that custom regions cannot be mapped geographically.
    
    Return your response strictly as this JSON object and nothing else:
    {{
      "thought_process": "Write step-by-step analytical rationale here...",
      "status": "success", 
      "message": "Write any adaptation or clarification descriptions here...",
      "charts": [
        {{
          "chart_title": "Descriptive Title",
          "chart_type": "choropleth",
          "target_map": "Brazil",
          "sql": "SELECT category AS dim, SUM(sales) AS metric FROM table_name GROUP BY dim"
        }}
      ]
    }}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raw_text = response.text.strip()
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            return json.loads(raw_text[start_idx:end_idx+1])
        raise Exception(f"AI returned malformed JSON. Details: {str(e)}")

def execute_live_sql(conn, sql_query, database, schema):
    if not is_safe_sql(sql_query):
        raise Exception("Security Error: Query blocked.")

    cursor = conn.cursor()
    try:
        cursor.execute('USE ROLE "PUBLIC"')
        cursor.execute('USE WAREHOUSE "VIZ_UTIL_SMALL_WH"')
        cursor.execute(f'USE DATABASE "{database}"')
        cursor.execute(f'USE SCHEMA "{schema}"')
        
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        col_names = [desc[0].lower() for desc in cursor.description]
        
        data = []
        for row in rows:
            if row[0] is None:
                continue
            
            clean_dict = {}
            row_dict = dict(zip(col_names, row))
            for k, v in row_dict.items():
                if isinstance(v, (int, float)):
                    if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
                        clean_dict[k] = 0
                    else:
                        clean_dict[k] = v
                elif v is not None:
                    try:
                        parsed_float = float(v)
                        if math.isinf(parsed_float) or math.isnan(parsed_float):
                            clean_dict[k] = 0
                        else:
                            clean_dict[k] = parsed_float
                    except Exception:  # FIX: Bulletproof catch-all for Dates, Decimals, Binary, or Overflow anomalies
                        # If we can't do math on it, it safely becomes a label
                        clean_dict[k] = str(v) 
                else:
                    clean_dict[k] = 0
            
            data.append(clean_dict)
        return data
    except Exception as e:
        raise Exception(f"SQL Execution Failed: {str(e)}")
    finally:
        cursor.close()

def is_safe_sql(sql_query):
    forbidden_pattern = re.compile(r'(?i)\b(drop|delete|update|insert|alter|grant|revoke|truncate|create|replace)\b')
    return not bool(forbidden_pattern.search(sql_query))

def fix_snowflake_sql(bad_sql, error_msg, golden_artifact):
    blueprint_str = json.dumps(golden_artifact, default=str)
    prompt = f"""
    You are an automated Data Engineering script. Your previous Snowflake query failed.
    ORIGINAL QUERY: {bad_sql}
    SNOWFLAKE ERROR: {error_msg}
    VALID SCHEMA MAP: {blueprint_str}
    Fix the SQL query based on the error. Output ONLY a strict JSON object with the fixed SQL.
    {{
      "sql": "SELECT ..."
    }}
    """
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    try:
        raw_text = response.text.strip()
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            return json.loads(raw_text[start_idx:end_idx+1])
        return {"sql": bad_sql} 
    except Exception:
        return {"sql": bad_sql}