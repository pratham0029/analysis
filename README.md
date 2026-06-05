# AI Data Analyst

An intelligent data analysis workspace that connects to Snowflake databases and enables natural language querying with automated visualization generation.

## Features

- **Snowflake Integration**: Secure SSO authentication with Snowflake data warehouses
- **Natural Language to SQL**: Uses Google Gemini AI (3.1-pro-preview and 3.5-flash) to translate natural language queries into optimized SQL
- **Dynamic Visualization**: Automatically generates interactive charts (7 types: line, bar, scatter, histogram, boxplot, stacked_bar_100, choropleth) using ECharts
- **Semantic Understanding**: AI analyzes table schemas and sample data to understand business context with comprehensive semantic blueprint
- **Multi-Chart Analysis**: Can generate multiple visualizations from a single query
- **Business Insights**: AI-generated executive summaries of analysis results
- **SQL Safety Guardrails**: Regex-based validation to prevent destructive operations
- **Self-Healing SQL**: AI-powered automatic SQL error correction and retry logic
- **Chat History Context**: Maintains conversation context for follow-up questions
- **Flexible Text Matching**: ILIKE-based fuzzy matching for product/brand names
- **Future Data Trap Prevention**: Smart relative date handling to avoid zero-padded future rows
- **Pre-Calculated Column Support**: Automatically detects and uses This Year (TY) / Last Year (LY) columns when available
- **Share Calculation Logic**: Dynamically calculates shares/ratios from base metrics to avoid mathematical errors
- **Schema Logging**: Automatic logging of raw Snowflake metadata to timestamped JSON files

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Snowflake Connector**: Python driver for Snowflake
- **Google Generative AI**: Gemini 3.1-pro-preview (semantic analysis) and Gemini 3.5-flash (SQL generation)
- **Pydantic**: Data validation

### Frontend
- **Vanilla HTML/JavaScript**: No framework dependencies
- **TailwindCSS**: Utility-first styling (via CDN)
- **ECharts**: Interactive charting library (via CDN)

## Prerequisites

- Python 3.13+
- Snowflake account with SSO authentication
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-data-analyst
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Configuration

### Snowflake Settings

Edit `backend/main.py` to configure your Snowflake account:
```python
SNOWFLAKE_ACCOUNT = "YOUR_ACCOUNT_IDENTIFIER"
```

Edit `backend/snowflake_db.py` to configure warehouse and role:
```python
warehouse='YOUR_WAREHOUSE',
role='YOUR_ROLE'
```

Edit `backend/sql_builder.py` to configure warehouse and role in the `execute_live_sql` function:
```python
cursor.execute('USE ROLE "YOUR_ROLE"')
cursor.execute('USE WAREHOUSE "YOUR_WAREHOUSE"')
```

## Usage

1. Start the development server:
```bash
uv run uvicorn backend.main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. **Connect to Snowflake**:
   - Enter your corporate SSO email
   - Complete the SSO authentication in the browser popup

4. **Select Data Sources**:
   - Choose a database from the dropdown
   - Search and select schemas
   - Select tables and views to analyze
   - Click "Load Selected Tables" to analyze the schema

5. **Ask Questions**:
   - Type natural language queries in the chat interface
   - Examples:
     - "Show me revenue trends over the last 30 days"
     - "What are the top 5 products by sales?"
     - "Compare performance across regions"

## API Endpoints

### Authentication & Connection
- `POST /api/connect-init` - Initialize Snowflake SSO connection
- `POST /api/disconnect` - Close active session
- `POST /api/restore-session` - Restore previous session

### Data Exploration
- `POST /api/get-schemas` - Fetch schemas for a database
- `POST /api/get-tables` - Fetch tables and views for a schema
- `POST /api/profile-selection` - Analyze selected tables and generate semantic artifact

### Analysis
- `POST /api/analyze` - Process natural language query and return visualizations

## Project Structure

```
ai-data-analyst/
├── backend/
│   ├── main.py              # FastAPI application and API endpoints
│   ├── snowflake_db.py      # Snowflake connection and metadata extraction
│   ├── ai_engine.py         # AI processing (semantic analysis, intent parsing)
│   └── sql_builder.py       # SQL generation and execution
├── frontend/
│   └── index.html           # Single-page application UI
├── logs/                    # Auto-generated directory for Snowflake metadata logs
├── .env                     # Environment variables
├── pyproject.toml           # Python dependencies
└── README.md                # This file
```

## How It Works

1. **Connection**: User authenticates via Snowflake SSO
2. **Schema Analysis**: Selected tables are analyzed for:
   - Column definitions and types
   - Sample data rows (using TABLESAMPLE for efficiency)
   - Primary/foreign key relationships
   - Metrics vs dimensions classification
3. **Semantic Artifact**: AI generates a comprehensive "semantic blueprint" understanding the business context including:
   - Executive summary of the dataset
   - Table grain (what one row represents)
   - Date/time context and formatting
   - Geographic boundaries
   - Categorical hierarchies
   - Business methodology and metrics
   - Data quality flags and anomalies
   - SQL generation rules
4. **Schema Logging**: Raw Snowflake metadata is automatically logged to timestamped JSON files in the `logs/` directory
5. **Query Processing**:
   - User submits natural language query
   - AI parses intent and identifies required metrics/dimensions
   - AI generates optimized SQL queries with proper aggregation
   - Multiple charts can be generated for different analytical angles
   - AI handles pre-calculated TY/LY columns when available
   - AI dynamically calculates shares/ratios from base metrics
6. **Visualization**: Results are rendered as interactive charts with SQL transparency

## Technical Architecture & User Journey

### Methodology Overview

This system implements a **Schema-Augmented Generation (SAG)** pattern, similar to Retrieval-Augmented Generation (RAG), but instead of retrieving document chunks, it retrieves and analyzes database schema metadata. The AI uses this semantic understanding to generate context-aware SQL queries and visualizations.

### Complete Technical Flow

#### Phase 1: Connection & Authentication

**User Action**: Enters corporate SSO email and clicks "Sign in via SSO"

**Backend Flow**:
1. `POST /api/connect-init` → `connect_init()` in `main.py`
2. Calls `get_snowflake_connection(account, user)` in `snowflake_db.py`
   - Cleans account identifier (removes .snowflakecomputing.com, https://)
   - Establishes Snowflake connection using `authenticator='externalbrowser'` (SSO)
   - Sets explicit warehouse: `VIZ_UTIL_SMALL_WH`
   - Sets explicit role: `PUBLIC`
   - Stores connection in `ACTIVE_CONNECTIONS` dictionary (reuses if exists)
3. Calls `fetch_databases(conn)` in `snowflake_db.py`
   - Executes `SHOW DATABASES` in Snowflake
   - Returns list of database names
4. Returns database list to frontend

#### Phase 2: Schema Exploration

**User Action**: Selects database, then schema, then tables/views

**Backend Flow**:
1. `POST /api/get-schemas` → `get_schemas()` in `main.py`
   - Retrieves connection from `ACTIVE_CONNECTIONS`
   - Calls `fetch_schemas(conn, database)` in `snowflake_db.py`
   - Executes `SHOW SCHEMAS IN DATABASE "{database}"`
   - Returns schema list

2. `POST /api/get-tables` → `get_tables()` in `main.py`
   - Calls `fetch_tables(conn, database, schema)` in `snowflake_db.py`
   - Executes `SHOW TABLES IN SCHEMA "{database}"."{schema}"`
   - Executes `SHOW VIEWS IN SCHEMA "{database}"."{schema}"`
   - Returns combined list of tables and views with types

#### Phase 3: Semantic Understanding (The "Semantic Blueprint")

**User Action**: Selects tables/views and clicks "Load Selected Tables"

**Backend Flow**:
1. `POST /api/profile-selection` → `profile_selection()` in `main.py`
2. Calls `extract_table_metadata(conn, database, schema, tables)` in `snowflake_db.py`
   - For each selected table:
     - Executes `DESCRIBE TABLE "{database}"."{schema}"."{table}"`
     - Extracts column names and data types
     - Executes `SELECT * FROM ... TABLESAMPLE BERNOULLI (1) LIMIT 40` to get sample rows
     - Stores column definitions + sample data in metadata dictionary
   - Returns enriched metadata with schema + sample_data for each table

3. Calls `generate_semantic_artifact(raw_enriched_metadata)` in `ai_engine.py`
   - Sends enriched metadata to Google Gemini 3.1-pro-preview
   - AI analyzes and identifies:
     - Executive summary of the dataset
     - Table grain (what one row represents)
     - Date/time context and formatting
     - Geographic boundaries
     - Categorical hierarchies
     - Business methodology and metrics
     - Data quality flags and anomalies
     - SQL generation rules
     - Column definitions with precise meanings
     - Primary/foreign key relationships
     - Metrics vs dimensions classification
   - Returns "semantic blueprint" JSON with:
     ```json
     {
       "executive_summary": "Business context explanation...",
       "table_grain": "What one row represents...",
       "date_time_context": "Temporal data formatting...",
       "geographic_context": "Geo-spatial data constraints...",
       "categorical_hierarchy": "Product/business segment hierarchies...",
       "business_methodology": "Units of measure, currencies, calculation logic...",
       "data_quality_flags": "Anomalies, NULL handling, placeholder values...",
       "sql_generation_rules": ["Rule 1", "Rule 2"],
       "column_definitions": {"TABLE_NAME.COL_1": "Precise meaning..."},
       "relationships": [{"table_1": "...", "col_1": "...", "table_2": "...", "col_2": "...", "join_type": "INNER JOIN"}],
       "metrics": ["TOTAL_REVENUE", "QUANTITY_SOLD"],
       "dimensions": ["REGION", "ORDER_DATE"]
     }
     ```

4. Logs raw metadata to `logs/snowflake_dump_{timestamp}.json` for debugging and audit purposes
5. Stores in `USER_SCHEMAS[user]`:
   - database, schema, tables
   - raw_metadata (column definitions + sample data)
   - metadata (semantic blueprint - comprehensive understanding)

#### Phase 4: Query Analysis & Execution (The Core AI Pipeline)

**User Action**: Types natural language question (e.g., "Show me revenue trends by region")

**Backend Flow**:
1. `POST /api/analyze` → `analyze_data()` in `main.py`
   - Retrieves connection from `ACTIVE_CONNECTIONS`
   - Retrieves context from `USER_SCHEMAS` (semantic blueprint + raw metadata)

2. Calls `generate_snowflake_sql(user_query, raw_metadata, schema_map, history)` in `sql_builder.py`
   - Constructs prompt with:
     - Chat history (for context from previous questions)
     - Current user question
     - Raw schema (column definitions + sample data)
     - Semantic blueprint (comprehensive understanding with relationships, metrics, dimensions, and business context)
   - Sends to Google Gemini 3.5-flash with strict JSON output requirement
   - AI performs agentic reasoning:
     - Analyzes user intent (greeting, clarification needed, or data query)
     - Identifies required metrics and dimensions
     - Determines optimal chart types (line, bar, scatter, histogram, boxplot, stacked_bar_100, choropleth)
     - Generates SQL queries with proper aggregation (GROUP BY before LIMIT)
     - Handles relative dates (anchors to MAX date where metric > 0 to avoid future zero rows)
     - Uses ILIKE for flexible text matching (product/brand names)
     - Checks for pre-calculated TY/LY columns before attempting date filtering
     - Avoids 1-bar charts by using at least LIMIT 5 or LIMIT 10
     - Dynamically calculates shares/ratios from base metrics using window functions
   - Returns JSON configuration:
     ```json
     {
       "thought_process": "Step-by-step analytical rationale...",
       "status": "success",
       "message": "Any clarifications or adaptations...",
       "charts": [
         {
           "chart_title": "Revenue Trends by Region",
           "chart_type": "line",
           "target_map": "Brazil",
           "sql": "SELECT region AS dim, SUM(revenue) AS metric FROM table GROUP BY region"
         }
       ]
     }
     ```

3. For each chart in configuration:
   - Calls `is_safe_sql(sql_query)` in `sql_builder.py`
     - Regex validation: blocks DROP, DELETE, UPDATE, INSERT, ALTER, GRANT, REVOKE, TRUNCATE, CREATE, REPLACE
     - Returns False if destructive keywords detected
   
   - If safe, calls `execute_live_sql(conn, sql, database, schema)` in `sql_builder.py`
     - Sets context: `USE ROLE "PUBLIC"`, `USE WAREHOUSE "VIZ_UTIL_SMALL_WH"`, `USE DATABASE`, `USE SCHEMA`
     - Executes SQL query
     - Processes results:
       - Handles NULL values
       - Converts to float for metrics
       - Handles infinity/NaN (converts to 0)
       - Handles non-numeric types (converts to string for labels)
     - Returns data array: `[{"dim": "Region A", "metric": 1000}, ...]`

   - If SQL execution fails:
     - Calls `fix_snowflake_sql(bad_sql, error_msg, semantic_blueprint)` in `sql_builder.py`
       - Sends failed SQL + error message + schema map to AI
       - AI analyzes error and generates corrected SQL
       - Returns JSON: `{"sql": "SELECT ..."}`
     - Retries execution with fixed SQL
     - If still fails, adds error chart to results

4. Calls `generate_business_insight(user_query, executed_charts)` in `ai_engine.py`
   - Sends user question + chart data to AI
   - AI generates comprehensive executive summary (4-6 sentences)
   - Highlights trends, identifies anomalies, explains comparisons
   - Returns natural language insight

5. Returns to frontend:
   ```json
   {
     "type": "query",
     "insight": "Executive summary...",
     "charts": [...],
     "context": {"database": "...", "schema": "...", "tables": [...]},
     "message": "Any AI messages..."
   }
   ```

#### Phase 5: Visualization Rendering

**Frontend Flow**:
1. Receives chart data and SQL queries
2. For each chart:
   - Creates ECharts instance
   - Configures chart based on type (line, bar, scatter, etc.)
   - Renders with proper tooltips, axes, styling
   - Displays SQL query in expandable panel
3. Displays AI executive summary
4. Shows query context (database, schema, tables)

### Function Execution Order & Details

#### Connection Phase Functions

1. **`get_snowflake_connection(account, user)`** (snowflake_db.py)
   - **Purpose**: Establish secure SSO connection to Snowflake
   - **How it works**: 
     - Cleans account identifier string
     - Uses external browser authenticator (Okta/Azure AD)
     - Sets explicit warehouse and role for security
   - **Returns**: Active Snowflake connection object

2. **`fetch_databases(conn)`** (snowflake_db.py)
   - **Purpose**: List available databases
   - **How it works**: Executes `SHOW DATABASES` SQL command
   - **Returns**: List of database names

3. **`fetch_schemas(conn, database)`** (snowflake_db.py)
   - **Purpose**: List schemas in a database
   - **How it works**: Executes `SHOW SCHEMAS IN DATABASE` SQL command
   - **Returns**: List of schema names

4. **`fetch_tables(conn, database, schema)`** (snowflake_db.py)
   - **Purpose**: List tables and views in a schema
   - **How it works**: 
     - Executes `SHOW TABLES` and `SHOW VIEWS` commands
     - Combines results with type indicators
   - **Returns**: List of objects with name and type (TABLE/VIEW)

#### Semantic Understanding Functions

5. **`extract_table_metadata(conn, database, schema, tables)`** (snowflake_db.py)
   - **Purpose**: Extract column definitions and sample data
   - **How it works**:
     - For each table: runs `DESCRIBE TABLE` to get schema
     - Runs `SELECT * TABLESAMPLE BERNOULLI (1) LIMIT 40` to get sample rows
     - Handles secured views that restrict SELECT *
   - **Returns**: Dictionary with column definitions and sample data per table

6. **`generate_semantic_artifact(enriched_metadata)`** (ai_engine.py)
   - **Purpose**: AI-powered business context analysis
   - **How it works**:
     - Sends schema + sample data to Gemini 3.1-pro-preview
     - AI identifies relationships, metrics, dimensions
     - AI writes comprehensive semantic blueprint including executive summary, table grain, date/time context, geographic context, categorical hierarchy, business methodology, data quality flags, and SQL generation rules
   - **Returns**: Semantic blueprint JSON with comprehensive understanding

#### Query Analysis Functions

7. **`generate_snowflake_sql(user_query, raw_metadata, semantic_blueprint, history)`** (sql_builder.py)
   - **Purpose**: Translate natural language to SQL with multi-chart planning
   - **How it works**:
     - Constructs comprehensive prompt with schema, semantic blueprint, chat history
     - AI performs chain-of-thought reasoning
     - AI determines optimal chart types and SQL structure
     - AI handles edge cases (relative dates, text matching, aggregation)
     - AI checks for pre-calculated TY/LY columns before date filtering
     - AI avoids 1-bar charts by using at least LIMIT 5 or LIMIT 10
     - AI dynamically calculates shares/ratios from base metrics using window functions
   - **Returns**: JSON with chart configurations and SQL queries

8. **`is_safe_sql(sql_query)`** (sql_builder.py)
   - **Purpose**: Validate SQL for destructive operations
   - **How it works**: Regex pattern matching against forbidden keywords
   - **Returns**: Boolean (True if safe, False if blocked)

9. **`execute_live_sql(conn, sql_query, database, schema)`** (sql_builder.py)
   - **Purpose**: Execute SQL in Snowflake with data processing
   - **How it works**:
     - Sets role, warehouse, database, schema context
     - Executes SQL query
     - Processes results (handles NULL, infinity, type conversion)
     - Formats data for frontend consumption
   - **Returns**: Array of dimension/metric objects

10. **`fix_snowflake_sql(bad_sql, error_msg, semantic_blueprint)`** (sql_builder.py)
    - **Purpose**: AI-powered SQL error correction
    - **How it works**:
      - Sends failed SQL + error + schema to AI
      - AI analyzes error and generates corrected SQL
      - Handles markdown formatting in AI response
    - **Returns**: JSON with corrected SQL

11. **`generate_business_insight(user_query, data_results)`** (ai_engine.py)
    - **Purpose**: Generate executive summary from analysis results
    - **How it works**:
      - Sends user question + chart data to AI
      - AI analyzes trends, anomalies, comparisons
      - AI writes professional 4-6 sentence summary
    - **Returns**: Natural language insight text

### Key Design Patterns

- **Schema-Augmented Generation (SAG)**: Like RAG, but retrieves database schema instead of documents
- **Agentic Reasoning**: AI performs step-by-step analytical thinking before generating SQL
- **Self-Healing Loop**: Automatic error detection and correction without user intervention
- **Guardrail Pattern**: Multiple safety layers (regex validation, explicit role/warehouse, connection pooling)
- **Context Persistence**: Session-based storage of semantic understanding for follow-up questions
- **Multi-Modal Output**: Combines SQL, charts, and natural language insights

## Security Notes

- Snowflake credentials are never stored; authentication uses SSO via external browser
- API keys should be kept in `.env` and never committed to version control
- All SQL queries are executed with explicit role and warehouse context

## Development

### Running in Development Mode
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding Dependencies
```bash
uv add <package-name>
```

## Troubleshooting

**SSO Authentication Fails**: Ensure your Snowflake account identifier is correct and you have proper permissions.

**No Data Returned**: Check that the selected warehouse has compute credits and the tables contain data.

**AI Errors**: Verify your Gemini API key is valid and has sufficient quota.

**SQL Execution Errors**: Ensure the role has SELECT permissions on the selected tables/views.

