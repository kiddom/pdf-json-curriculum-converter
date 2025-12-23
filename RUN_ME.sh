#!/bin/bash
# Simple script to run the converters

echo "=========================================="
echo "PDF to JSON Curriculum Converter"
echo "=========================================="
echo ""
echo "Which version do you want to run?"
echo ""
echo "1) V1 - Basic (fast, structure only) - Single PDF"
echo "2) V2 - Enhanced (more content extraction) - Single PDF"
echo "3) V3 - BEST (full activity content, 97% extraction) - Single PDF"
echo "4) Both versions + comparison - Single PDF"
echo "5) Batch process ALL PDFs in Input/ folder (V1)"
echo "6) Batch process ALL PDFs in Input/ folder (V2)"
echo "7) Batch process ALL PDFs in Input/ folder (V3) - RECOMMENDED"
echo ""
read -p "Enter choice (1-7): " choice

cd /Users/yotam/PDF-JSON

# Activate virtual environment
source venv/bin/activate

echo ""
echo "=========================================="

case $choice in
    1)
        echo "Running V1 (Basic)..."
        echo "=========================================="
        python curriculum_converter.py
        echo ""
        echo "✓ Done! Output saved to: Output/"
        echo ""
        echo "View results:"
        echo "  ls -R Output/"
        ;;
    2)
        echo "Running V2 (Enhanced Deterministic)..."
        echo "=========================================="
        python curriculum_converter_v2_deterministic.py
        echo ""
        echo "✓ Done! Output saved to: Output_V2_Deterministic/"
        echo ""
        echo "View results:"
        echo "  ls -R Output_V2_Deterministic/"
        ;;
    3)
        echo "Running V3 (BEST - Full Activity Content)..."
        echo "=========================================="
        python curriculum_converter_v3.py
        echo ""
        echo "✓ Done! Output saved to: Output_V3/"
        echo ""
        echo "View results:"
        echo "  ls -R Output_V3/"
        echo ""
        echo "Check quality:"
        echo "  python content_completeness_checker.py 'Input/[TK.1.A1] Lesson_ Identifying 2-D Shapes.pdf' Output_V3"
        ;;
    4)
        echo "Running V1..."
        echo "=========================================="
        python curriculum_converter.py
        echo ""
        echo "Running V2..."
        echo "=========================================="
        python curriculum_converter_v2_deterministic.py
        echo ""
        echo "Comparing results..."
        echo "=========================================="
        python compare_versions.py
        echo ""
        echo "✓ Done!"
        echo ""
        echo "Outputs saved to:"
        echo "  - Output/ (V1)"
        echo "  - Output_V2_Deterministic/ (V2)"
        ;;
    5)
        echo "Batch Processing ALL PDFs with V1..."
        echo "=========================================="
        python batch_converter.py v1
        echo ""
        echo "✓ Done! All outputs saved to: Output_Batch/"
        echo ""
        echo "View results:"
        echo "  ls -R Output_Batch/"
        ;;
    6)
        echo "Batch Processing ALL PDFs with V2..."
        echo "=========================================="
        python batch_converter.py v2
        echo ""
        echo "✓ Done! All outputs saved to: Output_Batch/"
        echo ""
        echo "View results:"
        echo "  ls -R Output_Batch/"
        ;;
    7)
        echo "Batch Processing ALL PDFs with V3 (RECOMMENDED)..."
        echo "=========================================="
        python batch_converter_v3.py
        echo ""
        echo "✓ Done! All outputs saved to: Output_Batch_V3/"
        echo ""
        echo "View results:"
        echo "  ls -R Output_Batch_V3/"
        echo ""
        echo "Check quality:"
        echo "  python batch_completeness_check.py 10"
        ;;
    *)
        echo "Invalid choice. Please run again and choose 1-7."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Need help? Read:"
echo "  - QUICK_START.md (beginner guide)"
echo "  - VERSION_COMPARISON.md (V1 vs V2)"
echo "  - README.md (full documentation)"
echo "=========================================="
