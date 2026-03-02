from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.image_to_text import extract_timetable_from_image

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/extract-timetable")
async def extract_timetable(file: UploadFile = File(...)):

    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Only PNG and JPG images are supported"
        )

    try:
        image_bytes = await file.read()
        extracted_json = extract_timetable_from_image(image_bytes)

        return JSONResponse(content=extracted_json)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )