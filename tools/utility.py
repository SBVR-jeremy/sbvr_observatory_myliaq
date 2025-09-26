#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""utility.py: This file contains functions shared over the application"""

__author__ = "Jeremy Bluteau"
__copyright__ = "Copyright 2023, SBVR Observatory"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Jeremy Bluteau"
__email__ = "jeremy.bluteau@syndicat-reyssouze.fr"
__status__ = "Dev"


# ---------------------------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import datetime
from datetime import date, timezone, timedelta
import re

import pytz

import csv

from dateutil import tz


# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------
def beginning_of_month(today: date | None = None) -> date:
    today = today or date.today()
    return date(today.year, today.month, 1)

def end_of_month(today: date | None = None) -> date:
    today = today or date.today()
    beginning_of_current_month = beginning_of_month(today) # Step (1)
    beginning_of_next_month = beginning_of_month(          # Step (3)
        beginning_of_current_month + date.resolution * 31  # Step (2)
    )
    return beginning_of_next_month - date.resolution

def utc2local(utc):
    #Use this function to display datetime as local time
    try:
        return utc.astimezone(tz.tzlocal())
    except Exception as e:
        print(e)
        return utc

