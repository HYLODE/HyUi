# Let's prove that the data exists and
import pandas as pd

df = pd.read_hdf("work/sample_df.h5")
print(df.head())
print(df.dtypes)
