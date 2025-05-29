from fastapi import FastAPI, Request, Depends , Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncIterator
import pyodbc
from fastapi.responses import StreamingResponse
from typing import Dict, Callable
import asyncio
import json
import uuid
import os
import json
import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
import base64
from contextlib import asynccontextmanager
from collections import namedtuple
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# from openai import OpenAI
from openai import AzureOpenAI

# Custom JSON encoder to handle datetime objects, Decimal objects, and bytes objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super().default(obj)

# Custom JSONResponse that uses our encoder
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            cls=CustomJSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# SSE event helper function
def format_sse_event(data: Any) -> str:
    json_data = json.dumps(data, cls=CustomJSONEncoder)
    return f"data: {json_data}\n\n"

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Override default JSONResponse with our custom one
app.router.default_response_class = CustomJSONResponse

# Environment and API Configs
DB_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",  # Update to your installed driver
    "server": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "AdventureWorksLT2022"),
    "user": os.getenv("DB_USER", "app_user"),
    "password": os.getenv("DB_PASSWORD", "app_password"),
    "port": os.getenv("DB_PORT", "1433")
}

# Azure OpenAI Configuration
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "your_azure_openai_key_here")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-azure-openai-endpoint.openai.azure.com/")  # Ensure this ends with a slash
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "DataChat")  # This is the deployment name for your model
API_VERSION = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")  # Azure OpenAI API version

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
)

print(f"Azure OpenAI API configured with endpoint: {AZURE_OPENAI_ENDPOINT}")

# Cache for schema
schema_cache = None
schema_cache_time = None
SCHEMA_CACHE_TTL = timedelta(hours=1)

# Pydantic models
class AnalyzeThis(BaseModel):
    analysisGoal: str
    tables: Optional[List[str]] = None
    contextId: Optional[str] = None
    executeQueries: Optional[bool] = False

def create_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']},{DB_CONFIG['port']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return pyodbc.connect(conn_str)

@asynccontextmanager
async def get_db_pool():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()

async def get_db_schema(pool):
    global schema_cache, schema_cache_time
    now = datetime.utcnow()
    if schema_cache and schema_cache_time and now - schema_cache_time < SCHEMA_CACHE_TTL:
        return schema_cache

    cursor = pool.cursor()
    columns_query = """
    SELECT TABLE_NAME as table_name, COLUMN_NAME as column_name, 
    DATA_TYPE as data_type, IS_NULLABLE as is_nullable, 
    COLUMN_DEFAULT as column_default
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'SalesLT'  -- Replace with your schema name
    ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """
    fks_query = """
    SELECT
        tc.TABLE_NAME as table_name, kcu.COLUMN_NAME as column_name, 
        ccu.TABLE_NAME AS foreign_table_name, 
        ccu.COLUMN_NAME AS foreign_column_name
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu ON ccu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
    WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY';
    """
    cursor.execute(columns_query)
    columns = cursor.fetchall()
    cursor.execute(fks_query)
    fks = cursor.fetchall()
    # Define namedtuples for better readability
    Column = namedtuple("Column", ["table_name", "column_name", "data_type", "is_nullable", "column_default"])
    ForeignKey = namedtuple("ForeignKey", ["table_name", "column_name", "foreign_table_name", "foreign_column_name"])

    # Convert raw database rows into namedtuples
    columns = [Column(*row) for row in columns]
    fks = [ForeignKey(*row) for row in fks]
    # # Log columns and foreign keys for debugging
    # print("Columns fetched from database:")

    schema = {}
    for row in columns:
        table = row.table_name
        if table not in schema:
            schema[table] = {"columns": [], "relationships": []}
        schema[table]["columns"].append({
            "name": row.column_name,
            "type": row.data_type,
            "nullable": row.is_nullable == 'YES',
            "default": row.column_default
        })

    for fk in fks:
        table = fk.table_name
        if table in schema:
            schema[table]["relationships"].append({
                "column": fk.column_name,
                "references": {
                    "table": fk.foreign_table_name,
                    "column": fk.foreign_column_name
                }
            })
    # # Log the schema for debugging
    # print("Schema constructed from database:")
    # for table, details in schema.items():
    #     print(f"Table: {table}")
    #     print("Columns:")
    #     for column in details["columns"]:
    #         print(f"  - {column}")
    #     print("Relationships:")
    #     for relationship in details["relationships"]:
    #         print(f"  - {relationship}")
    schema_cache = schema
    schema_cache_time = now
    cursor.close()
    return schema

async def sample_table_data(pool, table_name, limit=5):
    try:
        cursor = pool.cursor()
        query = f'SELECT TOP {limit} * FROM {table_name}'
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        # Convert rows to dictionaries and handle datetime objects
        result = []
        for row in rows:
            row_dict = {}
            for i, val in enumerate(row):
                # Convert datetime objects to ISO format strings
                if isinstance(val, (datetime, date)):
                    row_dict[columns[i]] = val.isoformat()
                else:
                    row_dict[columns[i]] = val
            result.append(row_dict)
        return result
    except Exception as e:
        return []

def generate_prompt(goal: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
    print("Generating prompt for AI with the following context:")
    print("Goal:", goal)
    print("Schema:", json.dumps(context['schema'], indent=2))
    print("Samples:", json.dumps(context['samples'], indent=2, cls=CustomJSONEncoder))
    
    return [
        {
            "role": "system",
            "content": f"""You are a data analysis assistant with SQL expertise.

The database schema is:
{json.dumps(context['schema'], indent=2)}

Here are sample rows:
{json.dumps(context['samples'], indent=2, cls=CustomJSONEncoder)}

Return:
1. Summary of structure related to goal
2. 2 SQL queries to achieve goal
3. Explanation for each query
4. queries should use Microsoft T-SQL syntax
5. Use SalesLT Database schema
6. Observations on data quality"""
        },
        {
            "role": "user",
            "content": f"Please analyze the data with this goal: \"{goal}\""
        }
    ]

async def call_openai(messages):
    try:
        # Azure OpenAI API call - we need to include the model parameter
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,  # For Azure, we still need to provide the model/deployment name
            messages=messages,
            temperature=0.2,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI API Error details: {str(e)}")
        return f"AI API Error: {str(e)}"

def extract_sql_queries(ai_response: str) -> List[str]:
    import re 
    from collections import namedtuple
    matches = re.findall(r"```sql\s*(.*?)\s*```", ai_response, re.DOTALL)
    return [m.strip() for m in matches if m.strip()]

# Add a default analysis request for GET requests
DEFAULT_ANALYSIS = {
    "analysisGoal": "Find the top 5 customers by order value",
    "tables": ["Customer", "SalesOrderHeader", "SalesOrderDetail"],
    "executeQueries": True
}

# Support GET method for the SSE endpoint
@app.get("/analyze/sse")
async def analyze_sse_get(request: Request):
    return await _analyze_sse_handler(AnalyzeThis(**DEFAULT_ANALYSIS))

# Support POST method for the SSE endpoint
@app.post("/analyze/sse")
async def analyze_sse_post(request: AnalyzeThis):
    return await _analyze_sse_handler(request)

# Common handler function for both GET and POST
async def _analyze_sse_handler(analyze_request: AnalyzeThis):
    async def event_generator() -> AsyncIterator[str]:
        # Send initial state event
        yield format_sse_event({
            "type": "state",
            "data": {
                "state": "running",
                "message": f"Starting analysis for goal: {analyze_request.analysisGoal}"
            }
        })
        
        try:
            async with get_db_pool() as pool:
                # Send schema loading event
                yield format_sse_event({
                    "type": "state",
                    "data": {
                        "state": "running",
                        "message": "Loading database schema..."
                    }
                })
                
                schema = await get_db_schema(pool)
                tables_to_analyze = analyze_request.tables if analyze_request.tables else list(schema.keys())
                context = {"schema": {}, "samples": {}}
                
                # Send tables loading event
                yield format_sse_event({
                    "type": "state",
                    "data": {
                        "state": "running",
                        "message": f"Loading sample data from tables: {', '.join(tables_to_analyze)}"
                    }
                })
                
                for table in tables_to_analyze:
                    if table in schema:
                        context["schema"][table] = schema[table]
                        context["samples"][table] = await sample_table_data(pool, table)
                
                # Send AI analysis event
                yield format_sse_event({
                    "type": "state",
                    "data": {
                        "state": "running",
                        "message": "Analyzing data with AI..."
                    }
                })
                
                messages = generate_prompt(analyze_request.analysisGoal, context)
                print("Generated messages for AI:", context.get("samples"))
                ai_response = await call_openai(messages)
                sql_queries = extract_sql_queries(ai_response)
                
                # Send the AI analysis result
                yield format_sse_event({
                    "type": "analysis",
                    "data": {
                        "goal": analyze_request.analysisGoal,
                        "aiSuggestions": ai_response,
                        "suggestedQueries": sql_queries
                    }
                })
                
                # Execute queries if requested
                query_results = {}
                if analyze_request.executeQueries and sql_queries:
                    yield format_sse_event({
                        "type": "state",
                        "data": {
                            "state": "running",
                            "message": "Executing SQL queries..."
                        }
                    })
                    
                    for i, query in enumerate(sql_queries):
                        try:
                            cursor = pool.cursor()
                            cursor.execute(query)
                            columns = [column[0] for column in cursor.description] if cursor.description else []
                            result = cursor.fetchall()
                            cursor.close()
                            
                            # Process results to handle datetime objects
                            processed_results = []
                            for row in result:
                                row_dict = {}
                                for j, val in enumerate(row):
                                    # Convert datetime objects to ISO format strings
                                    if isinstance(val, (datetime, date)):
                                        row_dict[columns[j]] = val.isoformat()
                                    else:
                                        row_dict[columns[j]] = val
                                processed_results.append(row_dict)
                            
                            query_results[f"query_{i+1}"] = {
                                "sql": query,
                                "results": processed_results
                            }
                            
                            # Send each query result as it completes
                            yield format_sse_event({
                                "type": "queryResult",
                                "data": {
                                    "queryIndex": i + 1,
                                    "sql": query,
                                    "results": processed_results
                                }
                            })
                            
                        except Exception as e:
                            query_results[f"query_{i+1}"] = {
                                "sql": query,
                                "error": str(e)
                            }
                            
                            # Send error for this query
                            yield format_sse_event({
                                "type": "queryError",
                                "data": {
                                    "queryIndex": i + 1,
                                    "sql": query,
                                    "error": str(e)
                                }
                            })
                
                # Send final completion event
                yield format_sse_event({
                    "type": "state",
                    "data": {
                        "state": "complete",
                        "message": "Analysis completed successfully"
                    }
                })
                
                # Send the full results at the end
                yield format_sse_event({
                    "type": "result",
                    "data": {
                        "status": "success",
                        "analysis": {
                            "goal": analyze_request.analysisGoal,
                            "aiSuggestions": ai_response,
                            "suggestedQueries": sql_queries,
                            "results": query_results
                        },
                        "context": {
                            "contextId": analyze_request.contextId,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                })
                
        except Exception as e:
            # Send error event if anything fails
            yield format_sse_event({
                "type": "error",
                "data": {
                    "message": f"Error during analysis: {str(e)}"
                }
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
        }
    )

# Keep the original endpoint for backward compatibility
@app.post("/analyze")
async def analyze(request: AnalyzeThis):
    print("Test message: Starting analysis process...1")
    print("Database Configuration:", DB_CONFIG)
    async with get_db_pool() as pool:
        schema = await get_db_schema(pool)  # Fetch schema details
        print("Test message: Starting analysis process...2", schema)
        # Use the provided tables or all tables in the schema
        tables_to_analyze = [f"{table}" for table in (request.tables if request.tables else list(schema.keys()))]
        print("Tables to analyze:", tables_to_analyze)
        context = {"schema": {}, "samples": {}}
        for table in tables_to_analyze:
            if table in schema:
                context["schema"][table] = schema[table]
                print(f"Fetching sample data for table: {table}")
                context["samples"][table] = await sample_table_data(pool, table)
                await asyncio.sleep(0.1)  # Wait for the sample_table_data call to complete
        print("Test message: Starting analysis process...3")
        messages = generate_prompt(request.analysisGoal, context)
        ai_response = await call_openai(messages)
        # Prepend "SalesLT." schema to table names in the extracted SQL queries
        sql_queries = [
            query.replace("FROM ", "FROM SalesLT.") if "FROM SalesLT." not in query else query
            for query in extract_sql_queries(ai_response)
        ]
        print("Test message: Starting analysis process...4")

        query_results = {}
        if request.executeQueries:
            for i, query in enumerate(sql_queries):
                try:
                    cursor = pool.cursor()
                    cursor.execute(query)
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    result = cursor.fetchall()
                    cursor.close()
                    
                    # Process results to handle datetime objects
                    processed_results = []
                    for row in result:
                        row_dict = {}
                        for j, val in enumerate(row):
                            # Convert datetime objects to ISO format strings
                            if isinstance(val, (datetime, date)):
                                row_dict[columns[j]] = val.isoformat()
                            else:
                                row_dict[columns[j]] = val
                        processed_results.append(row_dict)
                    
                    query_results[f"query_{i+1}"] = {
                        "sql": query,
                        "results": processed_results
                    }
                except Exception as e:
                    query_results[f"query_{i+1}"] = {
                        "sql": query,
                        "error": str(e)
                    }

    # Include schema details in the response
    return {
        "status": "success",
        "analysis": {
            "goal": request.analysisGoal,
            "aiSuggestions": ai_response,
            "suggestedQueries": sql_queries,
            "results": query_results
        },
        "schema": schema,  # Add schema details here
        "context": {
            "contextId": request.contextId,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

POST_ENDPOINT = "/send"  # Placeholder, customize as needed
transports: Dict[str, Callable] = {}

class SSEServerTransport:
    def __init__(self, endpoint: str, response: Response):
        self.endpoint = endpoint
        self.response = response
        self.session_id = str(uuid.uuid4())
        self.queue = asyncio.Queue()

    @property
    def sessionId(self):
        return self.session_id

    async def send(self, message: dict):
        await self.queue.put(f"data: {json.dumps(message)}\n\n")

    async def event_stream(self):
        try:
            while True:
                data = await self.queue.get()
                yield data
        except asyncio.CancelledError:
            print(f"Transport {self.session_id} cancelled")

@app.get("/connect")
async def connect(request: Request):
    print("connection request received")
    transport = SSEServerTransport(POST_ENDPOINT, Response)
    print("new transport created with session id:", transport.sessionId)
    transports[transport.sessionId] = transport

    async def stream_generator():
        await send_messages(transport)
        async for data in transport.event_stream():
            yield data

    async def cleanup():
        print("SSE connection closed")
        transports.pop(transport.sessionId, None)

    # Clean up when client disconnects
    def on_disconnect():
        asyncio.create_task(cleanup())

    request.state._on_disconnect = on_disconnect

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

async def send_messages(transport: SSEServerTransport):
    try:
        await transport.send({
            "jsonrpc": "2.0",
            "method": "sse/connection",
            "params": {"message": "Stream started"}
        })
        print("Stream started")

        message_count = 0

        while message_count < 2:
            await asyncio.sleep(1)
            message_count += 1
            message = f"Message {message_count} at {datetime.utcnow().isoformat()}"

            try:
                await transport.send({
                    "jsonrpc": "2.0",
                    "method": "sse/message",
                    "params": {"data": message}
                })
                print(f"Sent: {message}")
            except Exception as e:
                print("Error sending message:", e)
                break

        await transport.send({
            "jsonrpc": "2.0",
            "method": "sse/complete",
            "params": {"message": "Stream completed"}
        })
        print("Stream completed")

    except Exception as e:
        print("Error in send_messages:", e)
