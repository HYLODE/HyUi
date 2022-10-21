import pandas as pd
from pydantic import BaseModel


def to_data_frame(rows: list[BaseModel]) -> pd.DataFrame:
    return pd.DataFrame.from_records((row.dict() for row in rows))
