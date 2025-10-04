from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv
from gesture_detector import detector

load_dotenv()

app = FastAPI(title="Feedback Management System API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration - Railway PostgreSQL
DB_CONFIG = {
    'host': os.getenv('PGHOST', os.getenv('DB_HOST', 'localhost')),
    'database': os.getenv('PGDATABASE', os.getenv('DB_NAME', 'feedback_system')),
    'user': os.getenv('PGUSER', os.getenv('DB_USER', 'postgres')),
    'password': os.getenv('PGPASSWORD', os.getenv('DB_PASSWORD', '')),
    'port': int(os.getenv('PGPORT', os.getenv('DB_PORT', 5432)))
}

# Pydantic models
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
    gesture: Optional[str]  # "positive", "negative", or None
    landmarks: Optional[list] = None
    debug_info: Optional[dict] = None
    error: Optional[str] = None

def get_db_connection():
    try:
        print(f"Connecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        connection = psycopg2.connect(**DB_CONFIG)
        print("Database connection successful")
        return connection
    except Error as e:
        print(f"Database connection failed: {str(e)}")
        print(f"DB Config: {DB_CONFIG}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def init_database():
    """Initialize database and create tables if they don't exist"""
    connection = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create feedbacks table
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
        print("Database initialized successfully")
        
    except Error as e:
        print(f"Database initialization failed: {str(e)}")
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.on_event("startup")
async def startup_event():
    init_database()

@app.get("/")
async def root():
    return {"message": "Feedback Management System API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
    """Create a new feedback entry"""
    connection = None
    try:
        print(f"Creating feedback: {feedback.type}")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO feedbacks (type, name, email, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(query, (
            feedback.type,
            feedback.name,
            feedback.email,
            feedback.message
        ))
        
        connection.commit()
        feedback_id = cursor.fetchone()[0]
        
        print(f"Feedback created successfully with ID: {feedback_id}")
        return f"Feedback created successfully with ID: {feedback_id}"
        
    except Error as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.get("/feedbacks", response_model=list[FeedbackResponse])
async def get_feedbacks():
    """Get all feedback entries"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM feedbacks ORDER BY created_at DESC"
        cursor.execute(query)
        results = cursor.fetchall()
        
        return results
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.post("/detect-gesture", response_model=GestureDetectionResponse)
async def detect_gesture(request: GestureDetectionRequest):
    """Detect thumb gesture from camera frame"""
    try:
        result = detector.process_frame(request.frame_data)
        return GestureDetectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gesture detection error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
