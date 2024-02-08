#   -------------------------------------------------------------------------------------------------
#
#   This file is just for practice and testing purposes since the final database will require the use
#   of json files to store class information and enrolled students. This program mainly tests reading
#   an existing json file and writing into a new file after modifications are made.
#
#   -------------------------------------------------------------------------------------------------

import json

inputPath = "parse\example.json"
outputPath = "parse\output.json"

# Open file
with open(inputPath, "r") as f:
    data = json.load(f)

# Testing basic insertions into existing data
data['quiz']['math']['q1']['options'].insert(len(data['quiz']['math']['q1']['options']), "20")
data['quiz']['math']['q1']['options'].insert(len(data['quiz']['math']['q1']['options']), "21")
data['quiz']['math']['q1']['options'].insert(len(data['quiz']['math']['q1']['options']), "22")
data['quiz']['math']['q1']['incorrect answer'] = "22"
print("Inserted new data into Math Q1")

# Testing inserting full new entries into data
q3 = {
    "question": "5 + 4 = ?",
    "options": [
        "7", 
        "8", 
        "9", 
        "10"
    ],
    "answer": "9"
}
data['quiz']['math']['q3'] = q3
print("Added Q3 data to Math")

# Close file
with open(outputPath, "w") as f:
    json.dump(data, f)
    
# End
print("Successfully completed")