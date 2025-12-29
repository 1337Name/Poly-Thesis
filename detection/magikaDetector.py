from .baseDetector import BaseDetector
from .types import DetectionResult
from pathlib import Path
from typing import List
import magika

class MagikaDetector(BaseDetector):
    def __init__(self, threshold : float = 0.1):
        super().__init__()
        self._threshold = threshold
        self._magika = magika.Magika() #do it just once
        self._labels = self._magika._model_config.target_labels_space


    def _get_name(self) -> str:
        return "magika"
    def detect(self, path: Path) -> DetectionResult:
        try:
            preds = self._run(path)
            relevant = [(l,s) for l,s in preds if s > self._threshold]
            normalized = self._normalize([l for l,_ in relevant])
            return self._make_result(normalized, preds)
        except Exception as exception:
            return self._make_error(exception)

    def _run(self, path: Path) -> list:
        out, features = self._magika._get_result_or_features_from_path(path)
        if out != None:
            #https://github.com/google/magika/blob/main/python/src/magika/types/magika_result.py
            #https://github.com/google/magika/blob/main/python/src/magika/types/content_type_info.py#L26
            return [(out.output.label, out.output.score)]
        preds = self._magika._get_raw_predictions([(path, features)]).flatten()
        preds_labeled = list(zip(self._labels, preds))
        preds_sorted = sorted(preds_labeled, key=lambda x: x[1], reverse=True)
        return preds_sorted        