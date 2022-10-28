from typing import Iterable

import pandas as pd
from pydantic import BaseModel


def to_data_frame(
    rows: Iterable[BaseModel], model_type: type[BaseModel]
) -> pd.DataFrame:
    return pd.DataFrame.from_records(
        (row.dict() for row in rows), columns=model_type.__fields__.keys()
    )


def parse_to_data_frame(rows: list[dict], model_type: type[BaseModel]):
    model_rows = (model_type.parse_obj(row) for row in rows)
    return to_data_frame(model_rows, model_type)
