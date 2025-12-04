# Text Annotation Quality Pipeline – Proof of Concept

This repository contains a Python implementation of a small-scale annotation quality pipeline, along with a high-level system design (`design_document.md`) showing how this logic would operate inside a production-grade Azure + Databricks + Snowflake platform.

The PoC implements the exact steps required in the assignment:
1. Read annotation records  
2. Apply confidence filtering  
3. Detect annotator disagreement  
4. Produce a clean, model-ready training dataset in JSONL format  

---

## 1. How to Run the Script

### **Prerequisites**
- Python 3.8+ installed  
- `raw_annotations.csv` located in the same directory as `process_annotations.py`

### **Run the script**

Open Command Prompt and navigate to the folder containing the script:

```bash
cd <path-to-your-folder>
python process_annotations.py
```

### **Outputs generated**

After running the script, two files will appear in the same folder:

* `clean_training_dataset.jsonl` → high-confidence, agreed-upon samples
* `disagreements.log` → texts where annotators disagreed

---

## 2. What the PoC Does

### **(a) Read the raw_annotations.csv file**

Loads every annotation record without applying filters.

### **(b) Quality Check 1: Confidence Filter**

Removes any annotation where `confidence_score < 0.8`.

### **(c) Quality Check 2: Agreement Check**

For each text:

* If all high-confidence annotators agree → include the sample and Write agreed samples to clean_training_dataset.jsonl in JSONL format
* If labels conflict → log the text to `disagreements.log`

### **(d) Output Generation (JSONL)**

Final dataset uses JSON Lines format:

```json
{"text": "<text>", "label": "<label>"}
```

This format is directly compatible with downstream ML pipelines.

---

## 3. How This PoC Fits Into the Larger System

In the full end-to-end annotation pipeline described in `design_document.md`, raw customer text flows through several stages: ingestion, annotation, quality validation, dataset publishing, and lineage tracking.

This PoC represents the **Quality Validator & Training Dataset Generator** component.

### Role in the Production System

* **Azure Data Factory** ingests raw text into ADLS
* **Azure Service Bus** distributes annotation tasks
* **Human/LLM annotators** save labels into **Azure SQL Database**
* **Azure Databricks (Spark)** runs a scalable version of this quality-validation logic
* **ADLS / Snowflake** receive clean, versioned datasets
* **Purview** provides lineage and governance

### How the PoC Maps to the Production Component

| Production Component             | PoC Equivalent                                  |
| -------------------------------- | ----------------------------------------------- |
| Azure SQL annotation store       | `raw_annotations.csv` input                     |
| Spark QC logic in Databricks     | Python QC logic (confidence + agreement checks) |
| Writing cleaned datasets to ADLS | Writing `clean_training_dataset.jsonl` locally  |
| Logging disagreements for QA     | Writing `disagreements.log` locally             |
| Scheduled Databricks job         | Manual local script execution                   |

### Purpose of This Component in the System
This stage ensures that only **high-confidence, agreed-upon annotations** are used for downstream ML workflows. It removes:
- low-quality labels,
- inconsistent annotator decisions,
- ambiguous samples.

This produces a reliable, reproducible dataset that downstream training pipelines can consume.

The PoC demonstrates the exact transformation and validation logic that would be executed at scale in the cloud using Databricks Spark.

---
## 4. Key Decisions and Trade-offs

- **Plain Python vs. PySpark for the PoC**  
  The core quality logic (confidence filtering + agreement checking) is implemented in plain Python for maximal portability and ease of execution by reviewers. In production, the same logic would run as a Databricks Spark job for scale-out processing.

- **JSONL as the output format**  
  JSON Lines was chosen because it is widely used in ML workflows, easy to stream, and straightforward to version in ADLS. Each line is an independent `{text, label}` record, which maps naturally to tokenisation and downstream training pipelines.

- **Separation of annotation storage and training dataset**  
  Annotation events are stored in a relational store (Azure SQL) for transactional reliability and historical analysis.  
Clean, versioned training datasets are written to a file-based store (ADLS), which is cost-efficient, scalable, and ideal for ML ingestion workflows.  
A third layer, Snowflake, is used as the analytical and feature-style environment, enabling fast SQL-based exploration of annotation quality, disagreement trends, and label distributions without touching raw or training data.  

  This separation of concerns simplifies governance, supports reliable backfills, and enables multiple consumers (ML pipelines, analytics teams, monitoring dashboards) to operate independently without coupling.


- **Batch-oriented processing vs. fully streaming**  
  The design uses scheduled batch jobs (via ADF + Databricks) for quality validation and dataset generation. This keeps the system easier to reason about, easier to backfill, and aligns with most model training workflows, while still allowing future extension to streaming if stricter latency requirements emerge.

---
## 5. Files in This Repository

| File                           | Purpose                                                               |
| ------------------------------ | --------------------------------------------------------------------- |
| `design_document.md`           | High-level architecture showing Azure + Databricks + Snowflake design |
| `README.md`                    | Instructions for running the script and PoC-to-system mapping         |
| `raw_annotations.csv`          | Input dataset of raw annotations                                      |
| `process_annotations.py`       | Python script implementing confidence and agreement checks            |
| `clean_training_dataset.jsonl` | Output file containing high-quality agreed samples                    |
| `disagreements.log`            | Output file listing disagreements                                     |

---

## 6. Notes

* The PoC focuses on clarity and correctness rather than scale.
* Production implementation would run on Databricks Spark with dataset versioning, lineage, and orchestration through Azure Data Factory.

```



