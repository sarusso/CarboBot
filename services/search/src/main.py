from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, validator
from uuid import UUID
from typing import List
from enum import Enum
from .elastic import es

MINIMUM_SCORE = 0.8
MINIMUM_DIFF = 0.02

import logging

logger = logging.getLogger(__name__)


app = FastAPI()


class CommandEnum(str, Enum):
    init = "init"
    reset = "reset"
    delete = "delete"


class Command(BaseModel):
    command: CommandEnum
    confirmation_code: str = None


class Item(BaseModel):
    uuid: UUID
    description: str
    ingredients: List[str]

    @validator("ingredients")
    def check_ingredients_length(cls, v):
        if len(v) < 3:
            raise ValueError('"ingredients" must have at least 3 elements')
        return v


@app.post("/api/v1/manage/")
async def manage(command: Command):
    if command.confirmation_code != "DEADBEEF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid confirmation code"
        )
    if command.command == "init":
        try:
            es.init()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generic error during init",
            )
        return {"message": "init successfully executed"}
    elif command.command == "reset":
        try:
            es.reset()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generic error during reset",
            )
        return {"message": "reset successfully executed"}
    elif command.command == "delete":
        try:
            es.delete()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generic error during delete",
            )
        return {"message": "delete successfully executed"}


@app.post("/api/v1/add/")
async def add_item(item: Item):
    try:
        item_dict = item.dict()
        item_dict["uuid"] = str(item_dict["uuid"])
        response = es.add(item_dict)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generic error during add",
        )
    return response


@app.get("/api/v1/search")
async def search(q: str = Query(..., min_length=3, max_length=100)):
    elastic_response = es.search_q(q)

    # ------------------
    # maybe use k-means with _score and 1 ingredient as an enum
    # ------------------

    hits = elastic_response["hits"]["hits"]
    if not hits:
        return None

    max_score = elastic_response["hits"]["max_score"]

    high_score_hits = [h for h in hits if h["_score"] >= MINIMUM_SCORE]

    close_hits = [
        h for h in high_score_hits if (h["_score"] - max_score) < MINIMUM_DIFF
    ]

    return close_hits
