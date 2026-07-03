import asyncio
from dotenv import load_dotenv
load_dotenv()
from google.adk.agents import LlmAgent, Context
from google.adk.sessions import Session
from google.adk.tools import FunctionTool

# ------------------------------------------------------------------------------
# 1. Handling PII data with Implicit Context
# ------------------------------------------------------------------------------
# Mock Database that stores PII data keyed by the session ID. 
# By using implicit context, we ensure PII like email and SSN never needs to
# be passed back and forth in the LLM's prompt. The tools access it securely
# via the session context on the backend.
PII_DB = {
    "session-user-123": {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "account_balance": "$12,500"
    }
}

# The tool accepts the `context` parameter implicitly provided by the ADK.
# This avoids the agent needing to "ask" for a session ID.
def get_account_details(context: Context) -> str:
    """Retrieve the account details of the current user based on their session."""
    session_id = context.session.id
    if session_id in PII_DB:
        user_info = PII_DB[session_id]
        return f"Found account for {user_info['name']}. Email: {user_info['email']}, Balance: {user_info['account_balance']}"
    return "User account details not found for this session."

# Define the tool
account_tool = FunctionTool(get_account_details)


# ------------------------------------------------------------------------------
# 2. Define the Agent using OpenRouter (via LiteLLM)
# ------------------------------------------------------------------------------
# We import LiteLlm which allows us to use any provider, including OpenRouter.
# Note: You need to set `OPENROUTER_API_KEY` in your environment.
from google.adk.models.lite_llm import LiteLlm

# Use 'openrouter/auto' which automatically routes to a free or default model
openrouter_model = LiteLlm(model="openrouter/auto")

pii_agent = LlmAgent(
    model=openrouter_model,
    name="SecureAccountAgent",
    instruction=(
        "You are a helpful banking assistant. When asked for account details, "
        "use the `get_account_details` tool to fetch them. Never ask the user "
        "for their session ID, ID number, or PII. Provide a polite summary of the details."
    ),
    tools=[account_tool]
)


async def main():
    print("Starting Google ADK Agent Example with Rehydration and Implicit Context...\n")

    # ------------------------------------------------------------------------------
    # 3. Agent Rehydration
    # ------------------------------------------------------------------------------
    # In a real-world scenario, you would rehydrate the session from a database
    # e.g., session = await session_service.load("session-user-123")
    # This restores the memory/state without losing context between requests.
    session_id = "session-user-123"
    print(f"[*] Rehydrating session: {session_id}")
    
    # Create or Rehydrate the session instance
    session = Session(id=session_id, appName="banking-app", userId="user-123")
    
    # Establish the Implicit Context using the rehydrated session
    from google.adk.agents import InvocationContext
    from google.adk.sessions import BaseSessionService
    
    class DummySessionService(BaseSessionService):
        async def load(self, session_id): pass
        async def save(self, session): pass
        async def create_session(self, **kwargs): pass
        async def delete_session(self, **kwargs): pass
        async def get_session(self, **kwargs): pass
        async def list_sessions(self, **kwargs): pass
        
    mock_session_service = DummySessionService()
    
    from google.adk.agents.run_config import RunConfig
    
    inv_context = InvocationContext(
        session=session,
        session_service=mock_session_service,
        invocation_id="test-inv-123",
        run_config=RunConfig()
    )
    context = Context(invocation_context=inv_context)
    
    user_prompt = "Can you tell me my current account balance and email address?"
    print(f"[*] User Request: '{user_prompt}'")
    print("[*] Running Agent...\n")

    # Run the agent, passing the implicit context
    # The agent uses the tool, which pulls the PII from the DB using context.session.id
    response_stream = pii_agent.run(
        ctx=context,
        node_input=user_prompt
    )
    
    print("--------------------------------------------------")
    print("Agent Response:")
    print("--------------------------------------------------")
    async for event in response_stream:
        if hasattr(event, 'content'):
            print(event.content)
        else:
            print(event)


if __name__ == "__main__":
    asyncio.run(main())
