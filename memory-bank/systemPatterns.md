# System Patterns *Optional*

This file documents recurring patterns...

*
[2025-06-13 22:16:11] - ## Identified System Patterns

1. Agent Deployment Pattern
   ```python
   # Initialize Vertex AI
   vertexai.init(project=PROJECT_ID, location=LOCATION)
   
   # Create ADK App
   app = reasoning_engines.AdkApp(agent=root_agent)
   
   # Deploy to Agent Engine
   agent_engine = agent_engines.create(agent_engine=app)
   ```

2. Agent Tool Pattern
   ```python
   def tool_function(param: str) -> dict:
       # Implementation
       return {"status": "success", "report": result}
   
   agent = Agent(
       tools=[tool_function],
       model="gemini-2.5-flash-preview-05-20"
   )
   ```

3. Client Interaction Pattern
   ```python
   # Get agent and create session
   agent = agent_engines.get(AGENT_NAME)
   session = agent.create_session(user_id="test-user")
   
   # Stream responses
   responses = agent.stream_query(
       message=query,
       session_id=session["id"]
   )
   ```

[2025-06-13 23:06:30] - ## Client Interaction Pattern (Updated)

```python
# query.py - Client script for natural language queries

# ... (imports and configuration)

def query_agent(full_query: str):
    # ... (Vertex AI init, get agent, create session)
    return agent.stream_query(
        message=full_query, # Passes the full user query
        user_id='some-user-id',
        session_id=session['id']
    )

if __name__ == '__main__':
    user_query = sys.argv[1] # Takes full query from CLI
    responses = query_agent(user_query)
    # ... (process and print final text response)
```