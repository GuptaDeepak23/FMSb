from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv
from gesture_detector import detector

# Load environment variables
load_dotenv()

app = FastAPI(title="Feedback Management System API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration from Railway environment variables
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'database': os.getenv('PGDATABASE', 'feedback_system'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'port': int(os.getenv('PGPORT', 5432))
}

# --- Models ---
class FeedbackBase(BaseModel):
    type: str  # "positive" or "negative"
    name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    type: str
    name: Optional[str]
    email: Optional[str]
    message: Optional[str]
    created_at: datetime

class GestureDetectionRequest(BaseModel):
    frame_data: str  # Base64 encoded image data

class GestureDetectionResponse(BaseModel):
    gesture: Optional[str] = None
    landmarks: Optional[list] = None
    debug_info: Optional[dict] = None
    error: Optional[str] = None

# --- Database helpers ---
def get_db_connection():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def init_database():
    """Create the feedbacks table if it doesn't exist"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id SERIAL PRIMARY KEY,
                type VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                email VARCHAR(100),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()
        print("✅ Database initialized successfully")
    except Error as e:
        print(f"Database initialization failed: {e}")

# --- Events ---
@app.on_event("startup")
async def startup_event():
    init_database()

# --- Routes ---
@app.get("/")
async def root():
    return {"message": "Feedback Management System API running on Railway 🚀"}

@app.get("/health")
async def health_check():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/feedback", response_model=str)
async def create_feedback(feedback: FeedbackBase):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO feedbacks (type, name, email, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (feedback.type, feedback.name, feedback.email, feedback.message))
        feedback_id = cursor.fetchone()[0]
        connection.commit()
        cursor.close()
        connection.close()
        return f"Feedback created successfully with ID: {feedback_id}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")

@app.get("/feedbacks", response_model=list[FeedbackResponse])
async def get_feedbacks():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, type, name, email, message, created_at FROM feedbacks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        feedbacks = [
            FeedbackResponse(
                id=row[0],
                type=row[1],
                name=row[2],
                email=row[3],
                message=row[4],
                created_at=row[5]
            ) for row in rows
        ]
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/detect-gesture", response_model=GestureDetectionResponse)
async def detect_gesture(request: GestureDetectionRequest):
    try:
        result = detector.process_frame(request.frame_data)
        return GestureDetectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gesture detection error: {str(e)}")

# --- Run locally ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Railway provides PORT env var
    uvicorn.run(app, host="0.0.0.0", port=port)
