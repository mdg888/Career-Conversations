# Import required libraries
from dotenv import load_dotenv  # Load environment variables from .env file
from openai import OpenAI        # OpenAI API client
import json                      # JSON parsing for tool calls
import os                        # Access environment variables
import requests                  # Make HTTP requests for notifications
from pypdf import PdfReader      # Extract text from PDF files
import gradio as gr              # Web interface framework
from pydantic import BaseModel   # Data validation for structured outputs

# Load environment variables and initialize OpenAI client
load_dotenv(override=True)
openai = OpenAI()

# Send push notifications via Pushover service
def push(text):
    """Send a push notification to alert Michael about important events"""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

# Record contact details when a user wants to get in touch
def record_user_details(email, name="Name not provided", notes="not provided"):
    """Save user contact information and send notification"""
    # Send notification with user's name, email, and any conversation notes
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"status": "success"}

# Track questions the chatbot couldn't answer
def record_unknown_question(question):
    """Log unanswered questions to identify knowledge gaps"""
    # Alert Michael about questions that couldn't be answered
    push(f"{question} it appears I don't know how to answer that")
    return {"status": "success"}

# OpenAI function calling schema for recording user contact info
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

# OpenAI function calling schema for recording unanswered questions
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# List of tools available to the AI chatbot
tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

# Pydantic model for structured evaluation output
class Evaluation(BaseModel):
    """Response quality evaluation result"""
    is_acceptable: bool  # Whether the AI's response meets quality standards
    feedback: str        # Explanation of the evaluation decision

# Main chatbot class representing Michael Di Giatnamasso
class Me:

    def __init__(self):
        """Initialize the chatbot with Michael's profile information"""
        self.openai = OpenAI()
        self.name = "Michael Di Giatnomasso"

        # Extract LinkedIn profile text from PDF
        reader = PdfReader("me/profile_summary.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text

        # Load career summary from text file
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_calls(self, tool_calls):
        """Execute functions requested by the AI and return results"""
        results = []
        for tool_call in tool_calls:
            # Get the function name and arguments from the tool call
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            # Look up the function and execute it with the provided arguments
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}

            # Format the result for OpenAI API
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def system_prompt(self):
        """Generate the main system prompt that defines the AI's behavior"""
        # Define the AI's role, personality, and instructions
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        # Include Michael's career information as context
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## Summary Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def evaluator_system_prompt(self):
        """Generate system prompt for the quality evaluation AI"""
        # Define evaluation criteria and context
        evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
        The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        The Agent is expected to not answer any other random and disconnected questions and should redirect them to questions about {self.name} and information about their summary. \
        When the Agent is using record_user_details tool make sure the agent asks the user for a name and email. \
        The Agent has been provided with context on {self.name} in the form of their profile summary. Here's the information:"

        # Provide the same context the chatbot has for accurate evaluation
        evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## Profile Summary:\n{self.linkedin}\n\n"
        evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        return evaluator_system_prompt

    def evaluator_user_prompt(self, reply, message, history):
        """Build the evaluation prompt containing the conversation to assess"""
        # Provide full conversation context for evaluation
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable as a bool and your feedback as a string answer."
        return user_prompt

    def evaluate(self, reply, message, history) -> Evaluation:
        """Check if the AI's response meets quality standards"""
        # Build evaluation messages with system and user prompts
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + \
                   [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]

        # Use structured output to get consistent evaluation format
        response = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Evaluation
        )
        return response.choices[0].message.parsed

    def rerun(self, reply, message, history, feedback):
        """Regenerate response after evaluation failure, using feedback to improve"""
        # Add rejection feedback to system prompt for second attempt
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"

        # Generate improved response with explicit feedback
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content

    def chat(self, message, history):
        """Main chat handler - processes messages and generates quality-controlled responses"""
        # Build conversation context with system prompt, history, and new message
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False

        # Loop until AI provides final response (may call tools first)
        while not done:
            # Call OpenAI API with available tools
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)

            finish_reason = response.choices[0].finish_reason

            # If AI wants to call a tool, execute it and continue
            if finish_reason == "tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_calls(tool_calls)
                # Add tool calls and results to conversation
                messages.append(message_obj)
                messages.extend(results)
            else:
                # AI has finished and provided final response
                done = True

        # Extract the response content
        reply = response.choices[0].message.content

        # Quality control: evaluate the response
        evaluation = self.evaluate(reply, message, history)
        if not evaluation.is_acceptable:
            # Response failed quality check - regenerate with feedback
            print("eval")
            print(evaluation.feedback)
            reply = self.rerun(reply, message, history, evaluation.feedback)

        return reply

# Launch the chatbot web interface
if __name__ == "__main__":
    # Initialize chatbot and start Gradio web interface
    me = Me()
    gr.ChatInterface(me.chat).launch()
