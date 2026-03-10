from enum import StrEnum


class SolutionType(StrEnum):
    GA = "ga"
    PGWO = "pgwo"
    PGWO2 = "pgwo2"
    PGWO3 = "pgwo3"
    ILP_FIXED = "fixed"
    ILP_SINGLE = "single"
    ILP_VARYING = "varying"
