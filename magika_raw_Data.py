import magika
from pathlib import Path
import sys
m = magika.Magika()
pathName = ""
if len(sys.argv) < 2:
    print("Error: No arguments provided.", file=sys.stderr)
    sys.exit(1)

filenames = sys.argv[1:]
resultList = []
labels = m._model_config.target_labels_space
    
for filename in filenames:
    path = Path(filename)
    out, features = m._get_result_or_features_from_path(path)
    if out != None:
        continue #TODO implement logic
    preds = m._get_raw_predictions([(path, features)]).flatten()
    preds_labeled = list(zip(labels, preds))
    preds_sorted = sorted(preds_labeled, key=lambda x: x[1], reverse=True)
    resultList.append((path, preds_sorted))
    
print(resultList)



if __name__ == "__main__":
    basePath = Path(__file__).parent.parent