# CFLscraPy
Scraping CFL data using the API powering cfl.ca

Scrape one or more seasons using the get_all_pbp function. For example,

```python
pbp = get_all_pbp(2017, 2022)
```

will return all plays from 2017 to 2022 in a list.

To convert the list of plays to a Pandas DataFrame:

```python
import pandas as pd

pbp_df = pd.DataFrame(pbp)
```

If you encounter any problems, issues, or errors, feel free to reach out. Thanks, and hope you enjoy!
