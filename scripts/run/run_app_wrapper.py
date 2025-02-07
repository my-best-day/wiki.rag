"""
A wrapper for running the app.
"""
import os
from run_app import main

# Set environment variables dynamically
os.environ["OPENAI_API_KEY"] = open(os.path.expanduser("~/.openai_api_key_1")).read().strip()
os.environ["OPENAI_PROJECT_ID"] = open(os.path.expanduser("~/.openai_project_id")).read().strip()
os.environ["CONFIG_FILE"] = "pl256_config.ini"

main()
