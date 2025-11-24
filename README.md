# Michael Di Giantomasso – Career Profile Chatbot

A professional AI chatbot designed for Michael Di Giantomasso’s website. It answers questions about Michael’s **career, background, skills, and experience**, and logs any questions it cannot answer.

## What It Does

* **Conversational AI**
  Answers only questions related to Michael’s professional profile.

* **Contact Capture**
  Records when users want to be contacted (name, email, and notes).

* **Unknown Question Logging**
  Saves questions it can’t answer into a PostgreSQL database and sends a push notification.

* **Push Notifications**
  Uses the Pushover API for real-time alerts.

* **Dynamic Context**
  Loads Michael’s PDF and text summaries for on-brand responses.

* **Quality Checks**
  Every answer is evaluated; if it’s not good enough, the bot rewrites the response before sending it to the user.

* **Simple Web Interface**
  Built using Gradio.

## Technologies

* **Python 3.8+**
* **OpenAI API (GPT-4o-mini)**
* **PostgreSQL + psycopg2**
* **Gradio UI**
* **pypdf**, **requests**, **python-dotenv**
* **Pushover API**
* **pytest** for testing

## Getting Started

### Prerequisites

* Python 3.8+
* PostgreSQL server
* OpenAI API key
* Pushover API token & user key
* Two profile files:

  * `me/profile_summary.pdf`
  * `me/summary.txt`

### Installation

```bash
git clone <repo>
cd Career-Conversations
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Setup

```bash
createdb unanswered_questions
psql unanswered_questions < database/schema.sql
```

### Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your-key
PUSHOVER_TOKEN=your-token
PUSHOVER_USER=your-user-key
DATABASE_URL=postgresql://localhost/unanswered_questions
```

### Run the App

```bash
python src/app.py
```

Gradio will open at: `http://127.0.0.1:7860`

### Run Tests

```bash
pytest
pytest --cov=src
```

## How the Chatbot Works

1. User asks a question in the Gradio interface.
2. The bot uses Michael’s profile data to answer.
3. If the question is off-topic or unknown, the bot logs it and triggers a Pushover alert.
4. The answer goes through an automatic quality check.
5. If rejected, the bot rewrites the answer and sends the improved version.

## Project Structure

```
Career-Conversations/
|-- me/                     # Profile documents
|-- src/                    # Main chatbot code
|-- database/               # DB schema + operations
|-- tests/                  # Test suite
|-- requirements.txt
|-- README.md
```

## Key Components

### **QuestionDB**

Handles storing and retrieving unknown questions from PostgreSQL:

* Add/Search/Delete questions
* Get stats by category
* Full-text search support

### **Tool Functions**

* `record_user_details` – save contact details + send notification
* `record_unknown_question` – log unknown questions + alert

### **Me Class**

Main chatbot engine:

* Loads profile data
* Builds system prompts
* Handles OpenAI function calling
* Evaluates and reruns responses
* Powers the chat flow used by Gradio

## Customization

To adapt this chatbot for another person:

1. Replace files in the `me/` directory.
2. Update the name in the `Me` class.

To add new tools, create a function, define its JSON schema, and add it to the tools list.

## Deployment

### Hugging Face Spaces

Live demo: **[https://huggingface.co/spaces/mdg8888/career_conversation](https://huggingface.co/spaces/mdg8888/career_conversation)**

### Local or Server Deployment

Just run:

```bash
python src/app.py
```

Optional (production):

```bash
gunicorn src.app:app
```

### Docker (Optional)

```bash
docker build -t career-chatbot .
docker run -p 7860:7860 --env-file .env career-chatbot
```

## Troubleshooting

* **Database issues**: Ensure PostgreSQL is running and `DATABASE_URL` is correct.
* **OpenAI errors**: Check API key and usage limits.
* **Pushover issues**: Validate token and user key.
* **PDF errors**: Ensure the summary files exist and are readable.

## Contact

**Michael Di Giantomasso**
Chatbot link: [https://huggingface.co/spaces/mdg8888/career_conversation](https://huggingface.co/spaces/mdg8888/career_conversation)