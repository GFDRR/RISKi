'''Command-line utility for RISKi'''

import glob
import subprocess
import os

import typer

import riski as ri
from riski._utils import load_settings, generate_config
from riski.cli import templates


app = typer.Typer()
app.add_typer(templates.app, name="template")

r_conn = ri.RDLConnection(".settings.yaml", db_name='dev')


@app.command()
def setup_dev_db():
    r_conn.switch_db('dev')
    r_conn.create_schema()


@app.command()
def create_rdl_data_config(db_name: str):
    """Create rdl-data config files. Target specified DB."""
    r_conn.switch_db(db_name)
    generate_config(r_conn.settings, db_name)


@app.command()
def import_hazard(db_name: str, json_fn: str):
    """Import experimental JSON format for hazard data type."""
    if db_name != 'dev':
        print("This command only available for local dev at the moment.")
        return
    r_conn.switch_db(db_name)
    r_conn.import_hazard_json(json_fn)


@app.command()
def import_exposure(db_name: str, csv_fn: str, xml_fn: str):
    r_conn.switch_db(db_name)
    r_conn.import_exposure_event(xml_fn)





@app.command()
def local_export(db_name: str):
    """Temporary command to investigate CSV dump issue - remove when ready"""
    r_conn.switch_db(db_name)
    r_conn._export_exposure()


@app.command()
def backup_db_schema(fn: str):
    """Work in progress"""
    # "C:\Program Files\PostgreSQL\13\bin\pg_dump.exe" --file "C:\\Users\\takuy\\DOWNLO~1\\rdl_rb_test.SQL" --host "risk-data-library-dev-1.clmhhevrqy4f.ap-southeast-2.rds.amazonaws.com" --port "5432" --username "tiwanaga" --verbose --role "tiwanaga" --format=p --schema-only --create --clean --encoding "UTF8" --exclude-table public.*temp* "rdl" 
    pass


@app.command()
def backup_db_data(fn: str):
    """Work in progress"""
    # "C:\Program Files\PostgreSQL\13\bin\pg_dump.exe" --file "C:\\Users\\takuy\\DOCUME~1\\rdl_live_bkup.sql.tar" 
    # --host "risk-data-library-dev-1.clmhhevrqy4f.ap-southeast-2.rds.amazonaws.com" --port "5432" --username "tiwanaga" 
    # --verbose --role "tiwanaga" --format=t --blobs --create --clean --section=pre-data --section=data --section=post-data 
    # --encoding "UTF8" --exclude-table public.*temp* "rdl"
    pass


def main():
    app()


if __name__ == '__main__':
    app()
