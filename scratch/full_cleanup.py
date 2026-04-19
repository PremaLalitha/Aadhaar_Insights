import json
import os

files_to_clean = [
    r"c:\Users\Bala murukan\Desktop\Aadhaar_Insight\voter_eligibility_and_turnout_forecast.ipynb",
    r"c:\Users\Bala murukan\Desktop\Aadhaar_Insight\dataset1.ipynb"
]

def clean_notebook(path):
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    new_cells = []
    for cell in nb['cells']:
        source = cell['source']
        if isinstance(source, str):
            source = [source]
        
        # Check if cell contains "future_voters" or "ARIMA" or "turnout"
        contains_forbidden = any("future_voters" in line or "ARIMA" in line or "turnout" in line.lower() for line in source)
        
        if contains_forbidden:
            # For dataset1.ipynb, we just want to remove the specific line, not the whole cell
            # unless the whole cell is about it.
            filtered_source = [line for line in source if "future_voters" not in line and "ARIMA" not in line and "turnout" not in line.lower()]
            if filtered_source:
                cell['source'] = filtered_source
                new_cells.append(cell)
        else:
            new_cells.append(cell)
    
    nb['cells'] = new_cells
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print(f"Cleaned {os.path.basename(path)}")

for p in files_to_clean:
    clean_notebook(p)
