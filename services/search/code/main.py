import os
from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, validator
from uuid import UUID
from typing import List, Optional
from enum import Enum
from .elastic import es

# Conf
MIN_SCORE = float(os.environ.get('MIN_SCORE', 0.8))
MAX_DIFF = float(os.environ.get('MAX_DIFF', 0.02))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'ERROR')


# Setup logging
import logging
logger = logging.getLogger('uvicorn')
logger.setLevel(LOG_LEVEL)

# Get main App
app = FastAPI()

logger.info('Using MIN_SCORE=%s', MIN_SCORE)
logger.info('Using MAX_DIFF=%s', MAX_DIFF)


class CommandEnum(str, Enum):
    init = "init"
    reset = "reset"
    delete = "delete"


class Command(BaseModel):
    command: CommandEnum
    index_name: str = None
    confirmation_code: str = None


class Item(BaseModel):
    uuid: UUID
    description: str
    ingredients: List[str]
    index_name: str

    @validator("ingredients")
    def check_ingredients_length(cls, v):
        if len(v) < 3:
            raise ValueError('"ingredients" must have at least 3 elements')
        return v


@app.post("/api/v1/manage/")
async def manage(command: Command):

    # Check confirmation code
    if command.confirmation_code != "DEADBEEF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid confirmation code"
        )

    # Handle command
    if command.command == "init":
        try:
            es.init(index_name=command.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during delete: {}".format(e),
            )
        return {"message": "Init successfully executed"}
    elif command.command == "reset":
        try:
            es.reset(index_name=command.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during delete: {}".format(e),
            )
        return {"message": "Reset successfully executed"}
    elif command.command == "delete":
        try:
            es.delete(index_name=command.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during delete: {}".format(e),
            )
        return {"message": "Delete successfully executed"}


@app.post("/api/v1/add/")
async def add_item(item: Item):
    try:
        item_dict = item.dict()
        item_dict["uuid"] = str(item_dict["uuid"])
        index_name = item_dict.get('index_name', None)
        response = es.add(item_dict, index_name=index_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during add: {}".format(e),
        )
    return response


@app.get("/api/v1/search")
async def search(q: str = Query(..., min_length=3, max_length=100),
                 index_name: Optional[str] = None,
                 min_score: Optional[float] = None,
                 max_diff: Optional[float] = None):

    # Perform the search
    elastic_response = es.search_q(q,index_name)

    # ------------------
    # Filter hits
    # ------------------
    # TODO:  maybe use k-means with _score and 1 ingredient as an enum

    min_score = MIN_SCORE if min_score is None else min_score
    max_diff = MAX_DIFF if max_diff is None else max_diff

    hits = elastic_response["hits"]["hits"]
    if not hits:
        return []

    max_score = elastic_response["hits"]["max_score"]
    high_score_hits = [hit for hit in hits if hit["_score"] >= min_score]

    # Compute relative score
    for hit in high_score_hits:
        hit['_relative_score'] = hit["_score"] / max_score

    close_hits = [
        hit for hit in high_score_hits if hit["_relative_score"] > (1-max_diff)
    ]

    return close_hits
