"""Evaluation script — batch test and measure quality (evaluation.md)."""
from __future__ import annotations
import json, logging, sys
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

TEST_SET: List[Dict] = [
    {"question": "Giết người bị xử lý thế nào?", "expected_law": "hình sự", "expected_article": "Điều 123"},
    {"question": "Quyền thừa kế được quy định thế nào?", "expected_law": "dân sự", "expected_article": ""},
    {"question": "Người lao động bị sa thải trái luật?", "expected_law": "lao động", "expected_article": ""},
    {"question": "Vi phạm nồng độ cồn bị phạt gì?", "expected_law": "giao thông", "expected_article": ""},
    {"question": "Ly hôn chia tài sản thế nào?", "expected_law": "hôn nhân gia đình", "expected_article": ""},
]

def run_evaluation():
    from app.models import ChatRequest
    from app.pipeline import run_pipeline
    from app.classifier import predict_law_type

    results = []
    for tc in TEST_SET:
        # Test classifier
        predicted_law = predict_law_type(tc["question"])
        classifier_correct = predicted_law == tc["expected_law"]

        # Test pipeline
        resp = run_pipeline(ChatRequest(question=tc["question"], lawType=tc["expected_law"]))
        has_answer = resp.data is not None and resp.data.answer != ""
        has_basis = resp.data is not None and len(resp.data.legal_basis) > 0
        confidence = resp.data.confidence if resp.data else "none"
        article_match = tc["expected_article"] in " ".join(resp.data.legal_basis) if resp.data and tc["expected_article"] else None

        results.append({
            "question": tc["question"],
            "expected_law": tc["expected_law"],
            "predicted_law": predicted_law,
            "classifier_correct": classifier_correct,
            "has_answer": has_answer,
            "has_legal_basis": has_basis,
            "confidence": confidence,
            "article_match": article_match,
        })

    # Print report
    print("\n" + "="*70)
    print("EVALUATION REPORT")
    print("="*70)
    total = len(results)
    clf_acc = sum(1 for r in results if r["classifier_correct"]) / total
    ans_rate = sum(1 for r in results if r["has_answer"]) / total
    basis_rate = sum(1 for r in results if r["has_legal_basis"]) / total

    print(f"Classifier Accuracy: {clf_acc:.0%} ({sum(1 for r in results if r['classifier_correct'])}/{total})")
    print(f"Answer Rate:         {ans_rate:.0%}")
    print(f"Legal Basis Rate:    {basis_rate:.0%}")
    print("-"*70)
    for r in results:
        status = "OK" if r["classifier_correct"] else "FAIL"
        print(f"  {status} [{r['predicted_law']:12s}] {r['question'][:50]:50s} conf={r['confidence']}")
    print("="*70)

if __name__ == "__main__":
    run_evaluation()
