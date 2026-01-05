#!/usr/bin/env python3
"""Analyze polyglot detection results"""

import json
from collections import defaultdict
from pathlib import Path

def analyze_results(results_file: Path):
    with open(results_file) as f:
        data = json.load(f)

    results = data['results']
    polyglots = [r for r in results if r.get('is_polyglot', True)] 
    monoglots = [r for r in results if not r.get('is_polyglot', True)]
    print(f"Total files evaluated: {len(results)}")
    print(f"Polyglots: {len(polyglots)}")
    print(f"Monoglots: {len(monoglots)}")
    print(f"Timestamp: {data['timestamp']}\n")

    detectors = ['file', 'magika', 'polyfile', 'polydet'] 
    all_positives = {}
    all_fp = {}
    print("polyglot detection rate")
    for name in detectors:
        positives = sum(1 for p in polyglots if p['detectors'][name]['is_polyglot'])
        all_positives[name] = positives
        error_count = sum(1 for p in polyglots if p['detectors'][name].get('error'))
        valid_count = len(polyglots) - error_count
        detect =positives / valid_count * 100
        print(f"{name} {positives}/{valid_count} = {detect}%; errors: {error_count}")
    print("\nmonoglot false positive rate:")
    for name in detectors:
        fp_count = sum(1 for r in monoglots if r['detectors'][name]['is_polyglot'])
        all_fp[name] = fp_count
        error_count = sum(1 for r in monoglots if r['detectors'][name].get('error'))
        valid_count = len(monoglots) - error_count
        fp = fp_count / valid_count * 100
        print(f"{name} {fp_count}/{valid_count} = {fp}%; errors: {error_count}")
    print("\nprecision (polyglots only):")
    for name in detectors:
        fp = all_fp[name]
        p = all_positives[name]
        if p+fp > 0:
            precision = p / (p+fp)
        else:
            precision = 0
        print(f"{name}: {precision}")
        
    print("\novert format detection rate & exact")
    for name in detectors:
        det_overt = 0
        det_exact = 0
        for r in results:
            overt = r['overt_format']
            covert = r['covert_format']
            types = r['detectors'][name]['detected_types']
            if overt in types:
                det_overt +=1
            if overt in types and (covert == "" or covert in types) and len(types) <= 2:
                det_exact +=1
        rate1 = det_overt / len(results) * 100
        rate2 = det_exact / len(results )* 100
        print(f"{name} {det_overt}/{len(results)} = {rate1}%)")
        print(f"exact: {det_exact}/{len(results)} = {rate2}%")

if __name__ == "__main__":
    f = Path("generated/detection_results.json")
    analyze_results(f)
