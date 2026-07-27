# Exploratory Data Analysis Summary

Generated from 900 children, 220 foster families, 384 placements.

## Missing Values (Children)
None found.

## Duplicate Rows (Children)
Duplicate count: 0 (0.0%)

## Distribution Statistics (Children, numeric columns)
|                        |   count |   mean |   std |   min |   25% |   50% |   75% |   max |
|:-----------------------|--------:|-------:|------:|------:|------:|------:|------:|------:|
| age                    |     900 |   8.59 |  5.26 |  0    |  4    |  9    | 13    | 17    |
| sibling_group_size     |     900 |   1.73 |  0.94 |  1    |  1    |  1    |  2    |  4    |
| behavioral_notes_score |     900 |   0.37 |  0.17 |  0.02 |  0.23 |  0.36 |  0.48 |  0.92 |
| time_in_care_months    |     900 |  28.22 | 11.27 |  4    | 20    | 27    | 35    | 80    |

## Outlier Summary (IQR method)
| column                 |   outlier_count |   outlier_pct |   lower_bound |   upper_bound |
|:-----------------------|----------------:|--------------:|--------------:|--------------:|
| time_in_care_months    |              13 |          1.44 |         -2.5  |         57.5  |
| behavioral_notes_score |               8 |          0.89 |         -0.13 |          0.85 |
| age                    |               0 |          0    |         -9.5  |         26.5  |

## Correlation Matrix (Children, numeric columns)
|                        |    age |   sibling_group_size |   behavioral_notes_score |   time_in_care_months |
|:-----------------------|-------:|---------------------:|-------------------------:|----------------------:|
| age                    |  1     |               -0.017 |                    0.212 |                 0.438 |
| sibling_group_size     | -0.017 |                1     |                   -0.045 |                 0.205 |
| behavioral_notes_score |  0.212 |               -0.045 |                    1     |                 0.468 |
| time_in_care_months    |  0.438 |                0.205 |                    0.468 |                 1     |
