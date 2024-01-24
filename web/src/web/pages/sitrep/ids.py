from web.utils import gen_id

# raw stores
CENSUS_STORE = gen_id("census store", __name__)
BEDS_STORE = gen_id("beds store", __name__)
SITREP_STORE = gen_id("sitrep store", __name__)
DISCHARGES_STORE = gen_id("discharges store", __name__)
DEPT_GROUPER = gen_id("dept grouper", __name__)

# derived stores
DEPTS_OPEN_STORE = gen_id("open depts store", __name__)
ROOMS_OPEN_STORE = gen_id("open rooms store", __name__)
DEPTS_OPEN_STORE_NAMES = gen_id("open depts store names", __name__)

# controls
DEPT_GROUPER_SELECTOR = gen_id("dept grouper selector", __name__)
DEPT_SELECTOR = gen_id("dept selector", __name__)
LAYOUT_SELECTOR = gen_id("layout selector", __name__)
BED_SELECTOR_WARD = gen_id("bed selector ward", __name__)

# content
CYTO_CAMPUS = gen_id("cyto campus", __name__)
CYTO_WARD = gen_id("cyto ward", __name__)

PROGRESS_CAMPUS = gen_id("progress campus", __name__)
PROGRESS_WARD = gen_id("progress ward", __name__)

# modal (campus)
INSPECTOR_CAMPUS_MODAL = gen_id("inspector campus modal", __name__)

# sidebar (critical care and ward)
INSPECTOR_WARD_MODAL = gen_id("inspector ward modal", __name__)

INSPECTOR_WARD_SIDEBAR = gen_id("inspector patient sidebar", __name__)
INSPECTOR_WARD_TITLE = gen_id("inspector patient sidebar title", __name__)
INSPECTOR_WARD_ACCORDION = gen_id("ward accordion", __name__)

# accordion within sidebar
ACCORDION_ITEM_BED = gen_id("accordion bed", __name__)
ACC_BED_DECISION_TEXT = gen_id("bed decision text", __name__)
ACC_BED_STATUS_WARD = gen_id("bed status ward", __name__)
ACC_BED_SUBMIT_WARD = gen_id("bed submit ward", __name__)
ACC_BED_SUBMIT_WARD_NOTIFY = gen_id("bed submit ward notify", __name__)
ACC_BED_SUBMIT_STORE = gen_id("bed submit ward store", __name__)

ACCORDION_ITEM_PATIENT = gen_id("accordion patient", __name__)
ACCORDION_ITEM_DEBUG = gen_id("accordion debug", __name__)


# other
DEBUG_NODE_INSPECTOR_CAMPUS = gen_id("debug inspect node campus", __name__)
DEBUG_NODE_INSPECTOR_WARD = gen_id("debug inspect node ward", __name__)
