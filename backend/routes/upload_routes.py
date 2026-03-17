from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.file_handler import validate_and_clean, insert_dataframe

router = APIRouter()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accepts a CSV file, validates columns, cleans data,
    inserts into PostgreSQL, and returns a summary.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    file_bytes = await file.read()

    try:
        df = validate_and_clean(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rows_inserted = insert_dataframe(df)

    return {
        "message": "File uploaded and data inserted successfully.",
        "filename": file.filename,
        "rows_inserted": rows_inserted,
    }