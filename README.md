# AI Data Analyst

An intelligent data analysis workspace that connects to Snowflake databases and enables natural language querying with automated visualization generation.

## Features

- **Snowflake Integration**: Secure SSO authentication with Snowflake data warehouses
- **Natural Language to SQL**: Uses Google Gemini AI to translate natural language queries into optimized SQL
- **Dynamic Visualization**: Automatically generates interactive charts (line, bar) using ECharts
- **Semantic Understanding**: AI analyzes table schemas and sample data to understand business context
- **Multi-Chart Analysis**: Can generate multiple visualizations from a single query
- **Business Insights**: AI-generated executive summaries of analysis results

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Snowflake Connector**: Python driver for Snowflake
- **Google Generative AI**: Gemini 2.5 Flash for AI processing
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

Edit `backend/sql_builder.py` to configure warehouse and role:
```python
cursor.execute('USE ROLE "YOUR_ROLE"')
cursor.execute('USE WAREHOUSE "YOUR_WAREHOUSE"')
```

Edit `backend/snowflake_db.py` to set default warehouse and role:
```python
warehouse='YOUR_WAREHOUSE',
role='YOUR_ROLE'
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
├── .env                     # Environment variables
├── pyproject.toml           # Python dependencies
└── README.md                # This file
```

## How It Works

1. **Connection**: User authenticates via Snowflake SSO
2. **Schema Analysis**: Selected tables are analyzed for:
   - Column definitions and types
   - Sample data rows
   - Primary/foreign key relationships
   - Metrics vs dimensions classification
3. **Semantic Artifact**: AI generates a "golden artifact" understanding the business context
4. **Query Processing**:
   - User submits natural language query
   - AI parses intent and identifies required metrics/dimensions
   - AI generates optimized SQL queries with proper aggregation
   - Multiple charts can be generated for different analytical angles
5. **Visualization**: Results are rendered as interactive charts with SQL transparency

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

## License

[Add your license here]
