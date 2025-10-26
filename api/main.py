import requests
import csv
import os
import uuid

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from pydantic import BaseModel, Field

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "http://api.nessieisreal.com"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

headers = {
    "Content-Type": "application/json",
    "apikey": SERVICE_ROLE,
    "Authorization": f"Bearer {SERVICE_ROLE}",
    "Prefer": "return=representation"
}

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    target_amount: int
    customer_id: str

def create_customer():
    params = {
        "first_name": "John",
        "last_name": "Doe",
        "address": {
            "street_number": "101",
            "street_name": "Wall Street",
            "city": "New York",
            "state": "NY",
            "zip": "10010"
        }
    }
    response = requests.post(f"{BASE_URL}/customers?key={API_KEY}", json=params)
    if response.status_code != 201:
        print(f"Error: {response.status_code}\n {response.json()}")
        return
    
    endpoint = f"{SUPABASE_URL}/rest/v1/customer"
    payload = response.json()["objectCreated"]
    payload["customer_id"] = payload["_id"]
    payload["city"] = payload["address"]["city"]
    payload.pop("_id")
    payload.pop("address")
    

    resp = requests.post(endpoint, headers=headers, json=payload)
    if resp.status_code != 201:
        print("[customer] status:", resp.status_code)
    

def create_account(customer_id):
    params = {
        "type": "Credit Card",
        "nickname": "Personal Credit Card",
        "rewards": 0,
        "balance": 10000
    }
    response = requests.post(f"{BASE_URL}/customers?key={API_KEY}", json=params)
    if response.status_code == 201:
        print(response.json())
    else:
        print(f"Error: {response.status_code}\n {response.json()}")

app = FastAPI()

@app.get("/")
def main():
    return {"Hello": "World"}

@app.get("/users/{customer_id}")
def get_user_accounts(customer_id: str):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/accounts?{customer_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": f"{response.status_code} {response.text}"}

@app.get("/users/{customer_id}/purchases")
def get_purchases(customer_id: str):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/purchase?{customer_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": f"{response.status_code} {response.text}"}

@app.get("/users/{customer_id}/transactions")
def get_transactions(customer_id: str):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/transactions?{customer_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": f"{response.status_code} {response.text}"}

@app.get("/users/{customer_id}/balance_history")
def get_transactions(customer_id: str):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/balance_history?{customer_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": f"{response.status_code} {response.text}"}

@app.post("/users/{user_id}/goals")
def create_goal(goal: Goal):
    response = requests.post(f"{SUPABASE_URL}/rest/v1/goals?{goal.customer_id}", headers=headers, json=goal.model_dump())
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.status_code

if __name__ == "__main__":
    print("This app is running")