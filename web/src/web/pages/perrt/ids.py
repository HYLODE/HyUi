from web.utils import gen_id

# raw stores
CENSUS_STORE = gen_id("census store", __name__)
BEDS_STORE = gen_id("beds store", __name__)
NEWS_STORE = gen_id("news store", __name__)
PREDICTIONS_STORE = gen_id("predictions store", __name__)

# derived stores
DEPTS_OPEN_STORE = gen_id("open depts store", __name__)
ROOMS_OPEN_STORE = gen_id("open rooms store", __name__)
DEPTS_OPEN_STORE_NAMES = gen_id("open depts store names", __name__)

# controls
CAMPUS_SELECTOR = gen_id("campus selector", __name__)
DEPT_SELECTOR = gen_id("dept selector", __name__)
LAYOUT_SELECTOR = gen_id("layout selector", __name__)
BED_SELECTOR_CAMPUS = gen_id("bed selector campus", __name__)

# content
CYTO_CAMPUS = gen_id("cyto campus", __name__)
PROGRESS_CAMPUS = gen_id("progress campus", __name__)

# inspector
SIDEBAR_TITLE = gen_id("sidebar title", __name__)
SIDEBAR_CONTENT = gen_id("sidebar content", __name__)

INSPECTOR_CAMPUS_MODAL = gen_id("inspector campus modal", __name__)
INSPECTOR_CAMPUS_ACCORDION = gen_id("campus accordion", __name__)

ACCORDION_ITEM_PERRT = gen_id("accordion bed", __name__)
ACC_BED_DECISION_TEXT = gen_id("bed decision text", __name__)
ACC_BED_STATUS_CAMPUS = gen_id("bed status campus", __name__)
ACC_BED_SUBMIT_CAMPUS = gen_id("bed submit campus", __name__)
ACC_BED_SUBMIT_CAMPUS_NOTIFY = gen_id("bed submit campus notify", __name__)
ACC_BED_SUBMIT_STORE = gen_id("bed submit campus store", __name__)

ACCORDION_ITEM_PATIENT = gen_id("accordion patient", __name__)
ACCORDION_ITEM_DEBUG = gen_id("accordion debug", __name__)


# other
DEBUG_NODE_INSPECTOR_CAMPUS = gen_id("debug inspect node campus", __name__)
