#!/bin/bash
#use this to submit to a competition

# Exit on any error
set -e

# Ensure the script is called with at least one argument
if [ $# -lt 1 ]; then
    echo "Usage: $0 <filename> [comment]"
    exit 1
fi

# Parse arguments
INPUT_PATH=$1
COMMENT=$2

# Normalize the file path
if [[ $INPUT_PATH == ./results/* ]]; then
    FILE_PATH=$INPUT_PATH
else
    FILE_PATH="./results/$INPUT_PATH"
fi

# Infer competition name from the current directory
COMPETITION_NAME=$(basename "$(pwd)")
echo $COMPETITION_NAME

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Path to the YAML file relative to the script
CONFIG_FILE="$SCRIPT_DIR/../config/comp_cfg.yaml"

# Check if the YAML file exists
if [ -f "$CONFIG_FILE" ]; then
    # Use awk to parse the YAML file for the matching key within the competitions block
    YAML_COMPETITION_NAME=$(awk -v key="$COMPETITION_NAME" '
        BEGIN { in_competitions = 0 }
        /^[[:space:]]*competitions:/ { in_competitions = 1; next }
        in_competitions && /^[[:space:]]+[A-Za-z0-9 ]+:/ {
            # Match the key and extract its value
            gsub(/:/, "", $1)  # Remove the trailing colon
            if ($1 == key) {
                print $2
                exit
            }
        }
    ' "$CONFIG_FILE")

    # Remove quotes if the value is quoted
    YAML_COMPETITION_NAME=$(echo "$YAML_COMPETITION_NAME" | tr -d '"')

    # Update the competition name if a match is found
    if [ -n "$YAML_COMPETITION_NAME" ]; then
        COMPETITION_NAME="$YAML_COMPETITION_NAME"
    else
        echo "Error: Could not find competition name in $CONFIG_FILE for key $COMPETITION_NAME"
        exit 1
    fi
else
    echo "Error: Config file $CONFIG_FILE does not exist."
    exit 1
fi


echo $COMPETITION_NAME

# Ensure the file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' does not exist."
    exit 1
fi

# Submit to Kaggle
if [ -n "$COMMENT" ]; then
    echo "Submitting '$FILE_PATH' to competition '$COMPETITION_NAME' with comment '$COMMENT'..."
    kaggle competitions submit -c "$COMPETITION_NAME" -f "$FILE_PATH" -m "$COMMENT"
else
    echo "Submitting '$FILE_PATH' to competition '$COMPETITION_NAME'..."

    kaggle competitions submit -c "$COMPETITION_NAME" -f "$FILE_PATH"
fi

echo "Submission completed!"
