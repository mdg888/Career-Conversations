# Michael Di Giantomasso Career Profile Chatbot

This project is a professional conversational AI chatbot designed to represent Michael Di Giantomasso on his website. Its main purpose is to answer questions specifically about Michael’s career, background, skills, and experiences for visitors—potential clients or employers—offering a personalized, engaging touchpoint.

## Features

- **Conversational AI**: Engages users in natural language, staying strictly in character as Michael Di Giantomasso.
- **Career-Focused Answers**: Responds only to questions relevant to Michael’s professional background, skills, and experiences.
- **User Interaction Recording**: 
    - Records when users express interest in being contacted (capturing emails, names, and any context).
    - Logs all questions it cannot answer, regardless of topic.
- **Dynamic System Prompting**: Loads custom context from PDF and text profile summaries to support accurate, on-brand responses.
- **Quality Assurance Loop**:
    - Every AI response is evaluated for acceptability.
    - Unacceptable responses are rerun with critical feedback, ensuring professional and on-topic output.
- **Gradio Interface**: Simple, chat-style UI for users to interact with the AI.

## Technologies Used

- **Python**
- [OpenAI API](https://platform.openai.com/)
- [Gradio](https://www.gradio.app/)
- [Pydantic](https://docs.pydantic.dev/)
- [dotenv](https://pypi.org/project/python-dotenv/)
- [PyPDF2 (pypdf)](https://pypdf2.readthedocs.io/) for PDF reading
- [requests](https://requests.readthedocs.io/) for webhooks (Pushover API)

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Pushover API token and user key (for notifications)
- Profile Summary Files:
    - `me/profile_summary.pdf` (PDF containing LinkedIn or CV summary)
    - `me/summary.txt` (Plain text summary)

### Installation

1. **Clone the repository**  
   ```bash
   git clone <your-repository-url>
   cd <your-repository-folder>
   ```

2. **Set up environment variables**  
   Create a `.env` file in the project root and specify:
   ```env
   OPENAI_API_KEY=your-openai-key
   PUSHOVER_TOKEN=your-pushover-app-token
   PUSHOVER_USER=your-pushover-user-key
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure your profile summary files are present:**  
   - `me/profile_summary.pdf`
   - `me/summary.txt`

### Running the App

Simply run:

```bash
python src/app.py
```
The Gradio chat interface will launch locally in your default web browser.

## Usage Flow

1. **Users** visit the chat interface and ask questions.
2. The chatbot answers only if the question relates to Michael’s career or professional information.
3. If a user wishes to be contacted, the chatbot will prompt for an email and (optionally) a name, then record this via Pushover.
4. If it does not know the answer, the chatbot records the question via the Pushover API.
5. Each AI answer is programmatically evaluated for relevance and quality—rejections trigger an automatic rewrite and resubmission.

## File Structure

```plaintext
Career-Conversations/
│
├── me/
│   ├── profile_summary.pdf   # PDF with Michael's professional summary
│   └── summary.txt           # Text version of Michael's summary
│
├── src/
│   └── app.py                # Main application script
│
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not in version control)
└── .gitignore                # Git ignore rules
```

## Code Architecture

### Core Components

#### 1. **Tool Functions** (`record_user_details`, `record_unknown_question`)
These functions send notifications via Pushover API when:
- A user provides contact details (email, name, notes)
- The chatbot encounters a question it cannot answer

#### 2. **Tool Definitions** (`record_user_details_json`, `record_unknown_question_json`)
JSON schemas that define the structure and parameters for OpenAI function calling. These tell the AI when and how to use each tool.

#### 3. **Me Class**
The main class that orchestrates the chatbot:

**`__init__()`**:
- Initializes OpenAI client
- Loads Michael's name
- Reads profile data from `me/profile_summary.pdf` (LinkedIn summary)
- Reads additional context from `me/summary.txt`

**`handle_tool_calls(tool_calls)`**:
- Processes OpenAI function calls
- Executes the appropriate Python function
- Returns results back to the conversation

**`system_prompt()`**:
- Constructs the AI's system instructions
- Injects Michael's profile data as context
- Defines behavior rules (stay in character, record unknown questions, request emails)

**`evaluator_system_prompt()`**:
- Creates instructions for the quality evaluator
- Includes Michael's profile for reference
- Sets criteria for acceptable responses

**`evaluator_user_prompt(reply, message, history)`**:
- Formats the conversation for evaluation
- Includes user message, AI reply, and chat history

**`evaluate(reply, message, history)`**:
- Uses GPT-4o-mini with structured output (Pydantic)
- Returns `Evaluation` object with `is_acceptable` bool and `feedback` string
- Quality control layer to ensure professional responses

**`rerun(reply, message, history, feedback)`**:
- Called when evaluation fails
- Adds rejection feedback to system prompt
- Regenerates response with improved instructions

**`chat(message, history)`**:
- Main conversation loop
- Calls OpenAI API with tools enabled
- Handles tool calls in a loop until completion
- Evaluates final response
- Reruns if evaluation fails
- Returns final reply to user

#### 4. **Gradio Interface**
`gr.ChatInterface(me.chat).launch()` creates a web UI that:
- Accepts user messages
- Passes them to `me.chat()`
- Displays AI responses
- Manages conversation history

### Data Flow

```
User Input → chat() → OpenAI API (with tools) → Tool Calls?
                                                    ↓
                                            handle_tool_calls()
                                                    ↓
                                            Pushover Notification
                                                    ↓
AI Response → evaluate() → Pass? → Return to User
                            ↓ Fail
                        rerun() → Improved Response
```

## Customization

- **To represent a different individual**:
  Replace the `me/profile_summary.pdf` and `me/summary.txt` with the relevant person's information.
  Update the `self.name` attribute in the `Me` class.

- **Adding More Tools**:
  You can expand the `tools` list following the included schema to integrate additional functionality.

## Hugging Face Deployed Version 

Try out the chatbot **here**: [Michael's Website](https://huggingface.co/spaces/mdg8888/career_conversation)



## Security & Privacy

- **Sensitive data**, such as API keys and user email addresses, are handled securely using environment variables and are never stored or displayed.
- The chatbot never answers questions outside the professional domain and records all unknown or irrelevant questions for review.
