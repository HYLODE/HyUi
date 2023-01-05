def _as_int(s: int | float | None) -> int | None:
    if s is None:
        return None
    else:
        return int(float(s))


def _list_of_unique_rooms(beds: list) -> list:
    rooms = [_split_loc_str(bed["location_string"], "room") for bed in beds]
    rooms = list(set(rooms))
    return rooms


def _split_loc_str(s: str, part: str) -> str:
    dept, room, bed = s.split("^")
    if part == "dept":
        return dept
    elif part == "room":
        return room
    elif part == "bed":
        return bed
    else:
        raise ValueError(f"{part} not one of dept/room/bed")


def _filter_non_beds(beds):
    just_beds = []
    for bed in beds:
        location_string = bed.get("location_string", "").lower()
        if "wait" in location_string:
            continue
        just_beds.append(bed)

    return just_beds


def _make_bed(
    bed: dict, scale: int = 9, offset: tuple[int, int] = (-100, -100)
) -> dict:
    location_string = bed.get("location_string")
    hl7_bed = _split_loc_str(location_string, "bed")

    position = {}
    if bed.get("xpos") and bed.get("ypos"):
        position.update(x=bed.get("xpos") * scale + offset[0]),  # type: ignore
        position.update(y=bed.get("ypos") * scale + offset[1]),  # type: ignore

    room = _split_loc_str(bed["location_string"], "room")

    try:
        pretty_bed = hl7_bed.split("-")[1]
        try:
            bed_index = int(pretty_bed)
        except ValueError:
            bed_index = 0
    except IndexError:
        pretty_bed = hl7_bed
        bed_index = 0

    data = dict(
        id=bed["location_string"],
        bed_index=bed_index,  # noqa
        label=pretty_bed,
        parent=room,
        level="bed",
        closed=bed.get("closed", False),
        covid=bed.get("covid", False),
    )

    return dict(data=data, position=position)


def _make_room(room: str) -> dict:
    sideroom = False
    try:
        pretty_room = room.split(" ")[1]
        room_type = pretty_room[:2]
        room_number = pretty_room[2:]
        if room_type == "BY":
            label = "Bay "
        elif room_type == "SR":
            label = "Room "
            sideroom = True
        else:
            label = ""
        # noinspection PyAugmentAssignment
        label = label + room_number
    except IndexError:
        label = room

    return dict(
        data=dict(
            id=room,
            label=label,
            sideroom=sideroom,
            level="room",
        )
    )


def _populate_beds(bl: list[dict], cl: list[dict]) -> list[dict]:
    """
    Place patients in beds

    Args:
        bl: bed_list
        cl: census_list

    Returns:
        a list of dictionaries to populate elements for Cytoscape
    """
    # convert to dictionary of dictionaries to search / merge
    cd = {i["location_string"]: i for i in cl}
    for bed in bl:
        location_string = bed.get("data").get("id")  # type: ignore
        census = cd.get(location_string, {})  # type: ignore
        bed["data"]["census"] = census
        bed["data"]["encounter"] = _as_int(census.get("encounter", None))
        bed["data"]["occupied"] = True if census.get("occupied", None) else False
    return bl


def _update_patients_with_sitrep(bl: list[dict], sl: list[dict]) -> list[dict]:
    """
    Merge sitlist details on to patient list using encounter key
    Args:
        bl: beds with patients
        sl: sitlist

    Returns:
        updated bed_list holding sitlist data

    """

    # convert to dictionary for searching simply
    sd = {int(i["csn"]): i for i in sl if i["csn"]}
    for bed in bl:
        csn = bed.get("data").get("encounter")
        sitrep = sd.get(csn, {})
        bed["data"]["sitlist"] = sitrep
        bed["data"]["wim"] = sitrep.get("wim_1")
    return bl


def _update_discharges(bl: list[dict], discharges: list[dict]) -> list[dict]:
    # convert to dictionary of dictionaries to search / merge
    dd = {i["csn"]: i for i in discharges}
    for bed in bl:
        csn = bed.get("data").get("encounter")
        # if there's a patient in the bed
        if not csn:
            continue
        # pm = planned_move
        pm_type = bed["data"]["census"].get("pm_type")
        pm_modified = bed["data"]["census"].get("pm_datetime")
        bed["data"]["discharge"] = True if pm_type == "OUTBOUND" else False

        # if there's better info on discharge status
        dc_status = dd.get(csn, {})
        bed["data"]["dc_status"] = dc_status
        if not len(dc_status):
            continue
        dc_modified = dc_status.get("modified_at")
        if not pm_modified:
            bed["data"]["discharge"] = (
                True if dc_status.get("status") == "ready" else False
            )
        else:
            dc_modified = datetime.fromisoformat(dc_modified)
            pm_modified = datetime.fromisoformat(pm_modified)
            if dc_modified > pm_modified:
                bed["data"]["discharge"] = (
                    True if dc_status.get("status") == "ready" else False
                )

    return bl
