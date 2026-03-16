from fastapi import FastAPI
from sqlalchemy import text
from database.db_config import engine
from fastapi.middleware.cors import CORSMiddleware  

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Business Intelligence System API Running"}

@app.get("/business-data")
def get_business_data():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM business_data"))
        rows = [dict(row._mapping) for row in result]
    return rows