import pandas as pd
import json
import re
import polars as pl


def metadata_process():
    df = pd.read_json("raw.jsonl", lines=True)
    df = df.drop(columns=["content"])

    # Export metadata parquet (without relationships)
    metadata_df = df.drop(columns=["relationships"])
    metadata_df.to_parquet("metadata.parquet", index=False)
    print(f"✓ Exported metadata.parquet with shape {metadata_df.shape}")

    # Build relationships dataframe
    relationships_records = []

    for doc_id, relationships_json in zip(df["id"], df["relationships"]):
        rel_obj = (
            json.loads(relationships_json)
            if isinstance(relationships_json, str)
            else relationships_json
        )

        for rel_type, other_ids in rel_obj.items():
            # Remove count from relationship type: "Văn bản căn cứ (1)" -> "Văn bản căn cứ"
            cleaned_rel_type = re.sub(r"\s*\(\d+\)\s*$", "", rel_type)

            # other_ids is a list
            for other_id in other_ids:
                relationships_records.append(
                    {
                        "doc_id": doc_id,
                        "other_doc_id": other_id,
                        "relationship": cleaned_rel_type,
                    }
                )

    relationships_df = pd.DataFrame(relationships_records)
    # other_doc_id should be int too
    relationships_df["other_doc_id"] = relationships_df["other_doc_id"].astype(int)
    relationships_df.to_parquet("relationships.parquet", index=False)
    print(f"✓ Exported relationships.parquet with shape {relationships_df.shape}")

    print(f"\nRelationship types found:")
    print(relationships_df["relationship"].value_counts())


def content_process():
    # scan_ndjson is lazy; sink_parquet streams the result directly to disk
    pl.scan_ndjson("../data/raw.jsonl").sink_parquet("../data/content.parquet")
    print("✓ Exported content.parquet via streaming")


if __name__ == "__main__":
    # metadata_process()
    content_process()
