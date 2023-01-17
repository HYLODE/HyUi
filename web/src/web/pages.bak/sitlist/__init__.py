BPID = "sit_"


PROBABILITY_COLOUR_SCALE = [
    {
        "if": {
            "column_id": "prediction_as_real",
            "filter_query": (
                f"{{prediction_as_real}} >= {c / 10} "
                f"&& {{prediction_as_real}} < {c / 10 + 0.1}"
            ),
        },
        "backgroundColor": f"rgba(46, 204, 64, {c / 10})",
    }
    for c in range(0, 11)
]
