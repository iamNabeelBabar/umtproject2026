from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from typing import List
from fastapi.concurrency import run_in_threadpool
from services.image_to_text2 import extract_timetable_from_multiple_images

router = APIRouter(prefix="/ocr", tags=["OCR-MULTI"])

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg"}


@router.post(
    "/extract-timetable-multi",
    status_code=status.HTTP_200_OK,
    summary="Extract timetable from uploaded images",
)
async def extract_timetable_multi(
    file1: UploadFile = File(..., description="First timetable image (PNG/JPG)"),
    file2: UploadFile | None = File(None, description="Second timetable image (optional)"),
    file3: UploadFile | None = File(None, description="Third timetable image (optional)"),
    file4: UploadFile | None = File(None, description="Fourth timetable image (optional)"),
    file5: UploadFile | None = File(None, description="Fifth timetable image (optional)"),
):
    raw_files = [file1, file2, file3, file4, file5]
    files = [f for f in raw_files if f is not None and f.filename]

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one timetable image is required."
        )

    image_bytes_list: List[bytes] = []

    try:
        for file in files:
            if file.content_type not in ALLOWED_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.content_type}. Only PNG and JPG allowed."
                )

            contents = await file.read()

            if not contents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{file.filename}' is empty."
                )

            image_bytes_list.append(contents)

        extracted_json = await run_in_threadpool(
            extract_timetable_from_multiple_images,
            image_bytes_list
        )

        return extracted_json

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during timetable extraction."
        )