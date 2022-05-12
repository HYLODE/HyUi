# https://fastapi.tiangolo.com/tutorial/testing/
# then drop onto command line in activated virtual env
# pytest
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_main():
    return {"msg": "Hello World"}
