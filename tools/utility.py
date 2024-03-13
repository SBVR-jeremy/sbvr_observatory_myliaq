#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""utility.py: This file contains functions shared aver the application"""

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
import streamlit as st

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

def utc2local(utc):
    #Use this function to display datetime as local time
    try:
        return utc.astimezone(tz.tzlocal())
    except Exception as e:
        print(e)
        return utc

def hide_rainbow_bar():
    hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
        .css-z5fcl4 {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        [data-testid="stSidebarNav"] {
            padding-top: 52px;
        }
        
    </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

def hide_streamlit_credits():
    hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
    st.markdown(hide_default_format, unsafe_allow_html=True)


DEFAULT = ' --- '
def selectbox_with_default(text, values, default=DEFAULT, sidebar=False, index=0):
    func = st.sidebar.selectbox if sidebar else st.selectbox
    return func(text, np.insert(np.array(values, object), index, default))
