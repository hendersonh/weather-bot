# Decision Log

This file records architectural and implementation decisions...

*
[2025-06-13 22:15:49] - ## 2025-06-13: Key Architecture Decisions

1. Package Structure
   - Created root_agent as a proper Python package
   - Keeps agent code and tools together
   - Makes code importable and maintainable

2. Agent Design
   - Used google.adk.agents.Agent class
   - Implemented two tools: get_weather and get_current_time
   - Selected gemini-2.5-flash-preview-05-20 model

3. Deployment Strategy
   - Using Vertex AI Agent Engine for deployment
   - Created AdkApp with root_agent
   - Maintained minimal required dependencies

4. Client Implementation
   - Separate query_weather.py script for interacting with deployed agent
   - Includes agent verification and session management
   - Uses stream_query for real-time responses

[2025-06-13 22:44:29] - ## Creating query.py

### Design Decisions:
1. Command-line Interface
   - Takes city name as argument
   - Simple usage: `python query.py CITYNAME`

2. Error Handling
   - Handle missing arguments
   - Catch and display connection errors
   - Handle agent query errors

3. Configuration
   - Hardcoded values from successful deployment:
     - PROJECT_ID: 'chatbot-8ebb8'
     - LOCATION: 'us-central1'
     - AGENT_NAME: projects/845122974817/locations/us-central1/reasoningEngines/6480583106762899456

4. Response Handling
   - Stream responses as they arrive
   - Print each response chunk
   - Clean error messages

[2025-06-13 23:06:25] - ## 2025-06-13: query.py Natural Language Input

### Decision:
- Modified `query.py` to accept a full natural language query string as a command-line argument instead of just a city name.

### Rationale:
- Allows for more flexible user input (e.g., "weather in toronto", "toronto's weather").
- Simplifies the client script by offloading query interpretation to the agent.
- Aligns with the agent's capability to understand natural language.

### Impact:
- `query_agent` function now takes `full_query` as input.
- Command-line usage changed to `python query.py "YOUR FULL QUERY"`.

## Plan: Refactor get_weather() to use OpenWeather API (2025-06-14)

[2025-06-14 16:36:22] - 
**Objective:**
Refactor the `get_weather(city: str)` function in `root_agent/agent.py` to fetch real-time weather data from the OpenWeather API, replacing the current hardcoded responses.

**I. Prerequisites & Setup:**

1.  **OpenWeather API Key:**
    *   Obtain a free API key from [OpenWeatherMap](https://openweathermap.org/appid).
2.  **API Endpoint:**
    *   The primary endpoint for current weather data is `http://api.openweathermap.org/data/2.5/weather`.
3.  **Dependency Installation:**
    *   Install the `requests` library for making HTTP calls: `pip install requests`
    *   Install `python-dotenv` for managing environment variables: `pip install python-dotenv`
4.  **Environment Variable for API Key:**
    *   Create a file named `.env` in the project root directory (e.g., alongside `root_agent/`) or within `root_agent/.env`.
    *   Add the API key to this file: `OPENWEATHER_API_KEY="YOUR_ACTUAL_API_KEY"`
    *   Ensure `.env` is listed in your `.gitignore` file to prevent committing the API key.
5.  **`requirements.txt`:**
    *   Add/update `requirements.txt` to include:
        ```
        requests
        python-dotenv
        ```

**II. Refactoring the `get_weather` function in `root_agent/agent.py`:**

1.  **Import necessary modules:**
    ```python
    import requests
    import os
    from dotenv import load_dotenv, find_dotenv
    ```
2.  **Load Environment Variables:**
    *   At the beginning of the script (or before the function definition), load the `.env` file:
        ```python
        load_dotenv(find_dotenv())
        ```
3.  **Function Implementation:**
    ```python
    def get_weather(city: str) -> dict:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "report": "OpenWeather API key not found. Please set OPENWEATHER_API_KEY environment variable."
            }

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"  # Or "imperial" for Fahrenheit
        }

        try:
            response = requests.get(base_url, params=params, timeout=10) # Added timeout
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            
            data = response.json()

            # OpenWeather API specific error checking (even if HTTP status is 200)
            if data.get("cod") != 200 and data.get("cod") != "200": # API can return cod as int or string
                error_message = data.get("message", "Unknown error from OpenWeather API.")
                return {"status": "error", "report": f"API Error for {city}: {error_message}"}

            weather_description = data.get("weather", [{}])[0].get("description", "not available")
            temperature = data.get("main", {}).get("temp", "not available")
            
            report = f"The weather in {city} is {weather_description} with a temperature of {temperature}°C." # Assuming metric
            return {"status": "success", "report": report}

        except requests.exceptions.HTTPError as http_err:
            # Handle HTTP errors (e.g., 401 Unauthorized, 404 Not Found from server)
            if response.status_code == 401:
                 return {"status": "error", "report": f"API Error for {city}: Invalid API key or unauthorized."}
            elif response.status_code == 404:
                 return {"status": "error", "report": f"API Error for {city}: City not found."}
            return {"status": "error", "report": f"HTTP error for {city}: {http_err}"}
        except requests.exceptions.ConnectionError as conn_err:
            return {"status": "error", "report": f"Connection error for {city}: {conn_err}"}
        except requests.exceptions.Timeout as timeout_err:
            return {"status": "error", "report": f"Request timed out for {city}: {timeout_err}"}
        except requests.exceptions.RequestException as req_err:
            return {"status": "error", "report": f"Error fetching weather for {city}: {req_err}"}
        except (KeyError, IndexError, TypeError) as json_err: # Catch errors from unexpected JSON structure
            return {"status": "error", "report": f"Error parsing weather data for {city}: {json_err}"}

    ```

**III. Error Handling (Covered in the function implementation above):**

*   Missing API key.
*   Network errors (connection, timeout).
*   HTTP errors from the API (e.g., 401, 404).
*   API-specific errors (e.g., city not found, invalid key, even with HTTP 200).
*   Errors parsing the JSON response (unexpected structure).

**IV. Testing Strategy:**

1.  **Create a Test File:**
    *   E.g., `test_agent.py` in the `root_agent` directory or a dedicated `tests` directory.
2.  **Write Unit Tests (using `unittest.mock`):**
    *   **Mock `requests.get`:** To simulate API responses without actual network calls.
    *   **Mock `os.getenv`:** To test scenarios with and without the API key.
    *   **Test Cases:**
        *   Successful API call and data parsing.
        *   API key missing.
        *   Invalid API key (simulated 401 response).
        *   City not found (simulated 404 response or API specific error code).
        *   Network connection error.
        *   Request timeout.
        *   Malformed/unexpected JSON response.
3.  **Example Test Structure (Conceptual):**
    ```python
    # In test_agent.py
    import unittest
    from unittest.mock import patch, Mock
    # from root_agent.agent import get_weather # Adjust import based on your structure

    class TestGetWeather(unittest.TestCase):
        @patch('root_agent.agent.os.getenv')
        @patch('root_agent.agent.requests.get')
        def test_get_weather_success(self, mock_get, mock_getenv):
            # Setup mock_getenv to return a dummy API key
            # Setup mock_get to return a Mock response object with a .json() method
            #   that returns sample successful OpenWeather data.
            # Call get_weather("TestCity")
            # Assert the result is as expected
            pass
        
        # ... more test cases for error conditions ...
    ```
4.  **Run Tests:**
    *   Use a test runner like `python -m unittest discover` or `pytest`.
5.  **Manual Integration Test (Optional):**
    *   After unit tests pass, run the agent with a real city and your actual API key to verify end-to-end functionality.

**V. Implementation Workflow Summary:**

1.  Perform all setup steps (API key, `.env`, dependencies).
2.  Implement the refactored `get_weather` function in `root_agent/agent.py` with comprehensive error handling.
3.  Write and run unit tests for the `get_weather` function.
4.  Optionally, perform a manual test.
