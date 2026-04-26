from datetime import datetime
from uuid import uuid4
import os
import requests

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
   ChatAcknowledgement,
   ChatMessage,
   EndSessionContent,
   StartSessionContent,
   TextContent,
   chat_protocol_spec,
)

# Replace this with your own seed or use environment variable
SEED = os.getenv("AGENT_SEED", "superblock-asi1-skill-agent-seed-v1")
PORT = 8003

agent = Agent(
    name="superblock-city-planner",
    seed=SEED,
    port=PORT,
    endpoint=[f"http://127.0.0.1:{PORT}/submit"]
)

# Initialize the chat protocol with the standard chat spec
chat_proto = Protocol(spec=chat_protocol_spec)

# Utility function to wrap plain text into a ChatMessage
def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

def query_backend_orchestration() -> str:
    """Queries the FastAPI backend to get the latest city intervention plan."""
    try:
        # Calls the backend to orchestrate the AI agents (diagnosis -> simulation -> planning)
        response = requests.post("http://127.0.0.1:8000/agents/orchestrate", json={}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            narrative = data.get("narrative", "")
            if not narrative:
                # Fallback if narrative is missing
                plan = data.get("plan", {})
                best = plan.get("best_intervention", "Unknown")
                reason = plan.get("reasoning", "No reason provided")
                narrative = f"Based on the latest data, the recommended intervention is {best}. Reasoning: {reason}"
            return narrative
        else:
            return "I'm having trouble connecting to the Superblock city intelligence backend."
    except Exception as e:
        return f"Error analyzing city data: {str(e)}"

# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
   ctx.logger.info(f"Received message from {sender}")
   
   # Always send back an acknowledgement when a message is received
   await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

   # Process each content item inside the chat message
   for item in msg.content:
       if isinstance(item, StartSessionContent):
           ctx.logger.info(f"Session started with {sender}")
           welcome_msg = create_text_chat("Hello! I am the Superblock City Planner agent. I can analyze the current stress hotspots in the city and propose interventions. How can I help you?")
           await ctx.send(sender, welcome_msg)
      
       elif isinstance(item, TextContent):
           ctx.logger.info(f"Text message from {sender}: {item.text}")
           
           # If the user asks for analysis, we orchestrate the backend agents
           if "analyze" in item.text.lower() or "hotspot" in item.text.lower() or "stress" in item.text.lower() or "city" in item.text.lower():
               ctx.logger.info("Triggering Superblock backend orchestration...")
               result_narrative = query_backend_orchestration()
               response_message = create_text_chat(result_narrative)
           else:
               response_message = create_text_chat("I am the Superblock City Planner. Ask me to 'analyze current city hotspots' to run the diagnostic pipeline.")
               
           await ctx.send(sender, response_message)

       elif isinstance(item, EndSessionContent):
           ctx.logger.info(f"Session ended with {sender}")
       else:
           ctx.logger.info(f"Received unexpected content type from {sender}")

# Handle acknowledgements for messages this agent has sent out
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
   ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

# Include the chat protocol and publish the manifest to Agentverse
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__": 
    print("="*60)
    print("Starting Superblock ASI:One Skill Agent")
    print(f"Agent Address: {agent.address}")
    print("="*60)
    agent.run()
