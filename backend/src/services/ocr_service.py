from pathlib import Path


class OCRService:

    def extract_text(self, image_path: Path) -> str:
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(image_path)
            return pytesseract.image_to_string(image)
        except Exception as e:
            return f"[OCR extraction failed: {e}]"
