from typing import Dict, List, Optional
from types import MethodType
import warnings

import os
import re
import inspect

import psycopg2 as pg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import numpy as np
import pandas.io.sql as psql
import pandas as pd

from ._utils import load_settings
from . import hazard, _xml_funcs, _local_export


class RDLConnection(object):

    def __init__(self, settings: str, tmp_table: str = None, # dev: bool = False, 
                 db_name: str = None, verbose: bool = True):
        """Constructor for RDLConnection.

        Parameters
        ----------
        settings : str,
            Path to settings file in yaml format.

        tmp_table : str (default: 'tablename'),
            name of temporary table to use
        
        dev : bool (default: False),
            Whether to use local development server or not.

        """
        # Load in settings
        self.settings = load_settings(settings)
        self.verbose = verbose
        self.current_db = None

        # Create settings for DB entry
        self.switch_db(db_name)

        self.current_db = db_name

        if tmp_table is None:
            self.tmp_table = self.settings['database']['tmp_table']
        else:
            self.tmp_table = tmp_table
        
        # Dynamically attach additional methods
        funcs = inspect.getmembers(hazard, inspect.isfunction)
        funcs += inspect.getmembers(_xml_funcs, inspect.isfunction)
        funcs += inspect.getmembers(_local_export, inspect.isfunction)
        for name, func in funcs:
            setattr(self, name, MethodType(func, self))

    def switch_db(self, name: str):
        assert name in list(self.settings['database'].keys()), \
            "DB name/config not listed in settings file"

        if name == self.current_db:
            return

        rdl_db_settings = self.settings['database'][name]

        if name == 'dev':
            # remove psql entry as it is unneeded
            # this will eventually be removed in the future as direct 
            # interaction via the command-line will not be needed 
            rdl_db_settings.pop('psql', None)
            
            self._verbose_msg("Connected to local dev server")
        
        user = rdl_db_settings['user']
        password = rdl_db_settings['password']
        host = rdl_db_settings['host']
        port = rdl_db_settings['port']
        dbname = rdl_db_settings['dbname']

        conn_string = " ".join([f"{k}='{v}'" for (k, v) in rdl_db_settings.items()])
        self.conn = pg.connect(conn_string)

        # sqlalchemy connection string
        engine_conn = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_engine(engine_conn)

        self.engine_conn = engine_conn

        # OS environment variable to interface with rdl-infra
        os.environ["POSTGRES_CONNECTION_STRING"] = conn_string

        self.current_db = name

    def create_schema(self):
        from riski.schema import Base
        
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def _create_temp_table(self, struct):
        """Create a temporary table for the data import.

        Parameters
        ----------
        struct : List[tuple],
            Table column structure in the form of [("column name", "data type"), ]
        """
        self._remove_temp_table()  # remove table if it already exists

        columns = ",\n".join([f"{k} {v}" for k, v in struct])
        query = """CREATE TABLE {}({})""".format(self.tmp_table, columns)

        with self.conn.cursor() as cur:
            cur.execute(query)

        self.conn.commit()

    def _remove_temp_table(self):
        """Deletes temporary table from database."""
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS {}".format(self.tmp_table))

        self.conn.commit()

    def run_query(self, query):
        """Run an arbitrary SQL query."""

        data = psql.read_sql_query(query, self.conn)

        return data

    def _str_type(self, form: str):
        """Interpret string to printf-style data type.

        Returns
        -------
        str, '%f', '%i', '%s' for float, integer, or string
        """
        form = form.lower()
        if form.startswith('f'):
            return r'%f'
        elif form.startswith('i'):
            return r'%i'
        elif form.startswith('s'):
            return r'%s'
        else:
            raise ValueError(f"Unknown data type: {form}")
    
    # def _ensure_location(self, columns):
    #     location_id = "LocID" in columns
    #     lon = "lon" in columns
    #     lat = "lat" in columns
        
    #     if location_id and lon and lat:
    #         return

    #     raise ValueError("Provided CSV does not specify LocID, lon, or lat\n{}".format(columns))

    def _verbose_msg(self, msg):
        if self.verbose:
            print(msg)

    def __del__(self):
        # Clean up on destruction
        # self._remove_temp_table()  # remove table if exists

        try:
            self.conn.close()  # close connection
        except AttributeError:
            pass

    def __exit__(self):
        # Clean up on exit
        # self._remove_temp_table()  # remove table if exists
        try:
            self.conn.close()  # close connection
        except AttributeError:
            pass
