import json

file_path = r"c:\Users\Bala murukan\Desktop\Aadhaar_Insight\voter_eligibility_and_turnout_forecast.ipynb"

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Update the header cell (Cell 0)
if nb['cells'] and nb['cells'][0]['cell_type'] == 'markdown':
    source = nb['cells'][0]['source']
    new_source = []
    for line in source:
        # Remove any mentions of turnout/forecast
        clean_line = line.replace(" and turnout forecast", "").replace("and Turnout Forecast", "")
        new_source.append(clean_line)
    nb['cells'][0]['source'] = new_source

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook header cleaned successfully.")
