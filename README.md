# AIDBAnalysis

AIDBAnalysis is a FastAPI-based backend for AI-powered database analysis and business insights. It supports streaming responses (SSE), multiple database connections, and integration with OpenAI/Azure OpenAI for natural language analysis.

## Features

- FastAPI backend with async endpoints
- Supports Server-Sent Events (SSE) for real-time updates
- Connects to multiple SQL Server databases
- AI-powered SQL analysis and suggestions
- Custom JSON encoding for datetime, decimal, and binary data
- CORS support for frontend integration

## Requirements

- Python 3.8+
- pip

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/deebshisode/data.git
   cd data/AIDBAnalysis
   ```

2. **Create a virtual environment and activate it:**
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set environment variables for your database(s) and OpenAI keys as needed.**

5. **Run the FastAPI server:**
   ```sh
   uvicorn AnalyzeThis:app --reload
   ```

Note: pip install your dependencies individually (as needed) if not covered in requirements.txt

## Usage

- The main API endpoint is `/analyze` for streaming analysis.
- Configure your database connections in the code or via environment variables.
- Integrate with the React frontend for a complete solution.

## Project Structure

- `AnalyzeThis.py` — Main FastAPI application
- `requirements.txt` — Python dependencies

## Configuration

Before running the backend, you need to configure your database and Azure OpenAI settings.  
You can do this by setting environment variables or editing the configuration section in your code.

### Database Configuration

The backend uses the following configuration for connecting to SQL Server:

```python
DB_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",  # Update to your installed driver
    "server": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "AdventureWorksLT2022"),
    "user": os.getenv("DB_USER", "app_user"),
    "password": os.getenv("DB_PASSWORD", "app_password"),  # Replace with your database password
    "port": os.getenv("DB_PORT", "1433")
}

You can set these as environment variables in your shell or .env file:

export DB_HOST=localhost
export DB_NAME=AdventureWorksLT2022
export DB_USER=app_user
export DB_PASSWORD=your_db_password
export DB_PORT=1433

Azure OpenAI Configuration
Set the following environment variables for Azure OpenAI integration:

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "your-azure-openai-key")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-openai-endpoint.openai.azure.com/")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "your-deployment-name")
API_VERSION = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
```
# React Business Insights App

This project is a React-based web application that allows users to query business insights using natural language. The application communicates with a backend API to analyze data and display results in a user-friendly format.

## Features

- User-friendly form for inputting natural language queries.
- Displays formatted results from the analysis.
- Utilizes FastAPI for backend processing.

## Project Structure

```
react-business-insights-app
├── public
│   ├── index.html          # Main HTML file
├── src
│   ├── components
│   │   ├── AnalysisForm.jsx  # Component for user input
│   │   ├── ResultsDisplay.jsx # Component for displaying results
│   ├── services
│   │   └── api.js            # API service for making requests
│   ├── App.jsx               # Main application component
│   ├── index.js              # Entry point of the application
├── package.json              # Project metadata and dependencies
├── .gitignore                # Files to ignore in Git
├── README.md                 # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd react-business-insights-app
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Run the application:**
   ```
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000` to view the application.

## Usage

- Enter your business query in the input form and submit.
- The application will send the query to the `/analyze` endpoint and display the results.

## Technologies Used

- React
- FastAPI (for backend)
- Axios (for making HTTP requests)

## Running AdventureWorks SQL Server with Docker

To quickly set up a local SQL Server instance with the AdventureWorks sample database, you can use the following Docker image:

### 1. Pull and Run the Docker Image

```sh
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong!Passw0rd" \
   -p 1433:1433 --name sql1 \
   -d mcr.microsoft.com/mssql/server:2022-latest
```
2. Download and Restore the AdventureWorks Database

Download the AdventureWorks sample database .bak file from Microsoft's official GitHub.
Copy the .bak file into the running container:

```sh
docker cp AdventureWorksLT2022.bak sql1:/var/opt/mssql/data/
```

Connect to the SQL Server container:
```sh
docker exec -it sql1 /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'YourStrong!Passw0rd'
```
Restore the database
```sh
RESTORE DATABASE AdventureWorksLT2022
FROM DISK = '/var/opt/mssql/data/AdventureWorksLT2022.bak'
WITH MOVE 'AdventureWorksLT2022' TO '/var/opt/mssql/data/AdventureWorksLT2022.mdf',
     MOVE 'AdventureWorksLT2022_log' TO '/var/opt/mssql/data/AdventureWorksLT2022_log.ldf';
GO
```

3. Set your database connection variables to:

DB_HOST=localhost
DB_PORT=1433
DB_USER=SA
DB_PASSWORD=YourStrong!Passw0rd
DB_NAME=AdventureWorksLT2022

After everything is set and you start API server and Node server, it should show you the screens similar to this:

![Demo Screenshot](https://github.com/deebshisode/data/blob/main/images/Screen-1.png)

![Demo Screenshot](https://github.com/deebshisode/data/blob/main/images/Screen-2.png)

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.

## License

MIT License
