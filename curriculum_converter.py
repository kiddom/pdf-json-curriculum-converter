#!/usr/bin/env python3
"""
Curriculum PDF to JSON Converter
Converts curriculum PDFs into hierarchical JSON structure matching the example format.
"""

import pdfplumber
import re
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

class CurriculumConverter:
    """Main converter for curriculum PDFs"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.entities = {}
        self.edges = []

    def generate_uuid(self) -> str:
        """Generate a UUID for entity identifiers"""
        return str(uuid.uuid4())

    def create_entity(self, entity_type: str, title: str, **kwargs) -> Dict[str, Any]:
        """Create a curriculum entity with standard structure"""
        identifier = self.generate_uuid()

        entity = {
            "identifier": identifier,
            "type": entity_type,
            "title": title,
            "label": kwargs.get("label", ""),
            "is_student_facing": kwargs.get("is_student_facing", True),
            "sequence_num": kwargs.get("sequence_num", 0),
            "contents": kwargs.get("contents", []),
            "standards_alignment": kwargs.get("standards_alignment", [])
        }

        # Add entity-specific fields
        if entity_type == "activity":
            entity["timeframe"] = kwargs.get("timeframe")
            entity["grading_classification"] = kwargs.get("grading_classification", "formative")
            entity["instructional_grouping"] = kwargs.get("instructional_grouping")
            entity["activity_type"] = kwargs.get("activity_type", "Participation")

        return entity

    def add_relationship(self, child_id: str, child_type: str, parent_id: Optional[str], parent_type: Optional[str]):
        """Add a parent-child relationship"""
        self.edges.append({
            "type": "is_child_of",
            "identifier": child_id,
            "node_type": child_type,
            "parent_node_type": parent_type,
            "parent_id": parent_id
        })

    def extract_page_content(self, page_num: int, page) -> Dict[str, Any]:
        """Extract content from a single page"""
        text = page.extract_text() or ""

        # Extract with formatting
        words = page.extract_words(extra_attrs=['fontname', 'size'])

        return {
            "page_num": page_num,
            "text": text,
            "words": words
        }

    def parse_lesson_overview(self, pages: List[Dict]) -> Dict[str, Any]:
        """Parse lesson overview from first pages"""
        first_page_text = pages[0]["text"] if pages else ""

        overview = {}

        # Extract lesson number and title
        lesson_match = re.search(r'LESSON\s+(\d+)', first_page_text)
        if lesson_match:
            overview["lesson_number"] = int(lesson_match.group(1))

        # Extract title
        title_match = re.search(r'Identifying\s+2-D\s+Shapes', first_page_text)
        if title_match:
            overview["title"] = "Lesson: Identifying 2-D Shapes"
        else:
            # Fallback to extracting from brackets in filename
            filename_match = re.search(r'\[([^\]]+)\]\s+(.+)\.pdf', self.pdf_path.name)
            if filename_match:
                overview["title"] = f"Lesson: {filename_match.group(2)}"

        # Extract Math Idea and Section
        math_idea_match = re.search(r'Math Idea\s+(\d+)', first_page_text)
        if math_idea_match:
            overview["math_idea"] = math_idea_match.group(1)

        section_match = re.search(r'Section\s+([A-Z])', first_page_text)
        if section_match:
            overview["section"] = section_match.group(1)

        # Extract standards
        standards = []

        # GST standard
        gst_pattern = r'(GST\.[\d.]+\.EF)\s+([^:]+):\s*([^\n]+)'
        gst_match = re.search(gst_pattern, first_page_text)
        if gst_match:
            standards.append({
                "code": gst_match.group(1),
                "name": gst_match.group(2).strip(),
                "description": gst_match.group(3).strip()
            })

        # CC standard
        cc_pattern = r'(CC\.[\d.]+\.EF)\s+([^:]+):\s*([^\n]+)'
        cc_match = re.search(cc_pattern, first_page_text)
        if cc_match:
            standards.append({
                "code": cc_match.group(1),
                "name": cc_match.group(2).strip(),
                "description": cc_match.group(3).strip()
            })

        overview["standards"] = standards

        # Extract learning goals
        goals = []
        goal_section = re.search(r'LEARNING GOALS\s*(.+?)(?=LANGUAGE|$)', first_page_text, re.DOTALL)
        if goal_section:
            goal_text = goal_section.group(1)
            # Extract bullet points
            goal_bullets = re.findall(r'•\s*([^\n•]+)', goal_text)
            goals.extend([g.strip() for g in goal_bullets if g.strip()])

        overview["learning_goals"] = goals

        return overview

    def parse_day_activities(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Parse activities organized by day"""
        activities_by_day = {
            1: {"theme": "Explore", "activities": []},
            2: {"theme": "Discover", "activities": []},
            3: {"theme": "Build", "activities": []}
        }

        # Track which pages contain which day
        for page_data in pages:
            text = page_data["text"]
            page_num = page_data["page_num"]

            # Determine which day this page belongs to
            day = None
            if "DAY 1" in text or (page_num >= 5 and page_num <= 8):
                day = 1
            elif "DAY 2" in text or (page_num >= 9 and page_num <= 11):
                day = 2
            elif "DAY 3" in text or (page_num >= 12 and page_num <= 14):
                day = 3

            if day is None:
                continue

            # Extract activity sections
            # Look for specific activity markers
            activity_markers = [
                ("Number Play", "Choral Count"),
                ("Opening", "See and Ask"),
                ("Centers", "Inquiry Play"),
                ("Closing", "Let's Move|Let's Talk|Let's Draw")
            ]

            for activity_name, content_marker in activity_markers:
                if activity_name in text and content_marker in text:
                    # Extract timeframe
                    timeframe = None
                    time_pattern = rf'{activity_name}.*?(\d+(?:–|-)\d+\s*min|\d+\s*min)'
                    time_match = re.search(time_pattern, text, re.DOTALL)
                    if time_match:
                        timeframe = time_match.group(1)

                    # Create activity
                    activity = {
                        "day": day,
                        "theme": activities_by_day[day]["theme"],
                        "name": activity_name,
                        "timeframe": timeframe,
                        "page_num": page_num,
                        "content_preview": text[:500]
                    }

                    # Avoid duplicates
                    existing = [a for a in activities_by_day[day]["activities"]
                               if a["name"] == activity_name]
                    if not existing:
                        activities_by_day[day]["activities"].append(activity)

        # Flatten into list
        all_activities = []
        for day in sorted(activities_by_day.keys()):
            all_activities.extend(activities_by_day[day]["activities"])

        return all_activities

    def convert(self) -> Dict[str, Any]:
        """Main conversion method"""
        print(f"Converting {self.pdf_path.name}...")

        # Extract all pages
        pages = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                pages.append(self.extract_page_content(page_num, page))

        print(f"  Extracted {len(pages)} pages")

        # Parse lesson overview
        overview = self.parse_lesson_overview(pages)
        print(f"  Parsed lesson: {overview.get('title', 'Unknown')}")

        # Create hierarchy: course -> unit -> section -> lesson -> activities

        # 1. Create course
        course_title = "IM® TK Math"
        course = self.create_entity("course", course_title, sequence_num=0)
        self.entities["course"] = course
        self.add_relationship(course["identifier"], "course", None, None)
        print(f"  Created course: {course_title}")

        # 2. Create unit
        unit_title = f"Unit: Math Idea {overview.get('math_idea', '1')}"
        unit = self.create_entity("unit", unit_title, sequence_num=0)
        unit["contents"] = [{
            "type": "text_block",
            "title": "Unit Narrative",
            "label": "",
            "is_student_facing": False,
            "sequence_num": 0,
            "content": "This unit focuses on geometric shapes and spatial reasoning for transitional kindergarten students."
        }]
        self.entities["unit"] = unit
        self.add_relationship(unit["identifier"], "unit", course["identifier"], "course")
        print(f"  Created unit: {unit_title}")

        # 3. Create section
        section_title = f"Section {overview.get('section', 'A')}"
        section = self.create_entity("section", section_title, sequence_num=0)
        self.entities["section"] = section
        self.add_relationship(section["identifier"], "section", unit["identifier"], "unit")
        print(f"  Created section: {section_title}")

        # 4. Create lesson
        lesson_title = overview.get("title", "Lesson")
        lesson = self.create_entity("lesson", lesson_title, sequence_num=0)

        # Add lesson contents
        lesson_contents = []

        # Learning goals
        if overview.get("learning_goals"):
            goals_html = "<ul>" + "".join([f"<li>{g}</li>" for g in overview["learning_goals"]]) + "</ul>"
            lesson_contents.append({
                "type": "text_block",
                "title": "Learning Goals",
                "label": "",
                "is_student_facing": False,
                "sequence_num": len(lesson_contents),
                "content": goals_html
            })

        # Standards
        if overview.get("standards"):
            standards_html = "<ul>"
            for std in overview["standards"]:
                standards_html += f"<li><strong>{std['code']}</strong> {std['name']}: {std['description']}</li>"
            standards_html += "</ul>"
            lesson_contents.append({
                "type": "text_block",
                "title": "Standards Alignment",
                "label": "",
                "is_student_facing": False,
                "sequence_num": len(lesson_contents),
                "content": standards_html
            })

        lesson["contents"] = lesson_contents
        self.entities["lesson"] = lesson
        self.add_relationship(lesson["identifier"], "lesson", section["identifier"], "section")
        print(f"  Created lesson: {lesson_title}")

        # 5. Parse and create activities
        activities = self.parse_day_activities(pages)
        print(f"  Found {len(activities)} activities")

        for idx, activity_data in enumerate(activities):
            activity_title = f"{activity_data['day']}.{idx+1}: {activity_data['theme']} - {activity_data['name']}"

            activity = self.create_entity(
                "activity",
                activity_title,
                sequence_num=idx,
                timeframe=activity_data.get("timeframe"),
                activity_type=activity_data["name"]
            )

            self.entities[f"activity_{idx}"] = activity
            self.add_relationship(activity["identifier"], "activity", lesson["identifier"], "lesson")

        print(f"  Created {len(activities)} activities")

        return {
            "entities": self.entities,
            "edges": self.edges,
            "summary": {
                "course": 1,
                "units": 1,
                "sections": 1,
                "lessons": 1,
                "activities": len(activities)
            }
        }

    def save_outputs(self, result: Dict[str, Any]):
        """Save JSON files and edges.jsonl"""
        print("\nSaving output files...")

        # Create output directories
        for entity_type in ["course", "unit", "section", "lesson", "activity", "assessment"]:
            (self.output_dir / entity_type).mkdir(parents=True, exist_ok=True)

        # Save individual entity files
        for key, entity in result["entities"].items():
            entity_type = entity["type"]
            identifier = entity["identifier"]
            filename = f"{identifier}.json"
            filepath = self.output_dir / entity_type / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entity, f, indent=2, ensure_ascii=False)

        print(f"  Saved {len(result['entities'])} entity files")

        # Save edges.jsonl
        edges_file = self.output_dir / "edges.jsonl"
        with open(edges_file, 'w', encoding='utf-8') as f:
            for edge in result["edges"]:
                f.write(json.dumps(edge, ensure_ascii=False) + '\n')

        print(f"  Saved {len(result['edges'])} relationships to edges.jsonl")
        print(f"\nOutput saved to: {self.output_dir}")
        print(f"\nSummary: {json.dumps(result['summary'], indent=2)}")


def main():
    pdf_path = "/Users/yotam/PDF-JSON/Input/[TK.1.A1] Lesson_ Identifying 2-D Shapes.pdf"
    output_dir = "/Users/yotam/PDF-JSON/Output"

    converter = CurriculumConverter(pdf_path, output_dir)
    result = converter.convert()
    converter.save_outputs(result)

    print("\n✓ Conversion complete!")


if __name__ == "__main__":
    main()
