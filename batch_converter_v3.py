#!/usr/bin/env python3
"""
Batch Converter for V3 - Process all PDFs with enhanced activity extraction
"""

import sys
from pathlib import Path
from curriculum_converter_v3 import CurriculumConverterV3
import json
from datetime import datetime


def sanitize_filename(filename: str) -> str:
    """Create safe directory name from PDF filename"""
    # Remove extension
    name = Path(filename).stem

    # Remove brackets and special chars
    name = name.replace('[', '').replace(']', '')
    name = name.replace(' ', '_')
    name = name.replace('(', '').replace(')', '')
    name = name.replace(':', '_')

    return name


def process_all_pdfs_v3(input_dir: str, output_base_dir: str):
    """Process all PDFs in input directory with V3"""
    input_path = Path(input_dir)
    output_base = Path(output_base_dir)

    # Create output directory
    output_base.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdf_files = sorted(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {input_dir}")
        return

    print("=" * 80)
    print(f"BATCH PROCESSING V3: {len(pdf_files)} PDFs")
    print("=" * 80)
    print(f"Input directory: {input_path}")
    print(f"Output directory: {output_base}")
    print(f"Version: V3 (Enhanced Activity Extraction)")
    print("=" * 80)
    print()

    results = []
    successful = 0
    errors = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-" * 80)

        try:
            # Create output directory for this PDF
            safe_name = sanitize_filename(pdf_file.name)
            output_dir = output_base / f"{safe_name}_v3"

            # Convert
            converter = CurriculumConverterV3(str(pdf_file), str(output_dir))
            result = converter.convert()

            # Track result
            results.append({
                "pdf": pdf_file.name,
                "status": "success",
                "output_dir": str(output_dir.relative_to(output_base)),
                "summary": result
            })

            successful += 1
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "pdf": pdf_file.name,
                "status": "error",
                "error": str(e)
            })
            errors += 1
            print()

    # Print summary
    print("=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"✓ Successful: {successful}")
    print(f"❌ Errors: {errors}")
    print()

    if successful > 0:
        print("Results by file:")
        for result in results:
            if result["status"] == "success":
                summary = result["summary"]
                print(f"  ✓ {result['pdf']}")
                print(f"      → {summary['activities']} activities, "
                      f"{summary['learning_goals']} learning goals, "
                      f"{summary['standards']} standards")
                print(f"      → Output: {result['output_dir']}/")
            else:
                print(f"  ❌ {result['pdf']}")
                print(f"      → Error: {result['error']}")
        print()

    # Save batch report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_base / f"batch_report_v3_{timestamp}.json"

    batch_report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v3",
        "total": len(pdf_files),
        "successful": successful,
        "errors": errors,
        "results": results
    }

    with open(report_file, 'w') as f:
        json.dump(batch_report, f, indent=2)

    print(f"Detailed report saved to: {report_file.name}")


def main():
    input_dir = "/Users/yotam/PDF-JSON/Input"
    output_base_dir = "/Users/yotam/PDF-JSON/Output_Batch_V3"

    process_all_pdfs_v3(input_dir, output_base_dir)


if __name__ == "__main__":
    main()
