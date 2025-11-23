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
python app.py
```
The Gradio chat interface will launch locally in your default web browser.

## Usage Flow

1. **Users** visit the chat interface and ask questions.
2. The chatbot answers only if the question relates to Michael’s career or professional information.
3. If a user wishes to be contacted, the chatbot will prompt for an email and (optionally) a name, then record this via Pushover.
4. If it does not know the answer, the chatbot records the question via the Pushover API.
5. Each AI answer is programmatically evaluated for relevance and quality—rejections trigger an automatic rewrite and resubmission.

## File Structure (Key Files)

```plaintext
your_project/
│
├── me/
│   ├── profile_summary.pdf   # PDF with Michael's professional summary
│   └── summary.txt           # Text version of Michael's summary
│
├── app.py       # Main Python script (provided above)
├── requirements.txt          # Python dependencies
└── .env                      # API keys (not in version control)
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
