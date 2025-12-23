# PDF to JSON Curriculum Converter

A deterministic, AI-free tool for converting curriculum PDF documents into hierarchical JSON format. Designed to extract educational content from PDF lessons and activities for digital curriculum platforms.

## Overview

This converter processes curriculum PDFs and generates structured JSON files that capture:
- Hierarchical course structure (Course → Unit → Section → Lesson → Activity)
- Learning standards and goals
- Activity content with materials, guidance, and procedures
- Timeframes and instructional metadata
- Relationship graphs for content navigation

**Key Features:**
- 🎯 **100% Deterministic** - Same input always produces same output (no AI/LLM variability)
- 🚀 **High Quality** - Achieves 72-92% content extraction accuracy
- 📦 **Batch Processing** - Process hundreds of PDFs automatically
- 🔍 **Quality Verification** - Built-in quality checker validates extraction completeness
- 🎨 **Markdown/XML Ready** - Extracted content is ready for reformatting
- 🤖 **Automatic PDF Type Detection** - Handles both full lessons (11-20 pages) and single activities (1-3 pages)

## Quick Start

### Installation

1. Clone this repository
2. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Basic Usage

The simplest way to use the converter is through the interactive menu:

```bash
./RUN_ME.sh
```

**Menu Options:**
1. V1 - Basic converter (structure only) - Single PDF
2. V2 - Enhanced converter - Single PDF
3. **V3 - BEST** (full activity content, 97% extraction) - Single PDF ⭐
4. Compare versions - Single PDF
5. Batch process with V1
6. Batch process with V2
7. **Batch process with V3** (RECOMMENDED) ⭐

### Processing a Single PDF

Process one PDF with V3 (recommended):

```bash
python curriculum_converter_v3.py
```

Output will be saved to `Output_V3/`

### Batch Processing Multiple PDFs

Process all PDFs in the `Input/` folder:

```bash
python batch_converter_v3.py
```

Output will be saved to `Output_Batch_V3/` with a timestamped batch report.

### Checking Quality

Verify the quality of converted JSON:

```bash
# Single PDF quality check
python content_completeness_checker.py "Input/[TK.1.A1] Lesson_ Identifying 2-D Shapes.pdf" Output_V3

# Batch quality check (random sample of 10)
python batch_completeness_check.py 10
```

Quality scores:
- **80-100%**: EXCELLENT - Ready for markdown/XML generation
- **60-79%**: GOOD - Mostly ready
- **40-59%**: FAIR - Significant gaps
- **<40%**: POOR - Major content missing

## How It Works

### PDF Type Detection

The converter automatically detects PDF type and applies appropriate extraction:

- **1-3 pages**: Single-activity PDF → Extracts all content as one activity
- **4+ pages**: Multi-activity lesson → Detects and extracts individual activity sections

### Extraction Process

1. **Metadata Extraction**: Title, standards, learning goals from front matter
2. **Activity Detection**: Identifies activity sections by headers (Opening, Centers, Closing, etc.)
3. **Content Extraction**: Captures materials, guidance, procedures, timeframes
4. **HTML Formatting**: Structures content with proper formatting
5. **JSON Generation**: Creates hierarchical entities with UUIDs
6. **Relationship Graph**: Generates edges.jsonl for content relationships

### Output Structure

Each PDF produces:

```
Output_V3/
├── lesson.json          # Main lesson entity
├── activity_1.json      # Activity entities
├── activity_2.json
├── ...
└── edges.jsonl          # Relationship graph
```

### JSON Schema

**Lesson Entity:**
```json
{
  "id": "uuid-v4",
  "type": "lesson",
  "title": "Identifying 2-D Shapes",
  "description": "Students identify and name basic 2-D shapes",
  "learning_goals": [...],
  "standards": [...],
  "contents": [
    {
      "type": "html",
      "title": "Overview",
      "content": "<p>This lesson introduces...</p>"
    }
  ]
}
```

**Activity Entity:**
```json
{
  "id": "uuid-v4",
  "type": "activity",
  "title": "Opening - See and Ask: Shapes",
  "activity_type": "opening",
  "timeframe": "10 min",
  "contents": [
    {
      "type": "html",
      "title": "Materials",
      "content": "<ul><li>Slide: Basic Shapes</li></ul>"
    },
    {
      "type": "html",
      "title": "Guidance",
      "content": "<ol><li>Display the image</li>...</ol>"
    }
  ]
}
```

## Version Comparison

### V3 (RECOMMENDED) ⭐

**Quality Score:** 72-92% depending on PDF type

**Features:**
- Automatic PDF type detection
- Full activity content extraction (97% capture rate)
- 90% of activities populated with content
- Handles both single-activity and multi-activity PDFs
- Learning standards and goals extraction
- Timeframe detection
- Materials and guidance extraction

**Best For:** All use cases

### V2 (DEPRECATED)

**Quality Score:** 37%

**Issues:**
- Activities created but with empty content arrays
- Only 5.8% content extraction
- Not suitable for markdown/XML generation

### V1 (BASIC)

**Quality Score:** ~30%

**Features:**
- Basic structure extraction only
- Minimal content capture

## Performance

### V3 Results on Real Curriculum PDFs

**Full Lesson PDFs (11-20 pages):**
- Content extraction: 97-102%
- Activities with content: 88-90%
- Quality score: 72-87%
- ✅ Ready for markdown/XML generation

**Short Activity PDFs (1-3 pages):**
- Content extraction: 95-98%
- Activities with content: 100%
- Quality score: 85-92%
- ✅ Ready for markdown/XML generation

**Batch Processing:**
- Successfully processed 373 PDFs
- 100% success rate
- Average processing time: 2 seconds per PDF
- Total batch time: ~12 minutes

## File Structure

```
PDF-JSON/
├── curriculum_converter_v3.py           # Main V3 converter ⭐
├── batch_converter_v3.py                # Batch processor ⭐
├── content_completeness_checker.py      # Quality checker ⭐
├── batch_completeness_check.py          # Batch quality checker
├── RUN_ME.sh                            # Interactive menu ⭐
├── requirements.txt                     # Python dependencies
├── README.md                            # This file
├── V3_IMPROVEMENTS.md                   # Technical documentation
├── V3_TEST_RESULTS.md                   # Test results across PDF types
├── CONTENT_COMPLETENESS_REPORT.md       # Detailed quality assessment
└── [Other converter versions...]
```

## Technical Details

### Dependencies

- **pdfplumber**: Primary PDF text extraction
- **pymupdf (fitz)**: Supplementary extraction
- **Python 3.8+**: Required

### Deterministic Approach

This converter uses:
- ✅ Regex pattern matching
- ✅ Rule-based content extraction
- ✅ Deterministic boundary detection
- ❌ NO AI/LLM calls
- ❌ NO machine learning models
- ❌ NO probabilistic extraction

**Benefit:** Same PDF always produces identical output, enabling reliable testing and version control.

### Content Extraction Algorithm

1. **Page segmentation** - Identify overview pages (1-4) vs activity pages (5+)
2. **Header detection** - Find activity section headers using pattern matching
3. **Boundary calculation** - Determine where each activity's content ends
4. **Component extraction** - Extract timeframes, materials, guidance, procedures
5. **Structure preservation** - Maintain bullets, numbering, paragraphs
6. **HTML formatting** - Convert to structured HTML content blocks

## Quality Verification

The quality checker validates extraction across 7 categories:

1. **Titles** (10 points) - All section/activity titles captured
2. **Content Volume** (20 points) - % of PDF text extracted
3. **Activities** (25 points) - Count and content completeness
4. **Structural Elements** (15 points) - Headings, lists, tables
5. **Learning Standards** (10 points) - Standards alignment captured
6. **Learning Goals** (10 points) - Objectives extracted
7. **Metadata** (10 points) - Timeframes, instructions, preparation

**Total:** 100 points

## Use Cases

- **Digital Curriculum Platforms**: Convert legacy PDF curriculum to structured format
- **Content Migration**: Move curriculum content to modern learning management systems
- **Markdown/XML Generation**: Create alternative formats from extracted JSON
- **Content Analysis**: Analyze curriculum structure and components at scale
- **Quality Assurance**: Verify curriculum completeness and consistency

## Known Limitations

1. **Complex Tables**: Some complex table structures may not be fully captured
2. **Images**: Image content is not extracted (text-only extraction)
3. **PDF Format Dependency**: Works best with text-based PDFs (not scanned images)
4. **Custom Layouts**: PDFs with non-standard layouts may require pattern tuning

## Contributing

This is a deterministic, rule-based system. To improve extraction:

1. Analyze PDFs that score below 70%
2. Identify missing content patterns
3. Add regex patterns to `curriculum_converter_v3.py`
4. Test on diverse PDF samples
5. Run quality checker to verify improvements

## Documentation

- **[V3_IMPROVEMENTS.md](V3_IMPROVEMENTS.md)** - Technical details of V3 enhancements
- **[V3_TEST_RESULTS.md](V3_TEST_RESULTS.md)** - Test results across different PDF types
- **[CONTENT_COMPLETENESS_REPORT.md](CONTENT_COMPLETENESS_REPORT.md)** - Detailed quality assessment

## License

[Add your license here]

## Support

For issues or questions about the converter, please refer to the documentation files or check the code comments in `curriculum_converter_v3.py`.

---

**Version:** V3
**Last Updated:** December 2025
**Maintained by:** Kiddom
