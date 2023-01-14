from web.utils import gen_id

# stores
CENSUS_STORE = gen_id("census store", __name__)
BEDS_STORE = gen_id("beds store", __name__)
DEPTS_OPEN_STORE = gen_id("open depts store", __name__)
ROOMS_OPEN_STORE = gen_id("open rooms store", __name__)
DEPTS_OPEN_STORE_NAMES = gen_id("open depts store names", __name__)

# controls
CAMPUS_SELECTOR = gen_id("campus selector", __name__)
DEPT_SELECTOR = gen_id("dept selector", __name__)
LAYOUT_SELECTOR = gen_id("layout selector", __name__)

# content
CYTO_CAMPUS = gen_id("cyto campus", __name__)

# other
DEBUG_NODE_INSPECTOR = gen_id("debug inspect node", __name__)