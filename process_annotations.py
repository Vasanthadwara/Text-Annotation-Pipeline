"""
This script processes text annotation records by:
1. Reading raw annotations from CSV
2. Applying confidence filtering
3. Detecting annotator disagreement
4. Producing:
   - clean_training_dataset.jsonl
   - disagreements.log
This implements the PoC described in design_document.md.
"""

import csv
import json
from collections import defaultdict

INPUT_FILE = "raw_annotations.csv"
CLEAN_OUTPUT_FILE = "clean_training_dataset.jsonl"
DISAGREEMENTS_LOG_FILE = "disagreements.log"

CONFIDENCE_THRESHOLD = 0.8

""" Read all rows from raw_annotations.csv into a list of dicts  """
def read_raw_annotations(input_path: str):
   
    annotations = []
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotations.append(row)
    return annotations


""" Quality Check 1 (Confidence): Filter out any annotation with confidence_score < 0.8 """
def filter_by_confidence(annotations, threshold: float):
    
    filtered = []

    for row in annotations:
        try:
            confidence = float(row["confidence_score"])
        except (KeyError, ValueError):
            # If confidence is missing or invalid, treat as failing QC1
            continue

        if confidence >= threshold:
            filtered.append(
                {
                    "text": row["text"],
                    "annotator_id": row.get("annotator_id"),
                    "label": row["label"],
                    "confidence_score": confidence,
                }
            )

    return filtered


""" Group annotations by text after QC1 """
def group_by_text(annotations):   
    grouped = defaultdict(list)
    for ann in annotations:
        grouped[ann["text"]].append(ann)
    return grouped


""" Quality Check 2 (Agreement): For the remaining annotations, identify any text samples where annotators disagreed."""
def apply_agreement_check(grouped_annotations):
    agreed_samples = {}
    disagreements = []

    for text, anns in grouped_annotations.items():
        labels = {a["label"] for a in anns}

        if len(labels) == 1:
            # All high-confidence labels agree
            agreed_samples[text] = labels.pop()
        else:
            # High-confidence disagreement for this text
            disagreements.append((text, labels))

    return agreed_samples, disagreements


""" Output Generation:
#    - Log disagreements to disagreements.log
#    - Write agreed samples to clean_training_dataset.jsonl in JSONL format """
def write_outputs(agreed_samples, disagreements, clean_path, disagreements_path):

    # Write JSONL for clean training dataset
    with open(clean_path, mode="w", encoding="utf-8") as clean_f:
        for text, label in agreed_samples.items():
            record = {"text": text, "label": label}
            clean_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Write disagreements log
    with open(disagreements_path, mode="w", encoding="utf-8") as log_f:
        for text, labels in disagreements:
            label_list = ", ".join(sorted(labels))
            log_f.write(f'TEXT: {text} | LABELS: {label_list}\n')


def main():
    # a) Read the raw_annotations.csv file.
    print("Step (a): Reading raw annotations...")
    raw_annotations = read_raw_annotations(INPUT_FILE)
    print(f"Total raw annotations loaded: {len(raw_annotations)}")

    # b) Quality Check 1 (Confidence)
    print("Step (b): Applying confidence filter...")
    high_conf_annotations = filter_by_confidence(raw_annotations, CONFIDENCE_THRESHOLD)
    print(f"Annotations after QC1 (confidence >= {CONFIDENCE_THRESHOLD}): {len(high_conf_annotations)}")

    # Group by text after QC1
    grouped = group_by_text(high_conf_annotations)
    print(f"Unique texts after QC1: {len(grouped)}")

    # c) Quality Check 2 (Agreement)
    print("Step (c): Checking for agreement/disagreements...")
    agreed_samples, disagreements = apply_agreement_check(grouped)
    print(f"Texts with agreement: {len(agreed_samples)}")
    print(f"Texts with disagreements: {len(disagreements)}")

    # d) Output Generation
    print("Step (d): Writing outputs...")
    write_outputs(agreed_samples, disagreements, CLEAN_OUTPUT_FILE, DISAGREEMENTS_LOG_FILE)

    print("\nDone!")
    print(f"✔ Clean training dataset: {CLEAN_OUTPUT_FILE}")
    print(f"✔ Disagreements log: {DISAGREEMENTS_LOG_FILE}")


if __name__ == "__main__":
    main()
