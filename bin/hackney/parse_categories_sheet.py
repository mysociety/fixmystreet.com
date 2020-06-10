#!/usr/bin/env python

from __future__ import print_function

import json
import os
import pickle
import sys
from collections import defaultdict, namedtuple
from email.utils import parseaddr
from functools import reduce
from string import ascii_lowercase

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import click
import yaml

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

config = None

Row = namedtuple("Row", "group category email wfs_layer devolved")


@click.group()
@click.pass_context
def cli(ctx):
    """
    Parses the Hackney master categories spreadsheet and
    either produces categories.json which can be loaded by import_categories,
    or an layers.js file which sets up the mapping between categories and
    WFS layers and can be copy/pasted into Hackney's assets.js
    """
    global config
    with open("config.yml") as f:
        config = yaml.safe_load(f)

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=config["doc_id"], range=config["sheet_range"])
        .execute()
    )
    values = result.get("values", [])

    if not values:
        print("No data found.", file=sys.stderr)
        sys.exit(1)

    ctx.obj["rows"] = parse_rows(values)


@cli.command()
@click.pass_context
def categories(ctx):
    groups = defaultdict(list)
    for row in ctx.obj["rows"]:
        if not row.email:
            continue
        cat_obj = {
            "category": row.category,
            "email": row.email,
            "devolved": row.devolved,
        }
        if config["categories"].get(row.category, {}).get("extra_fields"):
            cat_obj["extra_fields"] = config["categories"][row.category]["extra_fields"]
        if row.email.count(":") > row.email.count("@"):
            # it's a category that has at least one Alloy destination
            cat_obj["extra_fields"] = [
                *cat_obj.get("extra_fields", []),
                *config["alloy_extra_fields"],
            ]
        elif row.wfs_layer:
            # if it's an email-only category with a WFS layer we want to
            # add an 'asset_id' field
            cat_obj["extra_fields"] = [
                *cat_obj.get("extra_fields", []),
                *config["asset_extra_fields"],
            ]
        groups[row.group].append(cat_obj)
    with open("categories.json", "w") as f:
        json.dump(
            {"disabled_message": config["disabled_message"], "groups": groups},
            f,
            indent=2,
            sort_keys=True,
        )


@cli.command()
@click.pass_context
def assets(ctx):
    TEMPLATE = """fixmystreet.assets.add(wfs_defaults, {{
    http_options: {{
        params: {{
            TYPENAME: "{wfs_layer}",
        }}
    }},
    asset_category: "{category}",
    attributes: {attributes}
}});
"""
    with open("layers.js", "w") as layers:
        for row in ctx.obj["rows"]:
            if not row.email and row.wfs_layer:
                print(
                    f"No email category for WFS layer {row.wfs_layer}, skipping.",
                    file=sys.stderr,
                )
                continue
            if row.wfs_layer and ":" in row.wfs_layer:
                attributes = json.dumps(
                    config["categories"].get(row.category, {}).get("wfs_attributes", {})
                )
                print(
                    TEMPLATE.format(
                        wfs_layer=row.wfs_layer,
                        category=row.category,
                        group=row.group,
                        attributes=attributes,
                    ),
                    file=layers,
                )


def parse_rows(rows):
    all_rows = [parse_row(row) for row in rows]
    return [row for row in all_rows if row is not None]


def parse_row(row):
    last_col = col_to_int(config["sheet_range"].rsplit(":", 1)[1])
    row += [""] * ((last_col + 1) - len(row))
    group = row[col_to_int(config["columns"]["group"])].strip()
    category = row[col_to_int(config["columns"]["category"])].strip()
    email, devolved = parse_email(row)
    wfs_layer = row[col_to_int(config["columns"]["wfs_layer"])].strip()
    if email is None and not wfs_layer:
        print(
            f"WARNING: Skipping row with no email addresses or WFS layer {group} - {category}"
        )
        return None
    finalised = row[col_to_int(config["columns"]["finalised"])]
    if not finalised or finalised.lower().strip() != "finalised":
        print(f"WARNING: Including non-finalised row {group} - {category}")
        # return None
    return Row(group, category, email, wfs_layer, devolved)


def col_to_int(col):
    """Turns a spreadsheet column letter into a 0-based index value"""
    return (
        reduce(lambda r, x: r * 26 + x + 1, map(ascii_lowercase.index, col.lower()), 0)
        - 1
    )


def parse_email(row):
    cols = (config["columns"]["emails"][t] for t in ("park", "estate", "other"))
    # get the actual values from the cells and tidy them up a bit
    emails = [row[col_to_int(col)].strip().lower().split(" ")[0] for col in cols]
    # if all three look like email addresses we need to set the send_method on the eventual contact
    park, estate, other = map(
        # ignore anything that's not an email or 'alloy'
        lambda e: apply_email_replacement(e, row)
        if ("@" in e or e == "alloy")
        else None,
        emails,
    )
    # Ignore any rows that have no email addresses
    if {park, estate, other} - {"alloy", None} == set():
        # Might be an Alloy-only category, or awaiting an email address from Hackney
        return None, None
    # if park or estate is missing, use the 'other' address
    park = park or other
    estate = estate or other
    # There are some park-category rows that only have something in the
    # 'park' or 'estate' cell and not 'other', so pick one to use for everything
    if not all([park, estate, other]):
        present = [e for e in (park, estate, other) if e][0]
        park = park or present
        estate = estate or present
        other = other or present
    if park == estate == other:
        # no need to repeat one address three times
        if "@" in other:
            return other, True  # NB always mark as devolved in this case
        else:
            # Alloy-only, don't include in output
            return None, None
    else:
        return (
            ";".join([f"park:{park}", f"estate:{estate}", f"other:{other}",]),
            all("@" in e for e in (park, estate, other)),
        )


def apply_email_replacement(email, row):
    # TODO replace 'alloy' with an Open311 service code
    if email == "alloy":
        group = row[col_to_int(config["columns"]["group"])].strip()
        category = row[col_to_int(config["columns"]["category"])].strip()
        key = f"{group} - {category}"
        return config["alloy_mapping"].get(key, email)
    elif config.get("email_replacement"):
        email = email.translate(str.maketrans(".@", "__"))
        email = config["email_replacement"].format(email=email)
    return email


if __name__ == "__main__":
    cli(obj={})
