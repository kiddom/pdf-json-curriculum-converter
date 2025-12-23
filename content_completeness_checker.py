#!/usr/bin/env python3
"""
Content Completeness Checker - Validates if JSON has enough information
to recreate PDF content in markdown/XML with different styling.

Checks for:
- Titles and headings
- Paragraphs and text content
- Activities by type (Explore, Discover, Build, etc.)
- Lists (bulleted, numbered)
- Tables
- Links and references
- Emphasis (bold, italic)
- Standards and metadata
- Learning goals
- Timeframes
"""

import json
import pdfplumber
from pathlib import Path
from typing import Dict, List, Tuple, Set
import re
from collections import defaultdict


class ContentType:
    """Content type identifiers"""
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    LINK = "link"
    BOLD = "bold_text"
    ITALIC = "italic_text"
    STANDARD = "standard"
    LEARNING_GOAL = "learning_goal"
    ACTIVITY = "activity"
    TIMEFRAME = "timeframe"
    INSTRUCTION = "instruction"
    SECTION = "section"


class ContentCompletenessChecker:
    """Check if JSON output has complete content for markdown/XML recreation"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)

        # Extracted from PDF
        self.pdf_content = {
            "titles": [],
            "headings": [],
            "paragraphs": [],
            "lists": [],
            "tables": [],
            "standards": [],
            "learning_goals": [],
            "activities": [],
            "timeframes": [],
            "instructions": [],
            "total_text_length": 0,
            "page_count": 0
        }

        # Extracted from JSON
        self.json_content = {
            "titles": [],
            "content_blocks": [],
            "activities": [],
            "standards": [],
            "learning_goals": [],
            "total_content_length": 0,
            "has_html": False,
            "content_types": set()
        }

        # Completeness scores
        self.scores = {}
        self.missing_content = []
        self.found_content = []

    def analyze_pdf(self):
        """Extract all content types from PDF"""
        print(f"\n📄 Analyzing PDF: {self.pdf_path.name}")
        print("-" * 80)

        if not self.pdf_path.exists():
            print(f"❌ PDF not found: {self.pdf_path}")
            return False

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.pdf_content["page_count"] = len(pdf.pages)

                all_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    all_text += text + "\n"

                self.pdf_content["total_text_length"] = len(all_text)

                # Extract titles (first large text or specific patterns)
                self._extract_pdf_titles(all_text)

                # Extract headings (DAY 1, DAY 2, section headers)
                self._extract_pdf_headings(all_text)

                # Extract paragraphs (blocks of text)
                self._extract_pdf_paragraphs(all_text)

                # Extract lists (bulleted/numbered)
                self._extract_pdf_lists(all_text)

                # Extract tables
                self._extract_pdf_tables(pdf)

                # Extract standards (GST.x.x.EF)
                self._extract_pdf_standards(all_text)

                # Extract learning goals
                self._extract_pdf_learning_goals(all_text)

                # Extract activities
                self._extract_pdf_activities(all_text)

                # Extract timeframes
                self._extract_pdf_timeframes(all_text)

                # Extract instructions
                self._extract_pdf_instructions(all_text)

                print(f"  Pages: {self.pdf_content['page_count']}")
                print(f"  Total text: {self.pdf_content['total_text_length']:,} characters")
                print(f"  Titles: {len(self.pdf_content['titles'])}")
                print(f"  Headings: {len(self.pdf_content['headings'])}")
                print(f"  Paragraphs: {len(self.pdf_content['paragraphs'])}")
                print(f"  Lists: {len(self.pdf_content['lists'])}")
                print(f"  Tables: {len(self.pdf_content['tables'])}")
                print(f"  Standards: {len(self.pdf_content['standards'])}")
                print(f"  Learning goals: {len(self.pdf_content['learning_goals'])}")
                print(f"  Activities: {len(self.pdf_content['activities'])}")
                print(f"  Timeframes: {len(self.pdf_content['timeframes'])}")
                print(f"  Instructions: {len(self.pdf_content['instructions'])}")

                return True

        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return False

    def _extract_pdf_titles(self, text: str):
        """Extract titles from PDF"""
        lines = text.split('\n')

        # First non-empty line is often the title
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                self.pdf_content["titles"].append(line)
                break

        # Look for lesson titles with codes
        title_patterns = [
            r'\[?[A-Z0-9\.]+\]?\s+Lesson[:\s]+(.+)',
            r'Lesson\s+\d+[:\s]+(.+)',
            r'^([A-Z][^a-z]{10,})',  # All caps titles
        ]

        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            self.pdf_content["titles"].extend(matches[:3])

    def _extract_pdf_headings(self, text: str):
        """Extract headings (DAY 1, DAY 2, section headers)"""
        heading_patterns = [
            r'^(DAY\s+\d+[:\s]+\w+)',  # DAY 1: Explore
            r'^([A-Z\s]{3,30}:)',  # LEARNING GOALS:
            r'^(\d+\.\d+:\s+[A-Z].+)',  # 1.1: Explore - Number Play
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):',  # Opening:, Closing:
        ]

        for pattern in heading_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            self.pdf_content["headings"].extend(matches)

    def _extract_pdf_paragraphs(self, text: str):
        """Extract paragraph blocks"""
        lines = text.split('\n')
        current_para = []

        for line in lines:
            line = line.strip()

            # Skip very short lines (likely headers/footers)
            if len(line) < 20:
                if current_para:
                    para_text = ' '.join(current_para)
                    if len(para_text) > 50:
                        self.pdf_content["paragraphs"].append(para_text)
                    current_para = []
                continue

            # Add to current paragraph
            current_para.append(line)

        # Add last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            if len(para_text) > 50:
                self.pdf_content["paragraphs"].append(para_text)

    def _extract_pdf_lists(self, text: str):
        """Extract bulleted and numbered lists"""
        list_patterns = [
            r'^[•●○▪▫■□]\s+(.+)',  # Bullet points
            r'^\d+[\.)]\s+(.+)',  # Numbered lists
            r'^[a-z][\.)]\s+(.+)',  # Lettered lists
        ]

        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            self.pdf_content["lists"].extend(matches)

    def _extract_pdf_tables(self, pdf):
        """Extract tables from PDF"""
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                self.pdf_content["tables"].extend(tables)

    def _extract_pdf_standards(self, text: str):
        """Extract learning standards"""
        patterns = [
            r'(GST\.[\d.]+\.EF)\s+([^:]+):\s*([^\n]+)',
            r'(CCSS[.\w]+)',
            r'(NGSS[.\w]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            self.pdf_content["standards"].extend(matches)

    def _extract_pdf_learning_goals(self, text: str):
        """Extract learning goals"""
        # Look for learning goals section
        lg_section = re.search(r'LEARNING GOALS?\s*:?\s*(.*?)(?=\n[A-Z\s]{3,}:|$)',
                               text, re.DOTALL | re.IGNORECASE)
        if lg_section:
            goals_text = lg_section.group(1)
            # Split by bullet points or numbers
            goals = re.split(r'[•●]\s*|\d+\.\s*', goals_text)
            self.pdf_content["learning_goals"].extend([g.strip() for g in goals if len(g.strip()) > 20])

    def _extract_pdf_activities(self, text: str):
        """Extract activities"""
        activity_patterns = [
            r'(\d+\.\d+:\s+\w+\s+-\s+[^\n]+)',  # 1.1: Explore - Number Play
            r'((?:Explore|Discover|Build|Practice)\s*-\s*[^\n]+)',
            r'(Opening|Centers|Closing)\s*:?\s*([^\n]+)',
        ]

        for pattern in activity_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                self.pdf_content["activities"].extend([m if isinstance(m, str) else ' '.join(m) for m in matches])

    def _extract_pdf_timeframes(self, text: str):
        """Extract timeframes"""
        timeframe_patterns = [
            r'(\d+(?:–|-)\d+\s*min)',
            r'(\d+\s*min)',
            r'(\d+\s*minutes?)',
        ]

        for pattern in timeframe_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            self.pdf_content["timeframes"].extend(matches)

    def _extract_pdf_instructions(self, text: str):
        """Extract instructional content"""
        instruction_patterns = [
            r'(?:Teacher|Instructor|Student)s?\s+(?:should|will|can)\s+([^\n.]{20,})',
            r'(?:Guide|Help|Ask)\s+(?:students?|children)\s+(?:to|through)\s+([^\n.]{20,})',
        ]

        for pattern in instruction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            self.pdf_content["instructions"].extend(matches[:10])  # Limit to 10

    def analyze_json(self):
        """Extract all content from JSON output"""
        print(f"\n📊 Analyzing JSON Output: {self.output_dir.name}")
        print("-" * 80)

        if not self.output_dir.exists():
            print(f"❌ Output directory not found: {self.output_dir}")
            return False

        try:
            # Load all entity types
            for entity_type in ["course", "unit", "section", "lesson", "activity", "assessment"]:
                folder = self.output_dir / entity_type
                if not folder.exists():
                    continue

                for json_file in folder.glob("*.json"):
                    with open(json_file, 'r') as f:
                        entity = json.load(f)

                    # Extract title
                    if "title" in entity:
                        self.json_content["titles"].append(entity["title"])

                    # Extract content blocks
                    contents = entity.get("contents", [])
                    for content_block in contents:
                        self.json_content["content_blocks"].append(content_block)

                        # Check content length
                        content_html = content_block.get("content", "")
                        self.json_content["total_content_length"] += len(content_html)

                        if content_html:
                            self.json_content["has_html"] = True

                        # Identify content types
                        content_title = content_block.get("title", "")
                        if "standard" in content_title.lower():
                            self.json_content["content_types"].add("standards")
                        if "goal" in content_title.lower():
                            self.json_content["content_types"].add("learning_goals")
                        if "timeframe" in content_title.lower():
                            self.json_content["content_types"].add("timeframes")

                    # Track activities
                    if entity_type == "activity":
                        self.json_content["activities"].append({
                            "title": entity.get("title", ""),
                            "has_content": len(contents) > 0,
                            "content_blocks": len(contents)
                        })

                    # Extract metadata
                    if "standards" in entity:
                        self.json_content["standards"].extend(entity["standards"])
                    if "learning_goals" in entity:
                        self.json_content["learning_goals"].extend(entity["learning_goals"])

            print(f"  Titles found: {len(self.json_content['titles'])}")
            print(f"  Content blocks: {len(self.json_content['content_blocks'])}")
            print(f"  Activities: {len(self.json_content['activities'])}")
            print(f"  Total content: {self.json_content['total_content_length']:,} characters")
            print(f"  Has HTML: {self.json_content['has_html']}")
            print(f"  Content types: {', '.join(self.json_content['content_types']) if self.json_content['content_types'] else 'None'}")

            # Activity details
            activities_with_content = sum(1 for a in self.json_content["activities"] if a["has_content"])
            print(f"  Activities with content: {activities_with_content}/{len(self.json_content['activities'])}")

            return True

        except Exception as e:
            print(f"❌ Error reading JSON: {e}")
            import traceback
            traceback.print_exc()
            return False

    def calculate_completeness_scores(self):
        """Calculate completeness scores for content recreation"""
        print(f"\n📈 Calculating Completeness Scores")
        print("=" * 80)

        max_score = 100
        score = 0

        # 1. Title completeness (10 points)
        print("\n1. TITLES")
        print("-" * 80)
        if len(self.json_content["titles"]) >= len(self.pdf_content["titles"]):
            title_score = 10
            self.found_content.append(f"All titles captured ({len(self.json_content['titles'])} found)")
        elif len(self.json_content["titles"]) > 0:
            title_score = 5
            self.missing_content.append(f"Some titles missing (found {len(self.json_content['titles'])}/{len(self.pdf_content['titles'])})")
        else:
            title_score = 0
            self.missing_content.append("No titles found in JSON")

        score += title_score
        self.scores["titles"] = title_score
        print(f"  PDF titles: {len(self.pdf_content['titles'])}")
        print(f"  JSON titles: {len(self.json_content['titles'])}")
        print(f"  Score: {title_score}/10")

        # 2. Content volume (20 points)
        print("\n2. CONTENT VOLUME")
        print("-" * 80)
        pdf_text_length = self.pdf_content["total_text_length"]
        json_text_length = self.json_content["total_content_length"]

        if pdf_text_length > 0:
            content_ratio = json_text_length / pdf_text_length
        else:
            content_ratio = 0

        if content_ratio >= 0.5:
            content_score = 20
            self.found_content.append(f"Good content extraction ({content_ratio:.1%} of PDF text)")
        elif content_ratio >= 0.25:
            content_score = 10
            self.missing_content.append(f"Moderate content extraction ({content_ratio:.1%} of PDF text)")
        else:
            content_score = 5
            self.missing_content.append(f"Low content extraction ({content_ratio:.1%} of PDF text)")

        score += content_score
        self.scores["content_volume"] = content_score
        print(f"  PDF text: {pdf_text_length:,} characters")
        print(f"  JSON content: {json_text_length:,} characters")
        print(f"  Extraction ratio: {content_ratio:.1%}")
        print(f"  Score: {content_score}/20")

        # 3. Activity completeness (25 points)
        print("\n3. ACTIVITIES")
        print("-" * 80)
        pdf_activities = len(self.pdf_content["activities"])
        json_activities = len(self.json_content["activities"])

        if json_activities >= pdf_activities and json_activities > 0:
            activity_score = 15
        elif json_activities >= pdf_activities * 0.5:
            activity_score = 10
        elif json_activities > 0:
            activity_score = 5
        else:
            activity_score = 0

        # Check if activities have content
        activities_with_content = sum(1 for a in self.json_content["activities"] if a["has_content"])

        if json_activities > 0:
            content_ratio = activities_with_content / json_activities
            if content_ratio >= 0.75:
                activity_content_score = 10
                self.found_content.append(f"Most activities have content ({activities_with_content}/{json_activities})")
            elif content_ratio >= 0.25:
                activity_content_score = 5
                self.missing_content.append(f"Some activities lack content ({activities_with_content}/{json_activities})")
            else:
                activity_content_score = 0
                self.missing_content.append(f"Most activities lack content ({activities_with_content}/{json_activities})")
        else:
            activity_content_score = 0
            self.missing_content.append("No activities found")

        score += activity_score + activity_content_score
        self.scores["activities"] = activity_score + activity_content_score
        print(f"  PDF activities: {pdf_activities}")
        print(f"  JSON activities: {json_activities}")
        print(f"  Activities with content: {activities_with_content}/{json_activities}")
        print(f"  Score: {activity_score + activity_content_score}/25")

        # 4. Structural elements (15 points)
        print("\n4. STRUCTURAL ELEMENTS")
        print("-" * 80)
        structure_score = 0

        # Headings
        if len(self.pdf_content["headings"]) > 0:
            if len(self.json_content["content_blocks"]) >= len(self.pdf_content["headings"]) * 0.5:
                structure_score += 5
                self.found_content.append("Headings/sections captured in content blocks")
            else:
                self.missing_content.append("Many headings/sections missing")

        # Lists
        if len(self.pdf_content["lists"]) > 5:
            if self.json_content["has_html"]:
                structure_score += 5
                self.found_content.append("Lists likely in HTML content")
            else:
                self.missing_content.append("Lists may not be captured")

        # Tables
        if len(self.pdf_content["tables"]) > 0:
            # Hard to check without parsing HTML
            structure_score += 2
            self.missing_content.append(f"Cannot verify if {len(self.pdf_content['tables'])} tables captured")
        else:
            structure_score += 3

        score += structure_score
        self.scores["structure"] = structure_score
        print(f"  PDF headings: {len(self.pdf_content['headings'])}")
        print(f"  PDF lists: {len(self.pdf_content['lists'])}")
        print(f"  PDF tables: {len(self.pdf_content['tables'])}")
        print(f"  JSON content blocks: {len(self.json_content['content_blocks'])}")
        print(f"  Score: {structure_score}/15")

        # 5. Learning standards (10 points)
        print("\n5. LEARNING STANDARDS")
        print("-" * 80)
        pdf_standards = len(self.pdf_content["standards"])
        json_standards = len(self.json_content["standards"])

        if pdf_standards > 0:
            if json_standards >= pdf_standards:
                standards_score = 10
                self.found_content.append(f"All standards captured ({json_standards} found)")
            elif json_standards > 0:
                standards_score = 5
                self.missing_content.append(f"Some standards missing ({json_standards}/{pdf_standards})")
            else:
                standards_score = 0
                self.missing_content.append(f"No standards captured (PDF has {pdf_standards})")
        else:
            standards_score = 10  # No standards to capture

        score += standards_score
        self.scores["standards"] = standards_score
        print(f"  PDF standards: {pdf_standards}")
        print(f"  JSON standards: {json_standards}")
        print(f"  Score: {standards_score}/10")

        # 6. Learning goals (10 points)
        print("\n6. LEARNING GOALS")
        print("-" * 80)
        pdf_goals = len(self.pdf_content["learning_goals"])
        json_goals = len(self.json_content["learning_goals"])

        if pdf_goals > 0:
            if json_goals >= pdf_goals:
                goals_score = 10
                self.found_content.append(f"Learning goals captured ({json_goals} found)")
            elif json_goals > 0:
                goals_score = 5
                self.missing_content.append(f"Some learning goals missing ({json_goals}/{pdf_goals})")
            else:
                goals_score = 0
                self.missing_content.append(f"No learning goals captured (PDF has {pdf_goals})")
        else:
            goals_score = 10  # No goals to capture

        score += goals_score
        self.scores["learning_goals"] = goals_score
        print(f"  PDF learning goals: {pdf_goals}")
        print(f"  JSON learning goals: {json_goals}")
        print(f"  Score: {goals_score}/10")

        # 7. Metadata (timeframes, instructions) (10 points)
        print("\n7. METADATA")
        print("-" * 80)
        metadata_score = 0

        # Timeframes
        if len(self.pdf_content["timeframes"]) > 0:
            if "timeframes" in self.json_content["content_types"]:
                metadata_score += 5
                self.found_content.append("Timeframes captured")
            else:
                self.missing_content.append(f"Timeframes missing ({len(self.pdf_content['timeframes'])} in PDF)")
        else:
            metadata_score += 5

        # Instructions
        if len(self.pdf_content["instructions"]) > 0:
            if self.json_content["total_content_length"] > 500:
                metadata_score += 5
                self.found_content.append("Instructional content likely captured")
            else:
                self.missing_content.append("Instructional content may be missing")
        else:
            metadata_score += 5

        score += metadata_score
        self.scores["metadata"] = metadata_score
        print(f"  PDF timeframes: {len(self.pdf_content['timeframes'])}")
        print(f"  PDF instructions: {len(self.pdf_content['instructions'])}")
        print(f"  Score: {metadata_score}/10")

        # Final score
        self.scores["total"] = score
        self.scores["max"] = max_score
        self.scores["percentage"] = (score / max_score * 100) if max_score > 0 else 0

        return score, max_score

    def print_summary(self):
        """Print completeness summary"""
        print("\n" + "=" * 80)
        print("CONTENT COMPLETENESS REPORT")
        print("=" * 80)

        score = self.scores["total"]
        max_score = self.scores["max"]
        percentage = self.scores["percentage"]

        print(f"\nOverall Score: {score}/{max_score} ({percentage:.1f}%)")

        if percentage >= 80:
            grade = "✅ EXCELLENT - Ready for markdown/XML generation"
            verdict = "JSON contains sufficient information to recreate PDF content."
        elif percentage >= 60:
            grade = "✓ GOOD - Mostly ready with minor gaps"
            verdict = "JSON has most content but may need minor enhancements."
        elif percentage >= 40:
            grade = "⚠️ FAIR - Significant gaps in content"
            verdict = "JSON missing important content for full recreation."
        else:
            grade = "❌ POOR - Major content missing"
            verdict = "JSON lacks critical information for content recreation."

        print(f"Grade: {grade}")
        print(f"\nVerdict: {verdict}")

        # Category breakdown
        print(f"\nCategory Breakdown:")
        print(f"  Titles: {self.scores.get('titles', 0)}/10")
        print(f"  Content Volume: {self.scores.get('content_volume', 0)}/20")
        print(f"  Activities: {self.scores.get('activities', 0)}/25")
        print(f"  Structure: {self.scores.get('structure', 0)}/15")
        print(f"  Standards: {self.scores.get('standards', 0)}/10")
        print(f"  Learning Goals: {self.scores.get('learning_goals', 0)}/10")
        print(f"  Metadata: {self.scores.get('metadata', 0)}/10")

        # What's captured well
        if self.found_content:
            print(f"\n✅ Content Captured ({len(self.found_content)}):")
            for item in self.found_content[:10]:
                print(f"  • {item}")

        # What's missing
        if self.missing_content:
            print(f"\n⚠️ Missing/Incomplete Content ({len(self.missing_content)}):")
            for item in self.missing_content[:10]:
                print(f"  • {item}")

        # Recommendations
        print(f"\n💡 Recommendations for Markdown/XML Generation:")

        if percentage >= 80:
            print("  • JSON output is comprehensive enough for content recreation")
            print("  • Can proceed with markdown/XML generation")
            print("  • May need to handle HTML-to-markdown conversion")
        elif percentage >= 60:
            print("  • Consider enhancing activity content extraction")
            print("  • Verify all structural elements are captured")
            print("  • May need post-processing to fill gaps")
        else:
            print("  • Need to improve content extraction significantly")
            print("  • Activities need content (currently empty)")
            print("  • Consider enhancing PDF parsing patterns")
            print("  • May need to use more sophisticated extraction methods")

        print("\n" + "=" * 80)

    def run_full_check(self):
        """Run complete content completeness check"""
        print("=" * 80)
        print("CONTENT COMPLETENESS CHECK")
        print("=" * 80)
        print(f"PDF: {self.pdf_path.name}")
        print(f"Output: {self.output_dir.name}")
        print("=" * 80)

        # Analyze PDF
        if not self.analyze_pdf():
            return None

        # Analyze JSON
        if not self.analyze_json():
            return None

        # Calculate scores
        self.calculate_completeness_scores()

        # Print summary
        self.print_summary()

        return {
            "pdf": self.pdf_path.name,
            "output_dir": str(self.output_dir),
            "scores": self.scores,
            "found_content": self.found_content,
            "missing_content": self.missing_content,
            "pdf_stats": {
                "pages": self.pdf_content["page_count"],
                "text_length": self.pdf_content["total_text_length"],
                "activities": len(self.pdf_content["activities"]),
                "standards": len(self.pdf_content["standards"])
            },
            "json_stats": {
                "titles": len(self.json_content["titles"]),
                "content_blocks": len(self.json_content["content_blocks"]),
                "activities": len(self.json_content["activities"]),
                "content_length": self.json_content["total_content_length"]
            }
        }


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python content_completeness_checker.py <pdf_path> <output_dir>")
        print("\nExample:")
        print("  python content_completeness_checker.py \\")
        print("    'Input/[TK.1.A1] Lesson_ Identifying 2-D Shapes.pdf' \\")
        print("    'Output_Batch/TK.1.A1_Lesson__Identifying_2-D_Shapes_v2'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]

    checker = ContentCompletenessChecker(pdf_path, output_dir)
    result = checker.run_full_check()

    if result:
        # Save report
        report_file = Path(output_dir) / "content_completeness_report.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()
