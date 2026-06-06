"""
Migration script: imports me/profile_summary.pdf and me/summary.txt
into a default chatbot in the new AI Profile Chatbot system.

Run once from the repo root:
    python migrate_existing_profile.py

Requires OPENAI_API_KEY to be set (embeddings are generated during ingest).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.src.db.database import init_db
from backend.src.services.config_service import ConfigService
from backend.src.services.document_service import DocumentService
from backend.src.models.chatbot import ChatbotCreate
from backend.src.core.config import settings

PDF_PATH = Path("me/profile_summary.pdf")
TXT_PATH = Path("me/summary.txt")


def main():
    print("Initialising database…")
    init_db()

    config_service = ConfigService()
    doc_service = DocumentService(data_dir=settings.data_dir)

    existing = config_service.list_chatbots()
    if existing:
        print(f"Found {len(existing)} existing chatbot(s). Skipping creation.")
        chatbot = existing[0]
    else:
        print("Creating default chatbot…")
        chatbot = config_service.create_chatbot(ChatbotCreate(
            name="Michael Di Giatnamasso",
            description="Answers questions about Michael's career, background, skills and experience.",
            tone="professional",
            greeting="Hi, I'm Michael's AI assistant. Ask me anything about his background and experience.",
            fallback_message="I don't have specific information about that. Feel free to reach out to Michael directly.",
            model="gpt-4o-mini",
        ))
        print(f"Created chatbot: {chatbot.id}")

    for path, label in [(PDF_PATH, "LinkedIn profile PDF"), (TXT_PATH, "Career summary TXT")]:
        if not path.exists():
            print(f"  [SKIP] {path} not found — skipping.")
            continue

        print(f"  Ingesting {label}: {path} …")
        file_bytes = path.read_bytes()
        doc = doc_service.ingest(chatbot.id, file_bytes, path.name)
        print(f"  → status: {doc.status}" + (f", error: {doc.error}" if doc.error else ""))

    print("\nMigration complete.")
    print(f"Chatbot ID: {chatbot.id}")
    print("Start the backend with:")
    print("  uvicorn backend.src.api.main:app --reload")


if __name__ == "__main__":
    main()
