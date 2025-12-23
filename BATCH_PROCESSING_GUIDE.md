# Batch Processing Multiple PDFs

## 🎯 Quick Answer

**Yes! Just put all PDFs in the Input folder and run batch mode.**

---

## 📁 Step-by-Step

### 1. Add Your PDFs
```bash
# Copy all your curriculum PDFs to the Input folder
cp /path/to/your/pdfs/*.pdf /Users/yotam/PDF-JSON/Input/

# Or drag and drop them into the Input folder
```

### 2. Run Batch Processing
```bash
cd /Users/yotam/PDF-JSON
./RUN_ME.sh
```

Choose option **5** (Batch V2) or **4** (Batch V1)

### 3. Done!
Each PDF gets its own output folder:
```
Output_Batch/
├── Lesson_1_Shapes_v2/
│   ├── activity/
│   ├── lesson/
│   └── edges.jsonl
├── Lesson_2_Numbers_v2/
│   ├── activity/
│   ├── lesson/
│   └── edges.jsonl
└── Lesson_3_Colors_v2/
    ├── activity/
    ├── lesson/
    └── edges.jsonl
```

---

## 💻 Alternative: Direct Command

```bash
# Batch process with V2 (recommended)
source venv/bin/activate
python batch_converter.py v2

# Or with V1 (faster, less content)
python batch_converter.py v1
```

---

## 📊 What Happens

The batch script will:

1. ✅ Find all `.pdf` files in `Input/`
2. ✅ Process each one automatically
3. ✅ Create a separate output folder for each
4. ✅ Generate a summary report
5. ✅ Show success/error status for each file

### Example Output:
```
================================================================================
BATCH PROCESSING: 3 PDFs
================================================================================
Input directory: /Users/yotam/PDF-JSON/Input
Output directory: /Users/yotam/PDF-JSON/Output_Batch
Version: V2
================================================================================

[1/3] Processing: Lesson_1_Shapes.pdf
--------------------------------------------------------------------------------
Converting Lesson_1_Shapes.pdf (V2 Deterministic)...
  Extracted 14 pages
  Created 12 activities
✓ Success! Output: Output_Batch/Lesson_1_Shapes_v2/

[2/3] Processing: Lesson_2_Numbers.pdf
--------------------------------------------------------------------------------
Converting Lesson_2_Numbers.pdf (V2 Deterministic)...
  Extracted 16 pages
  Created 10 activities
✓ Success! Output: Output_Batch/Lesson_2_Numbers_v2/

[3/3] Processing: Lesson_3_Colors.pdf
--------------------------------------------------------------------------------
Converting Lesson_3_Colors.pdf (V2 Deterministic)...
  Extracted 12 pages
  Created 8 activities
✓ Success! Output: Output_Batch/Lesson_3_Colors_v2/

================================================================================
BATCH PROCESSING COMPLETE
================================================================================

Total PDFs: 3
✓ Successful: 3
❌ Errors: 0

Results by file:
  ✓ Lesson_1_Shapes.pdf
      → 12 activities, 1 lesson(s)
      → Output: Lesson_1_Shapes_v2/
  ✓ Lesson_2_Numbers.pdf
      → 10 activities, 1 lesson(s)
      → Output: Lesson_2_Numbers_v2/
  ✓ Lesson_3_Colors.pdf
      → 8 activities, 1 lesson(s)
      → Output: Lesson_3_Colors_v2/

Detailed report saved to: batch_report_20231219_143022.json
```

---

## 🔍 Output Structure

Each PDF gets its own folder:

```
Output_Batch/
├── TK_1_A1_Lesson_Identifying_2-D_Shapes_v2/
│   ├── course/
│   │   └── {uuid}.json
│   ├── unit/
│   │   └── {uuid}.json
│   ├── section/
│   │   └── {uuid}.json
│   ├── lesson/
│   │   └── {uuid}.json
│   ├── activity/
│   │   ├── {uuid}.json
│   │   └── ...
│   └── edges.jsonl
│
├── TK_1_A2_Lesson_Counting_Objects_v2/
│   ├── course/
│   ├── unit/
│   └── ...
│
└── batch_report_20231219_143022.json  (summary)
```

---

## 📝 Batch Report

A JSON report is automatically created:

```json
{
  "timestamp": "2023-12-19T14:30:22",
  "version": "v2",
  "total": 3,
  "successful": 3,
  "errors": 0,
  "results": [
    {
      "pdf": "Lesson_1_Shapes.pdf",
      "status": "success",
      "output_dir": "Output_Batch/Lesson_1_Shapes_v2",
      "summary": {
        "course": 1,
        "units": 1,
        "lessons": 1,
        "activities": 12
      }
    }
  ]
}
```

---

## ⚡ Performance

- **V1**: ~2 seconds per PDF
- **V2**: ~2 seconds per PDF
- **10 PDFs**: ~20-30 seconds total
- **100 PDFs**: ~3-5 minutes total

Processes run sequentially (one at a time) to avoid memory issues.

---

## 🛠️ Customization

### Change Input/Output Directories

Edit `batch_converter.py`:

```python
def main():
    input_dir = "/Users/yotam/PDF-JSON/Input"        # Your PDFs here
    output_base_dir = "/Users/yotam/PDF-JSON/Output_Batch"  # Output here

    # ... rest of code
```

### Filter Specific PDFs

```bash
# Only process PDFs matching a pattern
# Edit batch_converter.py, change this line:
pdf_files = list(input_path.glob("*.pdf"))

# To something like:
pdf_files = list(input_path.glob("Lesson_*.pdf"))  # Only Lesson_*.pdf
pdf_files = list(input_path.glob("TK*.pdf"))       # Only TK*.pdf
```

---

## ❓ FAQ

### Q: Do I need to edit any code?
**A:** No! Just put PDFs in `Input/` and run `./RUN_ME.sh` → choose option 5.

### Q: What if one PDF fails?
**A:** The script continues processing the rest. Check the batch report for details.

### Q: Can I process 100+ PDFs?
**A:** Yes! The script handles any number. Just takes longer.

### Q: Will it overwrite previous results?
**A:** No! Each run creates uniquely named output folders (with timestamps if needed).

### Q: Which version should I use for batch?
**A:** Use **V2** (option 5) for more content. Use **V1** (option 4) if you only need structure.

---

## 🚀 Quick Start Example

```bash
# 1. Add your PDFs
cp ~/Downloads/curriculum_pdfs/*.pdf Input/

# 2. Run batch processing
./RUN_ME.sh

# 3. Choose option 5 (Batch V2)

# 4. Wait for completion

# 5. Check results
ls -R Output_Batch/
```

That's it! 🎉

---

## 📊 View All Results at Once

```bash
# Count total activities generated across all PDFs
find Output_Batch -name "*.json" -path "*/activity/*" | wc -l

# List all lesson files
find Output_Batch -name "*.json" -path "*/lesson/*"

# Check all batch reports
cat Output_Batch/batch_report_*.json | jq .
```

---

## ✅ Summary

**YES - Just put all PDFs in Input/ and choose batch mode (option 4 or 5)!**

Each PDF is processed independently and gets its own output folder.
No code changes needed.
