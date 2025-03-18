from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import cv2
import torch
from ultralytics import YOLO
from io import BytesIO
from typing import Dict, Any
from database import get_database
from pydantic import BaseModel
from datetime import datetime,timedelta
# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db, collection = get_database()


class AnimalData(BaseModel):
    estimatedAnimalLocation: Dict[str, float]
    class_name: str
    timestamp: str

@app.post("/save_animal_data")
async def save_animal_data(data: AnimalData):
    try:
        # Log incoming data
        print(f"Received data: {data}")

        # Convert the timestamp string to datetime object if needed
        timestamp_str = data.timestamp

        # Handle the "Z" in ISO format, replace with "+00:00"
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        # Parse the timestamp string
        timestamp = datetime.fromisoformat(timestamp_str)

        # Adjust the timestamp to Sri Lankan time (UTC +5:30)
        sri_lankan_time = timestamp + timedelta(hours=5, minutes=30)

        # Update the timestamp in the data
        data.timestamp = sri_lankan_time

        # Convert the Pydantic model to a dictionary
        data_dict = data.dict()

        # Log the adjusted timestamp
        print(f"Adjusted Sri Lankan Time: {sri_lankan_time}")

        # Insert the data into MongoDB
        result = collection.insert_one(data_dict)

        # Log the result or return the inserted ID
        print(f"Data inserted with ID: {result.inserted_id}")

        return {"message": "Animal data saved successfully!", "inserted_id": str(result.inserted_id)}

    except Exception as e:
        # Log the exception details
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

@app.get("/get_animal_data")
async def get_animal_data():
    try:
        # Fetch all animal data from the collection
        animal_data = list(collection.find({}, {"_id": 0}))  # Exclude _id field

        # Convert timestamp format
        for data in animal_data:
            if "timestamp" in data and isinstance(data["timestamp"], dict) and "$date" in data["timestamp"]:
                timestamp_ms = data["timestamp"]["$date"]["$numberLong"]
                timestamp = datetime.utcfromtimestamp(int(timestamp_ms) / 1000)
                sri_lankan_time = timestamp + timedelta(hours=5, minutes=30)
                data["timestamp"] = sri_lankan_time.isoformat()

        return animal_data

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
