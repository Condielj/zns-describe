#!/usr/bin/env python
import datetime as dt
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Union, Optional

import pandas as pd
import requests

from file_type import infer_file_type


@contextmanager
def disable_exception_traceback():
    """
    All traceback information is suppressed and only the exception type and value are printed
    """
    default_value = getattr(sys, "tracebacklimit", 1000)
    sys.tracebacklimit = 0
    yield
    sys.tracebacklimit = default_value  # revert changes


def make_item(row: pd.Series, hs_code_name: str) -> dict:

    return {
        "name": row["description"],
        "description": row["description"],
        "categories": (
            row["category"].split(" > ") if row["category"] == row["category"] else None
        ),
        "configuration": {"hsCodeProvided": row[hs_code_name].replace(".", "")[:6]},
    }


def improve_descriptions_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates an improved item description for a given dataframe
    """

    file_type = infer_file_type(df)
    hs_code_name = file_type.get_hs_code_name()

    items = df.apply(lambda row: make_item(row, hs_code_name), axis=1).to_list()

    query = """mutation GetSimpleClassification($inputs: [ClassificationCalculateInput!]!) {
        classificationsCalculate(input: $inputs) {
            id
            customsDescription
        }
    }
    """

    response = requests.post(
        url="https://classify-gpt3.prod.us-east-2.zdops.net/graphql",
        json={"query": query, "variables": {"inputs": items}},
        headers={"credentialToken": os.getenv("CREDENTIAL_TOKEN")},
    )

    if response.status_code != 200:
        raise (
            ValueError(
                f"Reponse code of {response.status_code} recieved.\n\n{response.text}"
            )
        )

    if "data" not in response.json():
        raise (
            ValueError(
                f'No data returned\n\n{json.dumps(response.json()["errors"],indent=2)})'
            )
        )

    response = response.json()["data"]["classificationsCalculate"]
    df["Optimized Goods Description"] = [
        item["customsDescription"] for item in response
    ]

    return df


def get_output_file(
    input_file: Path, output_file: Optional[Union[str, Path]], overwrite_existing: bool
) -> Path:
    """
    Determine's the output file name if not specified, otherwise checks if it exists and warns
    """

    # If you didn't specify an output file
    if output_file is None:

        # Add a "-with-descriptions" suffix
        output_file = input_file.with_name(
            input_file.stem + "-with-descriptions" + input_file.suffix
        )

        # If it exists, add a number at the end until it doesn't exist
        n = 0
        while output_file.exists():
            output_file = input_file.with_name(
                input_file.stem + f"-with-descriptions-{n}" + input_file.suffix
            )
            n += 1

    else:

        # Convert it to a Path object
        output_file = Path(output_file)

        # If it exists, and you haven't specified you want to force an overwrite
        if output_file.exists() and not overwrite_existing:

            # Warn that it would be overwritten
            raise (
                ValueError(
                    f"""Output file "{output_file}" exists. If you'd like to overwrite it, set the "overwrite_existing" argument to True."""
                )
            )

    return output_file


def validate_input_file(df: pd.DataFrame) -> bool:
    """
    Make sure the input file has all the right columns
    """

    # Define the required columns
    file_type = infer_file_type(df)

    # Calculate the missing columns
    missing_cols = file_type.missing_cols()

    # Yell if there are any missing
    if len(missing_cols):
        raise (ValueError(f"Input file is missing columns {missing_cols}"))

    # Make sure we have an hs_code column
    hs_code_col = file_type.get_hs_code_name()

    if hs_code_col is None:
        raise (
            ValueError(
                'Could not find the hs_code column. It must start with "hs_code"'
            )
        )

    return True


def cli(input_file, output_file, force: bool):

    # Get the input file
    input_file = Path(input_file)

    # Get the output file
    output_file = get_output_file(input_file, output_file, overwrite_existing=force)

    # Read the input file
    df = pd.read_csv(input_file, dtype=str)

    # Make sure the input file is what we expect
    validate_input_file(df)

    # Improve the descriptions
    t_start = dt.datetime.now()
    df = improve_descriptions_df(df)
    t_end = dt.datetime.now()

    # Save the file
    df.to_csv(output_file, index=False)

    # Print the elapsed time
    print(f"Elapsed time: {t_end-t_start}")


def debug(input_file, output_file=None, force: bool = False):

    input_file = Path(input_file)

    # Get the output file
    output_file = get_output_file(input_file, output_file, overwrite_existing=force)

    # Read the input file
    df = pd.read_csv(input_file, dtype=str)

    # Make sure the input file is what we expect
    validate_input_file(df)

    # Improve the descriptions
    t_start = dt.datetime.now()
    df = improve_descriptions_df(df)
    t_end = dt.datetime.now()

    # Save the file
    df.to_csv(output_file, index=False)

    # Print the elapsed time
    print(f"Elapsed time: {t_end-t_start}")


def describe(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    overwrite_existing: bool = False,
) -> pd.DataFrame:

    # Get the input file
    input_file = Path(input_file)

    # get the output file
    output_file = get_output_file(
        input_file, output_file, overwrite_existing=overwrite_existing
    )

    # read the input file
    df = pd.read_csv(input_file, dtype=str)

    # make sure the input file is what we expect
    validated = validate_input_file(df)

    if not validated:
        raise (ValueError("Input file failed validation."))

    # Improve the descriptions
    t_start = dt.datetime.now()
    df = improve_descriptions_df(df)
    t_end = dt.datetime.now()

    # save the file
    df.to_csv(output_file, index=False)

    # print the elapsed time
    print(f"Elapsed time: {t_end-t_start}")

    return df


if __name__ == "__main__":
    """
    Instructions for use:
        One time:
            - Make sure you have a .env file with a valid CREDENTIAL_TOKEN set
            - Set up a virtual environment
                 - 'python3 -m venv env-name'
                 - 'source env-name/bin/activate'
            - Run 'pip install -r requirements.txt' (if that doesn't work, try 'python3 -m pip install -r requirements.txt')
        Each time:
            - Run 'source env-name/bin/activate' if you're not already in the virtual environment
            - Set the input_file path and output_file path variables below.  If output file is not set, it will be '{input-file}-with-descriptions.csv'.  If the file is in the same folder as the script, you can just use the file name.
            - Make sure there are the columns 'category', 'description', and one that starts with 'hs_code'
            - Set overwrite existing to True if you want to overwrite the output file (if it already exists)
            - Run the script via IDE or 'python describe.py'

    """
    input_file = "Adafruit_2025-07-28_classified.csv"
    output_file = None
    overwrite_existing = False  # (True, False) -> Whether or not to overwrite the output file if it already exists

    # ================================
    import dotenv

    dotenv.load_dotenv()

    describe(
        input_file=input_file,
        output_file=output_file,
        overwrite_existing=overwrite_existing,
    )
