import os
import glob
import yaml
from pathlib import Path
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd

class KaggleUtils:
    def __init__(self, yaml_file='config/comp_cfg.yaml', data_path="../data/raw_dataset", competition_name = None):
        self.api = KaggleApi()
        self.api.authenticate()
        self.yaml_file = yaml_file
        self.data_path = data_path
        self.competition_name = competition_name if competition_name else self.infer_competition_name()

    def download(self):
        """
        Download and unzip data from a Kaggle competition, avoiding re-download if CSV files already exist.
        """
        if os.path.exists(self.data_path):
            csv_files = glob.glob(os.path.join(self.data_path, "*.csv"))
            if csv_files:
                print(f"CSV files already exist in {self.data_path}. Skipping download.")
                return
        else:
            os.makedirs(self.data_path)

        print(f"Downloading data for competition {self.competition_name}...")
        self.api.competition_download_files(self.competition_name, path=self.data_path)

        zip_file_path = next((os.path.join(self.data_path, file) for file in os.listdir(self.data_path) if file.endswith(".zip")), None)
        if not zip_file_path:
            print("No zip file found in the downloaded data.")
            return

        print(f"Unzipping {zip_file_path}...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_path)
        os.remove(zip_file_path)
        print(f"Data has been downloaded and unzipped to {self.data_path}")

    def submit(self, file_name, message=''):
        """
        Submit a file to the Kaggle competition.
        """
        try:
            full_file_name = self.infer_submission_file(file_name)
            print(f"Submitting file: {full_file_name} to competition: {self.competition_name}")

            self.api.competition_submit(
                file_name=full_file_name,
                competition=self.competition_name,
                message=message
            )
            print(f"Submission to '{self.competition_name}' successful!")
        except Exception as e:
            print(f"Error during submission: {e}")

    def get_submission_scores(self):
        """
        Retrieve submission scores for the competition.
        """
        submissions = self.api.competitions_submissions_list(self.competition_name)
        if not submissions:
            return None

        submissions_df = pd.DataFrame(submissions)
        submissions_df["date"] = pd.to_datetime(submissions_df["date"])

        submissions_df=submissions_df.sort_values(by='date',ascending=False)

        return submissions_df

    def get_latest_score(self, return_submission_row=False):
        """
        Retrieve the latest submission score.
        """
        submissions_df = self.get_submission_scores()
        if submissions_df is None or submissions_df.empty:
            print(f"No submissions found for competition {self.competition_name}")
            return

        latest_submission = submissions_df.iloc[0]
        if latest_submission.status == "complete":
            score = latest_submission.publicScore
            filename = latest_submission.fileName
            print(f"Latest submission '{filename}' score: {score}")
        else:
            print(f"Latest submission status is not 'complete'. Check: https://www.kaggle.com/competitions/{self.competition_name}/submissions")

        return latest_submission if return_submission_row else latest_submission.publicScore

    def infer_competition_name(self):
        """
        Infer the competition name based on the current directory and YAML configuration.
        """
        cwd = os.getcwd()
        path_parts = cwd.split(os.sep)

        try:
            kaggle_index = path_parts.index("Kaggle")
            competition_folder = path_parts[kaggle_index + 1]
            yaml_path = os.path.join(os.sep.join(path_parts[:kaggle_index + 1]), self.yaml_file)

            with open(yaml_path, 'r') as file:
                yaml_data = yaml.safe_load(file)

            if 'competitions' in yaml_data and competition_folder in yaml_data['competitions']:
                return yaml_data['competitions'][competition_folder]
            else:
                raise ValueError(f"Competition name '{competition_folder}' not found in YAML file.")
        except (ValueError, IndexError) as e:
            raise ValueError("Could not infer competition name. Ensure you are running from a directory nested under 'Kaggle/<competition_name>'.") from e

    def infer_submission_file(self, file_name):
        """
        Construct the relative path to the submission file based on the current working directory.
        """
        file_path = Path(file_name).name
        cwd = os.getcwd()
        path_parts = cwd.split(os.sep)

        kaggle_index = path_parts.index("Kaggle")
        nested_levels = len(path_parts) - (kaggle_index + 2)
        full_relative_path = os.path.join('../' * nested_levels, 'results', file_path)

        return full_relative_path
