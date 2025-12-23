#!/usr/bin/env python3
"""
Batch Content Completeness Check
Run completeness checker on multiple PDFs to get overall statistics
"""

import sys
from pathlib import Path
from content_completeness_checker import ContentCompletenessChecker
import json
import random


def batch_check(output_base: str, sample_size: int = 5):
    """Check completeness of multiple conversions"""
    output_path = Path(output_base)
    input_path = Path("/Users/yotam/PDF-JSON/Input")

    if not output_path.exists():
        print(f"❌ Output directory not found: {output_base}")
        return

    # Find all output directories
    output_dirs = [d for d in output_path.iterdir()
                   if d.is_dir() and d.name.endswith("_v2")]

    print("=" * 80)
    print(f"BATCH CONTENT COMPLETENESS CHECK")
    print("=" * 80)
    print(f"Total conversions: {len(output_dirs)}")
    print(f"Checking sample of {min(sample_size, len(output_dirs))} conversions...")
    print("=" * 80)

    # Sample random directories
    sample_dirs = random.sample(output_dirs, min(sample_size, len(output_dirs)))

    results = []
    scores = []

    for i, output_dir in enumerate(sample_dirs, 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}/{len(sample_dirs)}] Checking: {output_dir.name}")
        print("=" * 80)

        # Find corresponding PDF
        # Try different naming patterns
        base_name = output_dir.name.replace("_v2", "")

        # Try to find matching PDF
        pdf_file = None
        for pdf in input_path.glob("*.pdf"):
            pdf_safe_name = pdf.stem.replace("[", "").replace("]", "").replace(" ", "_")
            if base_name.lower() in pdf_safe_name.lower() or pdf_safe_name.lower() in base_name.lower():
                pdf_file = pdf
                break

        if not pdf_file:
            print(f"⚠️  Could not find matching PDF for {output_dir.name}")
            continue

        checker = ContentCompletenessChecker(str(pdf_file), str(output_dir))
        result = checker.run_full_check()

        if result:
            results.append(result)
            scores.append(result["scores"]["percentage"])

            # Save individual report
            report_file = output_dir / "content_completeness_report.json"
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2)

    # Overall summary
    if results:
        print("\n" + "=" * 80)
        print("BATCH COMPLETENESS SUMMARY")
        print("=" * 80)

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        print(f"\nTotal PDFs checked: {len(results)}")
        print(f"\nScore Statistics:")
        print(f"  Average: {avg_score:.1f}%")
        print(f"  Min: {min_score:.1f}%")
        print(f"  Max: {max_score:.1f}%")

        # Grade distribution
        excellent = sum(1 for s in scores if s >= 80)
        good = sum(1 for s in scores if 60 <= s < 80)
        fair = sum(1 for s in scores if 40 <= s < 60)
        poor = sum(1 for s in scores if s < 40)

        print(f"\nGrade Distribution:")
        print(f"  ✅ Excellent (80-100%): {excellent} ({excellent/len(scores)*100:.0f}%)")
        print(f"  ✓ Good (60-79%): {good} ({good/len(scores)*100:.0f}%)")
        print(f"  ⚠️ Fair (40-59%): {fair} ({fair/len(scores)*100:.0f}%)")
        print(f"  ❌ Poor (<40%): {poor} ({poor/len(scores)*100:.0f}%)")

        # Category averages
        print(f"\nAverage Scores by Category:")
        categories = ["titles", "content_volume", "activities", "structure",
                     "standards", "learning_goals", "metadata"]
        category_maxes = {"titles": 10, "content_volume": 20, "activities": 25,
                         "structure": 15, "standards": 10, "learning_goals": 10,
                         "metadata": 10}

        for cat in categories:
            cat_scores = [r["scores"].get(cat, 0) for r in results]
            cat_avg = sum(cat_scores) / len(cat_scores)
            cat_max = category_maxes[cat]
            cat_pct = (cat_avg / cat_max * 100) if cat_max > 0 else 0
            print(f"  {cat.replace('_', ' ').title()}: {cat_avg:.1f}/{cat_max} ({cat_pct:.0f}%)")

        # Common issues
        print(f"\nMost Common Missing Content:")
        all_missing = []
        for r in results:
            all_missing.extend(r["missing_content"])

        # Count occurrences
        from collections import Counter
        issue_counts = Counter(all_missing)

        for issue, count in issue_counts.most_common(10):
            print(f"  • {issue} ({count}/{len(results)} PDFs)")

        # Overall verdict
        print(f"\n" + "=" * 80)
        print("OVERALL VERDICT")
        print("=" * 80)

        if avg_score >= 80:
            print("✅ JSON outputs are comprehensive enough for markdown/XML generation")
            print("   Content extraction is working well.")
        elif avg_score >= 60:
            print("✓ JSON outputs are mostly adequate but have some gaps")
            print("   Consider enhancing specific categories with low scores.")
        elif avg_score >= 40:
            print("⚠️ JSON outputs have significant gaps")
            print("   Content extraction needs improvement before markdown/XML generation.")
        else:
            print("❌ JSON outputs are missing critical content")
            print("   Major improvements needed to content extraction patterns.")
            print("\n   Key issues to address:")
            print("   1. Activities have no content (empty contents[] arrays)")
            print("   2. Only extracting ~5-10% of PDF text")
            print("   3. Standards and learning goals not captured")
            print("   4. Tables and lists may not be properly structured")

        print("\n" + "=" * 80)

        # Save batch report
        batch_report = {
            "total_checked": len(results),
            "avg_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "grade_distribution": {
                "excellent": excellent,
                "good": good,
                "fair": fair,
                "poor": poor
            },
            "results": results
        }

        report_file = Path(output_base) / "batch_completeness_summary.json"
        with open(report_file, 'w') as f:
            json.dump(batch_report, f, indent=2)

        print(f"📄 Batch report saved to: {report_file}")


def main():
    sample_size = 5  # Default to 5 PDFs
    if len(sys.argv) > 1:
        sample_size = int(sys.argv[1])

    batch_check("/Users/yotam/PDF-JSON/Output_Batch", sample_size)


if __name__ == "__main__":
    main()
