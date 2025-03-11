import os
from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, validator
from uuid import UUID
from typing import List, Optional
from enum import Enum
from .elastic import es, NotFoundError

# Conf
MIN_SCORE = float(os.environ.get('MIN_SCORE', 0.5))
MAX_DIFF = float(os.environ.get('MAX_DIFF', 0.3))
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
    index_name: str
    confirmation_code: str = None


class Item(BaseModel):
    uuid: UUID
    description: str
    ingredients: List[str]
    index_name: str

    @validator("ingredients")
    def check_ingredients_length(cls, v):
        if len(v) < 1:
            raise ValueError('"ingredients" must have at least one element')
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
            es.init_index(index_name=command.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during delete: {}".format(e),
            )
        return {"message": "Init successfully executed"}
    elif command.command == "reset":
        try:
            es.reset_index(index_name=command.index_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during delete: {}".format(e),
            )
        return {"message": "Reset successfully executed"}
    elif command.command == "delete":
        try:
            es.delete_index(index_name=command.index_name)
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
        response = es.add_item(item_dict, index_name=index_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during add: {}".format(e),
        )
    logger.info('Added {}'.format(item_dict))
    return response

@app.post("/api/v1/delete/")
async def delete_item(item: Item):
    try:
        item_dict = item.dict()
        item_dict["uuid"] = str(item_dict["uuid"])
        index_name = item_dict.get('index_name', None)
        response = es.delete_item(uuid=item_dict["uuid"], index_name=index_name)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during delete: {}".format(e),
        )
    logger.info('Deleted {}'.format(item_dict["uuid"] ))
    return response


@app.get("/api/v1/search")
async def search(q: str = Query(..., min_length=3, max_length=100),
                 index_name: Optional[str] = None,
                 min_score: Optional[float] = None,
                 max_diff: Optional[float] = None):


    # Perform the search
    elastic_response = es.query(q,index_name)

    # ------------------
    # Filter hits
    # ------------------
    # TODO:  maybe use k-means with _score and 1 ingredient as an enum

    # This is when there is no index at all
    if not elastic_response:
        return []

    # Shortcut
    hits = elastic_response["hits"]["hits"]

    # Ensure we have some hits
    if not hits:
        return []

    # Set the boundaries
    min_score = MIN_SCORE if min_score is None else min_score
    max_diff = MAX_DIFF if max_diff is None else max_diff

    # Only keep the high scoring hits
    max_score = elastic_response["hits"]["max_score"]
    high_score_hits = [hit for hit in hits if hit["_score"] >= min_score]
    if not high_score_hits:
        return []
    logger.debug('high_score_hits={}'.format(high_score_hits))


    # Set the reference main ingredient
    reference_main_ingredient = high_score_hits[0]['_source']['ingredients'][0]

    # Filter based on the main ingredient
    filtered_high_score_hits = []
    for hit in high_score_hits:
        if hit['_source']['ingredients'][0] == reference_main_ingredient:
            filtered_high_score_hits.append(hit)
    logger.debug('filtered_high_score_hits={}'.format(filtered_high_score_hits))

    # Compute the relative score
    for hit in filtered_high_score_hits:
        hit['_relative_score'] = hit["_score"] / max_score

    # Get now only the close hits based on the relative score
    close_hits = [
        hit for hit in filtered_high_score_hits if hit["_relative_score"] >= (1-max_diff)
    ]
    logger.debug('close_hits={}'.format(close_hits))

    return close_hits

