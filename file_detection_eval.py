import magika
from polyfile import polyfile as pf
from pathlib import Path
import sys
m = magika.Magika()

def magika_eval(filename):
    path = Path(filename)
    out, features = m._get_result_or_features_from_path(path)
    if out != None:
        continue #TODO implement logic
    preds = m._get_raw_predictions([(path, features)]).flatten()
    preds_labeled = list(zip(labels, preds))
    preds_sorted = sorted(preds_labeled, key=lambda x: x[1], reverse=True)
    return preds_sorted 
pathName = ""
if len(sys.argv) < 2:
    print("Error: No arguments provided.", file=sys.stderr)
    sys.exit(1)

filenames = sys.argv[1:]
resultList = []
labels = m._model_config.target_labels_space
    
for filename in filenames:
    fileEval = {}
    base_name, covert, overt = filename.rsplit('.', 2)
    file_eval['base_name'] = base_name
    file_eval['overt'] = overt
    file_eval['covert'] = covert
    magika_preds = magika_eval(filename)
    file_eval['magika'] = preds_sorted

print(resultList)