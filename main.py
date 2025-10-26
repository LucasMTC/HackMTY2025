import requests
import csv
import os
import json
import uuid

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from pydantic import BaseModel, Field
col_pal = sns.color_palette()
plt.style.use("fivethirtyeight")



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

def get_transactions(customer_id):
    response = requests.get(f"{SUPABASE_URL}/rest/v1/purchase?{customer_id}", headers=headers)
    if response.status_code == 200:
        with open("data.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=response.json()[0].keys())
            writer.writeheader()
            writer.writerows(response.json())
    else:
        print(f"Error: {response.status_code}\n {response.json()}")

app = FastAPI()

@app.get("/users/{user_id}")
def get_user_accounts(user_id: str):
    accounts = {user_id:[]}
    response = requests.get(f"{BASE_URL}/accounts?key={API_KEY}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    for acc in response.json():
        if acc["customer_id"] == user_id:
            accounts[user_id].append(acc)
    return accounts

@app.post("/users/{user_id}/goals")
def create_goal(goal: Goal):
    response = requests.post(f"{SUPABASE_URL}/rest/v1/goals?{goal.customer_id}", headers=headers, json=goal.model_dump())
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.status_code

def predition_model():
    df = pd.read_csv("data.csv")

    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    df['purchase_month'] = df['purchase_date'].dt.month
    df['purchase_day'] = df['purchase_date'].dt.day
    df['purchase_dayofweek'] = df['purchase_date'].dt.dayofweek
    df = df.drop(columns=['description'])

    le = LabelEncoder()
    df['category_encoded'] = le.fit_transform(df['category'])

    features_to_drop = ['_id', 'merchant_id', 'payer_id', 'purchase_date', 'created_at', 'category']
    X = df.drop(columns=features_to_drop)
    y = df['category_encoded']

    categorical_cols = ['type', 'status', 'medium', 'merchant_name']
    X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = xgb.XGBClassifier(objective='multi:softmax', num_class=len(le.classes_), use_label_encoder=False, eval_metric='mlogloss', n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)

    print("--- XGBoost Classification Report for Category Prediction ---")
    print(f"Accuracy: {report['accuracy']:.4f}")
    print("Detailed Report (JSON format):", json.dumps(report, indent=2))
    print("----------------------------------------------------------")

if __name__ == "__main__":
    print("This app is running")
    predition_model()