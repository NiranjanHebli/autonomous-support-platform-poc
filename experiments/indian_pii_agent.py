import asyncio
import re
import functools
import inspect
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent, Context
from google.adk.sessions import Session
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

# ------------------------------------------------------------------------------
# 1. PII Registry and Anonymization Engine
# ------------------------------------------------------------------------------

class PIIRegistry:
    def __init__(self):
        self.placeholder_to_real = {}
        self.real_to_placeholder = {}
        self.counters = {}

    def get_placeholder(self, pii_type: str, real_value: str) -> str:
        # Normalize whitespace in real value to ensure consistent matching
        norm_value = " ".join(real_value.split())
        
        if norm_value in self.real_to_placeholder:
            return self.real_to_placeholder[norm_value]
        
        count = self.counters.get(pii_type, 0) + 1
        self.counters[pii_type] = count
        
        placeholder = f"[{pii_type.upper()}_{count}]"
        self.placeholder_to_real[placeholder] = norm_value
        self.real_to_placeholder[norm_value] = placeholder
        return placeholder

    def clear(self):
        self.placeholder_to_real.clear()
        self.real_to_placeholder.clear()
        self.counters.clear()


# Curated regexes tailored for Indian PII details
PII_PATTERNS = {
    # 1. Government IDs (Aadhaar, PAN)
    "aadhaar": r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    
    # 2. Financial Details (Bank Account Numbers: 13-18 digits to avoid Aadhaar clash)
    "bank_account": r"\b\d{13,18}\b",
    "upi": r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b",
    
    # 3. Contact Details (Indian Mobile numbers starting with 6-9, Pin codes, Emails)
    "phone": r"\+91[\-\s]?[6-9]\d{9}\b|\b[6-9]\d{9}\b",
    "pincode": r"\b[1-9]\d{5}\b",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    
    # 4. Social Links (LinkedIn, Twitter/X)
    "social_link": r"\b(?:https?://)?(?:www\.)?(?:linkedin\.com/in/|twitter\.com/|instagram\.com/|github\.com/)[a-zA-Z0-9_\-\./]+",
    
    # 5. Names & Job Details (Curated list for deterministic POC demonstration)
    "job_detail": r"\b(?:Software Engineer at Infosys|Manager at ICICI Bank|Software Engineer|Manager|Data Analyst|Senior Developer|Consultant|Developer|Engineer)\b",
    "name": r"\b(?:Priya Patel|Rohan Sharma|Amit Kumar|Ananya Iyer|Vikram Singh|Priya|Rohan|Amit|Ananya|Vikram|Sharma|Patel|Kumar|Iyer|Singh)\b",
}


def anonymize(text: str, registry: PIIRegistry) -> str:
    if not text:
        return text
    
    matches = []
    
    # Scan for all matches across all PII patterns
    for pii_type, pattern in PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            matches.append((match.start(), match.end(), pii_type, match.group()))
            
    # De-duplicate and resolve overlapping matches by prioritizing longer matches first
    matches.sort(key=lambda x: (x[0], -x[1]))
    
    filtered_matches = []
    last_end = -1
    for start, end, pii_type, value in matches:
        if start >= last_end:
            filtered_matches.append((start, end, pii_type, value))
            last_end = end
            
    # Print diagnostics for matched PII
    if filtered_matches:
        print("[PII Detection Diagnostics]")
        for start, end, pii_type, value in filtered_matches:
            print(f"  -> Detected {pii_type.upper()}: '{value}' at [{start}:{end}]")
            
    # Replace PII from right to left to avoid changing string offsets during execution
    filtered_matches.sort(key=lambda x: x[0], reverse=True)
    
    result = text
    for start, end, pii_type, value in filtered_matches:
        placeholder = registry.get_placeholder(pii_type, value)
        result = result[:start] + placeholder + result[end:]
        
    return result


def deanonymize(text: str, registry: PIIRegistry) -> str:
    if not text:
        return text
    result = text
    # Sort placeholders by length descending to prevent substring replacing bugs (e.g. replacing NAME_10 before NAME_1)
    placeholders = sorted(registry.placeholder_to_real.keys(), key=len, reverse=True)
    for placeholder in placeholders:
        real_value = registry.placeholder_to_real[placeholder]
        result = result.replace(placeholder, real_value)
    return result


# ------------------------------------------------------------------------------
# 2. Tool Wrappers for Parameter Resolution & Output Sanitization
# ------------------------------------------------------------------------------

def pii_tool_wrapper(func, registry: PIIRegistry):
    """
    Decorator/wrapper that intercepts LLM tool call:
    1. Unmasks (de-anonymizes) tool arguments containing placeholders.
    2. Runs the underlying tool with real PII data.
    3. Masks (anonymizes) the tool's response before sending it back to the LLM.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        # 1. Unmask positional and keyword arguments
        clean_args = [
            deanonymize(arg, registry) if isinstance(arg, str) else arg 
            for arg in args
        ]
        clean_kwargs = {
            k: (deanonymize(v, registry) if isinstance(v, str) else v)
            for k, v in kwargs.items()
        }
        
        # Log intercepted arguments
        print(f"\n[Tool Interceptor - Input]")
        print(f"  -> Original arguments from LLM: args={args}, kwargs={kwargs}")
        print(f"  -> Resolved real-world PII arguments: args={clean_args}, kwargs={clean_kwargs}")
        
        # 2. Execute original tool
        result = func(*clean_args, **clean_kwargs)
        
        # 3. Mask the output
        print(f"[Tool Interceptor - Output]")
        print(f"  -> Raw tool output (contains PII): {result}")
        masked_result = anonymize(result, registry)
        print(f"  -> Masked tool output (sent to LLM): {masked_result}\n")
        
        return masked_result
        
    return wrapped


# ------------------------------------------------------------------------------
# 3. Define Rule-Based Dummy Tools
# ------------------------------------------------------------------------------

def check_loan_status(aadhaar_or_pan: str, phone: str) -> str:
    """
    Retrieve the status of a loan application using Aadhaar/PAN and phone number.
    
    Parameters:
    - aadhaar_or_pan: The customer's Aadhaar or PAN card number.
    - phone: The customer's registered phone number.
    """
    # Simulate database lookup based on incoming real PII
    norm_phone = "".join(filter(str.isdigit, phone))
    
    # Priya Patel's record
    if "9876543210" in norm_phone:
        return (
            "Loan application status for Priya Patel (Software Engineer at Infosys) is APPROVED. "
            "Verified Aadhaar: 2345 6789 0123. PAN: ABCDE1234F. PIN Code: 560001. "
            "UPI ID: priya@okaxis. Bank Account: 12345678901234. "
            "Verification link was sent to linkedin.com/in/priyapatel."
        )
    # Rohan Sharma's record
    elif "8765432109" in norm_phone:
        return (
            "Loan application status for Rohan Sharma (Manager at ICICI Bank) is PENDING. "
            "Verified Aadhaar: 9876 5432 1098. PAN: WXYZ9876A. PIN Code: 110011. "
            "UPI ID: rohan.sharma@upi. Bank Account: 98765432109876. "
            "Verification link was sent to twitter.com/rohansharma."
        )
    else:
        return f"No loan application found for Aadhaar/PAN: {aadhaar_or_pan} and Phone: {phone}."


def update_profile_contact(name: str, pin_code: str, social_link: str, upi_id: str, bank_account: str) -> str:
    """
    Update profile contact, pincode, social links, upi ID, and bank account information.
    
    Parameters:
    - name: Customer's full name.
    - pin_code: 6-digit PIN code.
    - social_link: Social media profile link (LinkedIn or Twitter).
    - upi_id: Customer's UPI address.
    - bank_account: Customer's bank account number.
    """
    return (
        f"Success! Updated records for {name}. "
        f"PIN Code: {pin_code}, Social Link: {social_link}, UPI ID: {upi_id}, Bank Account: {bank_account}."
    )


# ------------------------------------------------------------------------------
# 4. Agent Initialization with Debug Model Subclass
# ------------------------------------------------------------------------------

class DebugLiteLlm(LiteLlm):
    async def generate_content_async(self, llm_request, stream=False):
        print(f"\n[DebugLiteLlm - generate_content_async]")
        print(f"  -> Model: {llm_request.model or self.model}")
        
        # Call Stack Inspection to find InvocationContext and print its events
        frame = inspect.currentframe()
        session_obj = None
        while frame:
            if 'invocation_context' in frame.f_locals:
                ctx = frame.f_locals['invocation_context']
                session_obj = ctx.session
                break
            frame = frame.f_back
            
        if session_obj:
            print(f"  -> Session Events in Context: {len(session_obj.events)}")
            for idx, event in enumerate(session_obj.events):
                print(f"     Event {idx}: author='{event.author}', role='{getattr(event, 'role', None)}', type='{getattr(event, 'type', None)}'")
                # Print details of the content/parts in events
                if hasattr(event, 'content') and event.content:
                    for p_idx, part in enumerate(event.content.parts):
                        if part.text:
                            print(f"       Part {p_idx} (text): {part.text[:80]}...")
                        if part.function_call:
                            print(f"       Part {p_idx} (fc): name='{part.function_call.name}', args={part.function_call.args}")
                        if part.function_response:
                            print(f"       Part {p_idx} (fr): name='{part.function_response.name}', response={part.function_response.response}")
        else:
            print("  -> Session object NOT found in call stack!")

        print(f"  -> Number of messages in LlmRequest.contents: {len(llm_request.contents) if llm_request.contents else 0}")
        if llm_request.contents:
            for idx, content in enumerate(llm_request.contents):
                print(f"     Message {idx}: role='{content.role}'")
                for p_idx, part in enumerate(content.parts):
                    if part.text:
                        print(f"       Part {p_idx} (text): {part.text[:120]}...")
                    if part.function_call:
                        print(f"       Part {p_idx} (function_call): name='{part.function_call.name}', args={part.function_call.args}")
                    if part.function_response:
                        print(f"       Part {p_idx} (function_response): name='{part.function_response.name}', response={part.function_response.response}")
        
        async for response in super().generate_content_async(llm_request, stream):
            yield response


# Shared conversation PII Registry
session_registry = PIIRegistry()

# Register wrapped tools
wrapped_loan_tool = FunctionTool(pii_tool_wrapper(check_loan_status, session_registry))
wrapped_update_tool = FunctionTool(pii_tool_wrapper(update_profile_contact, session_registry))

# Initialize Debug Model via OpenRouter (using GPT-4o-mini for robust OpenAI-compatible tool support)
openrouter_model = DebugLiteLlm(model="openrouter/openai/gpt-4o-mini", max_tokens=1000)

pii_sanitized_agent = LlmAgent(
    model=openrouter_model,
    name="SecureIndianSupportAgent",
    instruction=(
        "You are a customer service assistant for an Indian bank. "
        "Your task is to assist customers with checking their loan status or updating contact details. "
        "Use the tools provided. When calling tools, pass the EXACT placeholders (like [NAME_1], [PHONE_1], [AADHAAR_1]) "
        "that you see in the customer message as arguments. Do not attempt to guess or ask for the real values. "
        "Once a tool returns a response, summarize the response to the user. Do not call the tool again once it returns a result."
    ),
    tools=[wrapped_loan_tool, wrapped_update_tool]
)


# ------------------------------------------------------------------------------
# 5. Execution Pipeline
# ------------------------------------------------------------------------------

async def process_customer_query(raw_query: str):
    print("=" * 80)
    print(f"[STAGE 1] Raw Customer Query (contains PII):")
    print(f"  -> \"{raw_query}\"")
    
    # Mask prompt before sending it to the LLM
    print()
    masked_query = anonymize(raw_query, session_registry)
    print(f"\n[STAGE 2] Masked Query Sent to LLM:")
    print(f"  -> \"{masked_query}\"")
    
    # Establish Session context
    session = Session(id="session-ind-999", appName="secure-bank-app", userId="user-ind-999")
    
    # Set up a functional In-Memory Session Service so that conversation events
    # (tool calls and responses) survive reloads during the agent's execution loop.
    from google.adk.agents import InvocationContext
    from google.adk.sessions import BaseSessionService
    from google.adk.agents.run_config import RunConfig
    
    class InMemorySessionService(BaseSessionService):
        def __init__(self):
            self.sessions = {}
        async def load(self, session_id):
            return self.sessions.get(session_id)
        async def save(self, session):
            self.sessions[session.id] = session
        async def create_session(self, **kwargs):
            session_id = kwargs.get("id") or "session-default"
            session = Session(id=session_id, **kwargs)
            self.sessions[session_id] = session
            return session
        async def delete_session(self, **kwargs): pass
        async def get_session(self, **kwargs):
            return self.sessions.get(kwargs.get("session_id"))
        async def list_sessions(self, **kwargs):
            return list(self.sessions.values())

    mock_session_service = InMemorySessionService()
    await mock_session_service.save(session)

    inv_context = InvocationContext(
        session=session,
        session_service=mock_session_service,
        invocation_id="test-inv-pii",
        run_config=RunConfig(max_llm_calls=5)
    )
    context = Context(invocation_context=inv_context)

    print(f"\n[STAGE 3] Running Agent (LLM sees only placeholders)...")
    
    response_stream = pii_sanitized_agent.run(
        ctx=context,
        node_input=masked_query
    )
    
    # Collect completion response
    llm_output_parts = []
    async for event in response_stream:
        # Save event to session so the history is preserved for tool-use loops
        session.events.append(event)
        
        if hasattr(event, 'content'):
            text_chunk = ""
            # Handle types.Content structure
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text_chunk += part.text
            elif isinstance(event.content, str):
                text_chunk = event.content
            
            if text_chunk:
                print(text_chunk, end="", flush=True)
                llm_output_parts.append(text_chunk)
    print()  # newline
    
    full_llm_response = "".join(llm_output_parts)
    
    # De-anonymize response for the user
    final_user_response = deanonymize(full_llm_response, session_registry)
    print(f"\n[STAGE 4] Final De-Anonymized Response Shown to User:")
    print(f"  -> \"{final_user_response}\"")
    print("=" * 80)
    print("\n")


# ------------------------------------------------------------------------------
# 6. Test Runner with Dummy Customer Queries
# ------------------------------------------------------------------------------

async def main():
    print("Starting Indian PII Masking Customer Service Agent Demo...\n")
    
    # Query 1: Priya Patel checking loan status
    query_priya = (
        "Hi, I am Priya Patel (Software Engineer at Infosys). I submitted a loan application last week. "
        "My Aadhaar number is 2345 6789 0123, PAN is ABCDE1234F. My phone number is +91-9876543210. "
        "Can you check my loan status? My pin code is 560001. Here is my LinkedIn: linkedin.com/in/priyapatel. "
        "Also my UPI ID is priya@okaxis."
    )
    await process_customer_query(query_priya)
    
    # Query 2: Rohan Sharma updating profile contact
    query_rohan = (
        "Hello, this is Rohan Sharma. I need to update my contact information on my ICICI Bank profile. "
        "I am a Manager at ICICI Bank, phone +91 8765432109, bank account number 98765432109876. "
        "My new PIN code is 110011, my UPI ID is rohan.sharma@upi and my twitter profile link is twitter.com/rohansharma. "
        "Can you verify and update this?"
    )
    await process_customer_query(query_rohan)


if __name__ == "__main__":
    asyncio.run(main())
