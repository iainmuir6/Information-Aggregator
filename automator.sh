#!/bin/bash

# Switch to Correct Directory
cd /Users/iainmuir/PycharmProjects/Desktop/PersonalProjects/Information-Aggregator || exit

# Activate Virtual Environment
source bin/activate

# Connect to Datapane API
datapane login --token=55010cebc170ecfbeddb82838c360776bf36f6be

# Run Jupyter Notebook
jupyter nbconvert --to notebook --execute aggregator.ipynb --output aggregator.ipynb

# Deactivate Virtual Environment
deactivate

# Commit updated run log
git commit -m "daily run; updating log..." -- run_log.txt
git push