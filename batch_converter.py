#!/usr/bin/env python3
"""
Batch Curriculum Converter
Processes all PDFs in the Input folder automatically.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Import the converter classes
from curriculum_converter import CurriculumConverter as ConverterV1
from curriculum_converter_v2_deterministic import CurriculumConverterV2 as ConverterV2

def sanitize_filename(filename: str) -> str:
    """Create a safe directory name from filename"""
    # Remove extension
    name = Path(filename).stem
    # Replace spaces and special chars with underscores
    name = name.replace(' ', '_').replace('[', '').replace(']', '').replace(':', '_')
    return name

def process_all_pdfs(input_dir: str, output_base_dir: str, version: str = "v2"):
    """Process all PDFs in input directory"""

    input_path = Path(input_dir)
    output_base = Path(output_base_dir)

    # Find all PDFs
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {input_dir}")
        return

    print("="*80)
    print(f"BATCH PROCESSING: {len(pdf_files)} PDFs")
    print("="*80)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_base_dir}")
    print(f"Version: {version.upper()}")
    print("="*80)

    results = []

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-"*80)

        try:
            # Create unique output directory for this PDF
            safe_name = sanitize_filename(pdf_file.name)
            output_dir = output_base / f"{safe_name}_{version}"

            # Choose converter version
            if version.lower() == "v1":
                converter = ConverterV1(str(pdf_file), str(output_dir))
            else:
                converter = ConverterV2(str(pdf_file), str(output_dir))

            # Convert
            result = converter.convert()
            converter.save_outputs(result)

            # Record result
            results.append({
                "pdf": pdf_file.name,
                "status": "success",
                "output_dir": str(output_dir),
                "summary": result["summary"]
            })

            print(f"✓ Success! Output: {output_dir.relative_to(Path.cwd())}")

        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")
            results.append({
                "pdf": pdf_file.name,
                "status": "error",
                "error": str(e)
            })

    # Print summary
    print("\n" + "="*80)
    print("BATCH PROCESSING COMPLETE")
    print("="*80)

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"\nTotal PDFs: {len(pdf_files)}")
    print(f"✓ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")

    print("\nResults by file:")
    for result in results:
        status_icon = "✓" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {result['pdf']}")
        if result["status"] == "success":
            summary = result["summary"]
            print(f"      → {summary.get('activities', 0)} activities, "
                  f"{summary.get('lessons', 0)} lesson(s)")
            print(f"      → Output: {Path(result['output_dir']).name}/")
        else:
            print(f"      → Error: {result.get('error', 'Unknown error')}")

    # Save results report
    report_file = output_base / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "total": len(pdf_files),
            "successful": success_count,
            "errors": error_count,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed report saved to: {report_file.name}")
    print("="*80)

def main():
    input_dir = "/Users/yotam/PDF-JSON/Input"
    output_base_dir = "/Users/yotam/PDF-JSON/Output_Batch"

    # Check command line arguments
    version = "v2"  # Default to V2

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["v1", "v2"]:
            version = arg
        else:
            print("Usage: python batch_converter.py [v1|v2]")
            print("  v1 - Basic structure only")
            print("  v2 - Enhanced content extraction (default)")
            sys.exit(1)

    process_all_pdfs(input_dir, output_base_dir, version)

if __name__ == "__main__":
    main()
