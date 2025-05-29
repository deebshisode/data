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

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.