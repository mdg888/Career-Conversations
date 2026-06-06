from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pathlib import Path
from backend.src.models.document import DocumentResponse, ALLOWED_EXTENSIONS
from backend.src.services.document_service import DocumentService
from backend.src.core.config import settings

router = APIRouter(prefix="/api/chatbots/{chatbot_id}/documents", tags=["documents"])

MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


def get_document_service() -> DocumentService:
    return DocumentService(data_dir=settings.data_dir)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    chatbot_id: str,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb} MB."
        )

    try:
        return service.ingest(chatbot_id, content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[DocumentResponse])
def list_documents(chatbot_id: str, service: DocumentService = Depends(get_document_service)):
    return service.list_documents(chatbot_id)


@router.delete("/{doc_id}", status_code=204)
def delete_document(chatbot_id: str, doc_id: str, service: DocumentService = Depends(get_document_service)):
    if not service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{doc_id}/rebuild", response_model=DocumentResponse)
def rebuild_document(chatbot_id: str, doc_id: str, service: DocumentService = Depends(get_document_service)):
    try:
        return service.rebuild_embeddings(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
