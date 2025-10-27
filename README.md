# zns-describe
A helper script to provide customs descriptions to a CSV in bulk.  Requires a Zonos API credential.

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