import pandas as pd


def test_flatten_data_frame_dict() -> None:
    df = pd.DataFrame(
        data={
            "column": [
                [
                    {"keyA": "valueA1", "keyB": "valueB1"},
                    {"keyA": "valueA2", "keyB": "valueB2"},
                ]
            ]
        }
    )
    df["flattened_column"] = df["column"].apply(
        lambda rows: "|".join([row.get("keyA", "") for row in rows])
    )

    assert df.iloc[0]["flattened_column"] == "valueA1|valueA2"
