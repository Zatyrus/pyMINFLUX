import pandas as pd

# create a DataFrame
df = pd.DataFrame({"A": ["foo", "bar", "baz"], "B": [1, 2, 3]})

# create a dictionary of replacements
replacements = {"foo": "qux", "baz": "quux"}

# replace values using the .map() method
df["A"] = df["A"].map(replacements).fillna(df["A"])

# print the DataFrame
print(df)
