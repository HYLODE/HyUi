def gen_id(name: str) -> str:
    module_name = __name__.split(".")[-2]
    name = name.replace("_", "-").replace(" ", "-").replace(".", "-")
    return f"{module_name}-{name}"


CENSUS_STORE = gen_id("census store")
CAMPUS_SELECTOR = gen_id("campus selector")
CYTO_MAP = gen_id("cyto map")
LAYOUT_SELECTOR = gen_id("layout selector")
DEBUG_NODE_INSPECTOR = gen_id("debug inspect node")
