from typing import Sequence

from fastapi import FastAPI

from zova.src.zova.models import Activity, TravelerProfile

app = FastAPI(title="Zova API")


@app.get("/health")
def health_check():
    return {"status": "ok"} 

@app.post("/upload")
def upload_preferences(profile: TravelerProfile, activities: Sequence[Activity]):
    # Here you would handle the uploaded preferences, e.g., save them to a database
    print (f"Received profile: {profile}")
    print (f"Received activities: {activities}")
    return {"message": "Preferences uploaded successfully", "profile": profile, "activities": activities}
    pass