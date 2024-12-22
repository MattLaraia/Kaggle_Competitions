import os
import kaggle
import glob
import yaml
from pathlib import Path
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd


def download(competition_name, download_path="../data/raw_dataset"):
    """
    Download and unzip data from a Kaggle competition, but only if the data 
    hasn't already been downloaded (checks for CSV files in the download path).

    :param competition_name: Kaggle competition name (e.g., 'playground-series-s4e12')
    :param download_path: Directory where the data will be downloaded and unzipped
    """
    # Check if the directory exists and contains CSV files
    if os.path.exists(download_path):
        csv_files = glob.glob(os.path.join(download_path, "*.csv"))
        if csv_files:
            print(f"CSV files already exist in {download_path}. Skipping download.")
            return
    else:
        os.makedirs(download_path)
    
    # Set up Kaggle API client
    api = KaggleApi()
    api.authenticate()

    # Download the dataset for the competition
    print(f"Downloading data for competition {competition_name}...")
    api.competition_download_files(competition_name, path=download_path)

    # Find the zip file in the download path
    zip_file_path = None
    for file in os.listdir(download_path):
        if file.endswith(".zip"):
            zip_file_path = os.path.join(download_path, file)
            break

    if not zip_file_path:
        print("No zip file found in the downloaded data.")
        return

    # Unzip the downloaded file
    print(f"Unzipping {zip_file_path}...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(download_path)

    # Optionally, remove the zip file after extraction
    os.remove(zip_file_path)
    print(f"Data has been downloaded and unzipped to {download_path}")



def submit(file_name, message=''):
    """
    Submits a file to the Kaggle competition inferred from the directory structure.

    :param file_name: The submission file name (e.g., 'submission.csv')
    :param message: A custom message for the submission
    """
    try:
        # Infer competition name and file path
        competition_name = infer_competition_name()
        full_file_name = infer_submission_file(file_name)

        # Print debugging info
        print(f"Competition Name: {competition_name}")
        print(f"Full Submission File Path: {full_file_name}")

        # Submit to Kaggle API
        kaggle.api.competition_submit(
            file_name=full_file_name,
            competition=competition_name,
            message=message
        )
        print(f"Submission to '{competition_name}' successful!")

        submissions =  kaggle.api.competitions_submissions_list(competition_name)

        submissions = pd.DataFrame(submissions)

        sub_score = submissions.iloc[0]["publicScoreNullable"]

        print(f"submission score: {sub_score}")
    except Exception as e:
        print(f"Error during submission: {e}")

def infer_competition_name(yaml_file='config/comp_cfg.yaml'):
    """
    Infers the competition name from the directory structure.
    Assumes the directory structure has the competition name as the folder
    nested under 'Kaggle' and looks it up in the given YAML file.

    Args:
        yaml_file (str): The relative path to the YAML file containing competition names.
    
    Returns:
        str: The competition name as per the YAML mapping.
    """
    # Get the current working directory
    cwd = os.getcwd()
    # print(f"Current working directory: {cwd}")
    
    # Split the path into components
    path_parts = cwd.split(os.sep)

    # Find the 'Kaggle' folder in the path
    try:
        kaggle_index = path_parts.index("Kaggle")
        competition_name = path_parts[kaggle_index + 1]  # The next folder is the competition name

        # Rebuild the path to the 'Kaggle' directory
        kaggle_path = os.path.join(os.sep.join(path_parts[:kaggle_index + 1]))

        # Construct the absolute path to the YAML file
        yaml_path = os.path.normpath(os.path.join(kaggle_path, yaml_file))

        # print(f"Resolved YAML file path: {yaml_path}")

        # Load the YAML file and extract the competition name from the mapping
        with open(yaml_path, 'r') as file:
            yaml_data = yaml.safe_load(file)

        # Ensure 'competitions' key exists in the YAML
        if 'competitions' in yaml_data and competition_name in yaml_data['competitions']:
            return yaml_data['competitions'][competition_name]
        else:
            raise ValueError(f"Competition name '{competition_name}' not found in YAML file.")
    
    except (ValueError, IndexError) as e:
        raise ValueError("Could not infer competition name. Ensure you are running from a directory nested under 'Kaggle/<competition_name>'.") from e

def infer_submission_file(file_name):
    """
    Infer submission path from the relative path.

    :param file_name: The expected filename (assumes file is located in the 'results' directory)
    :return: The full relative path to the submission file
    """
    # Turn file_name into a Path object
    file_path = Path(file_name)

    # Extract the part of the path nested within 'results' (e.g., 'results/mean.csv' should return 'mean.csv')
    relative_file_name = file_path.name

    # Based on cwd, determine how many more nested directories after "Kaggle"
    cwd = os.getcwd()
    # print(f"Current working directory: {cwd}")
    
    # Split the path into components
    path_parts = cwd.split(os.sep)

    # Find the 'Kaggle' folder in the path
    kaggle_index = path_parts.index("Kaggle")

    # Calculate the nested levels after 'Kaggle'
    nested_levels = len(path_parts) - (kaggle_index + 2)  # +1 to account for the 'Kaggle' and competition_name folders

    # Construct the full relative path to the submission file
    full_relative_path = os.path.join('../' * nested_levels, 'results', relative_file_name)

    # print(f"Resolved submission file path: {full_relative_path}")
    return full_relative_path



