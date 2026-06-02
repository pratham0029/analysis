import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from backend.snowflake_db import get_snowflake_connection, fetch_databases, fetch_schemas, fetch_tables, extract_table_metadata
from backend.ai_engine import parse_user_intent, generate_business_insight, generate_semantic_artifact
from backend.sql_builder import generate_snowflake_sql, execute_live_sql

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SNOWFLAKE_ACCOUNT = "COLPAL-COLGATEPALMOLIVEDEV"

class BaseConnection(BaseModel):
    user: str
    database: Optional[str] = None
    schema_name: Optional[str] = None

class ProfileRequest(BaseConnection):
    tables: List[str]

class QueryRequest(BaseModel):
    user: str
    query: str

class SessionRequest(BaseModel):
    user: str

ACTIVE_CONNECTIONS = {}
USER_SCHEMAS = {}

@app.post("/api/connect-init")
def connect_init(req: BaseConnection):
    global ACTIVE_CONNECTIONS
    try:
        if req.user in ACTIVE_CONNECTIONS:
            try: ACTIVE_CONNECTIONS[req.user].close()
            except: pass
            
        conn = get_snowflake_connection(SNOWFLAKE_ACCOUNT, req.user)
        ACTIVE_CONNECTIONS[req.user] = conn
        
        databases = fetch_databases(conn)
        return {"status": "success", "databases": databases}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/get-schemas")
def get_schemas(req: BaseConnection):
    conn = ACTIVE_CONNECTIONS.get(req.user)
    if not conn: raise HTTPException(status_code=401, detail="Session expired. Please reconnect.")
    try:
        schemas = fetch_schemas(conn, req.database)
        return {"status": "success", "schemas": schemas}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/get-tables")
def get_tables(req: BaseConnection):
    conn = ACTIVE_CONNECTIONS.get(req.user)
    if not conn: raise HTTPException(status_code=401, detail="Session expired. Please reconnect.")
    try:
        tables = fetch_tables(conn, req.database, req.schema_name)
        return {"status": "success", "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/profile-selection")
def profile_selection(req: ProfileRequest):
    global USER_SCHEMAS
    conn = ACTIVE_CONNECTIONS.get(req.user)
    if not conn: raise HTTPException(status_code=401, detail="Session expired. Please reconnect.")
    
    try:
        raw_enriched_metadata = extract_table_metadata(conn, req.database, req.schema_name, req.tables)
        golden_artifact = generate_semantic_artifact(raw_enriched_metadata)
        
        USER_SCHEMAS[req.user] = {
            "database": req.database,
            "schema": req.schema_name,
            "tables": req.tables,
            "raw_metadata": raw_enriched_metadata, 
            "metadata": golden_artifact  
        }
        return {"status": "success", "artifact": golden_artifact}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/restore-session")
def restore_session(req: SessionRequest):
    if req.user in ACTIVE_CONNECTIONS and req.user in USER_SCHEMAS:
        return {"status": "success", "context": USER_SCHEMAS[req.user]}
    raise HTTPException(status_code=401, detail="Session expired.")

@app.post("/api/disconnect")
def disconnect_session(req: SessionRequest):
    global ACTIVE_CONNECTIONS, USER_SCHEMAS
    if req.user in ACTIVE_CONNECTIONS:
        try: ACTIVE_CONNECTIONS[req.user].close()
        except: pass
        del ACTIVE_CONNECTIONS[req.user]
    if req.user in USER_SCHEMAS:
        del USER_SCHEMAS[req.user]
    return {"status": "success"}

@app.post("/api/analyze")
def analyze_data(req: QueryRequest):
    conn = ACTIVE_CONNECTIONS.get(req.user)
    active_context = USER_SCHEMAS.get(req.user)
    
    if not conn or not active_context:
        raise HTTPException(status_code=401, detail="Session expired. Please reconnect.")

    schema_map = active_context.get("metadata", {})
    raw_metadata = active_context.get("raw_metadata", {})
    database = active_context.get("database", "UNKNOWN")
    schema = active_context.get("schema", "UNKNOWN")
    
    # 1. Handle casual conversation first
    parsed_intent = parse_user_intent(req.query, schema_map)
    if parsed_intent.get("intent_type") == "chat":
        return {"type": "chat", "message": parsed_intent.get("message")}
    
    try:
        # 2. Fetch the advanced Multi-Chart Plan
        config = generate_snowflake_sql(req.query, raw_metadata, schema_map)
        
        # 3. Handle Clarifications & Impossible requests
        if config.get("status") in ["clarify", "impossible"]:
            return {"type": "chat", "message": config.get("message", "I need more details to run this analysis.")}
            
        # 4. Loop through and execute every chart the AI requested
        executed_charts = []
        for chart in config.get("charts", []):
            sql = chart.get("sql")
            chart_data = execute_live_sql(conn, sql, database, schema)
            
            if chart_data: # Only attach it if data was found
                executed_charts.append({
                    "chart_title": chart.get("chart_title", "Analysis"),
                    "chart_type": chart.get("chart_type", "bar"),
                    "data": chart_data,
                    "sql": sql
                })
        
        if not executed_charts:
            return {"type": "chat", "message": "The queries executed correctly, but returned no matching data."}
            
        # 5. Generate a massive overarching summary of ALL charts combined
        insight = generate_business_insight(req.query, executed_charts)
        
        context_payload = {
            "database": database,
            "schema": schema,
            "tables": active_context.get("tables", ["UNKNOWN"])
        }
        
        return {
            "type": "query", 
            "insight": insight,
            "charts": executed_charts, # Returns an Array of charts now!
            "context": context_payload
        }
        
    except Exception as e:
        return {
            "type": "chat",
            "message": f"Analytical calculation failed.\n\nDetails: {str(e)}"
        }

@app.get("/", response_class=HTMLResponse)
def get_workspace_ui():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, "frontend", "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")