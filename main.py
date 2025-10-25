from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("API_KEY")


app = FastAPI()

@app.get("/")
def main():
    return {"Hello": "hackmty2025!"}


if __name__ == "__main__":
    print(api_key)
    main()
