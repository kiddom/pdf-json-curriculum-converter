#!/usr/bin/env python3
"""
Curriculum PDF to JSON Converter - V3 Enhanced Activity Extraction
===================================================================
Fixes the critical issue: Activities have empty contents[] arrays

Key improvements over V2:
- Extracts full activity content from pages 5-14
- Properly segments activities by their section headers
- Captures time allocations, materials, guidance, procedures
- Maintains deterministic extraction (no AI)
"""

import pdfplumber
import re
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class ActivityContentExtractor:
    """Extract detailed activity content from lesson PDFs"""

    def __init__(self):
        # Activity section headers to look for
        self.activity_headers = [
            'Number Play',
            'Opening',
            'Centers',
            'Closing',
            "Let's Move!",
            "Let's Talk!",
            "Let's Draw!",
            'See and Ask',
            'Time to Count',
            'Inquiry Play',
            'Partner Play',
            'Teacher-Led Play'
        ]

        # DAY markers
        self.day_markers = ['DAY 1', 'DAY 2', 'DAY 3', 'Explore', 'Discover', 'Build']

    def extract_all_text_from_activity_pages(self, pdf) -> str:
        """Extract text from pages that contain activity details (typically 5-14)"""
        all_text = ""

        # Skip first few pages (usually overview, materials list)
        # Activities typically start on page 5
        start_page = min(4, len(pdf.pages) - 1)  # Page 5 (0-indexed)

        for page_num in range(start_page, len(pdf.pages)):
            text = pdf.pages[page_num].extract_text() or ""
            all_text += text + "\n\n=== PAGE_BREAK ===\n\n"

        return all_text

    def find_activity_sections(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Find all activity sections in text
        Returns: [(activity_title, start_pos, end_pos), ...]
        """
        sections = []

        # Find all occurrences of activity headers
        for header in self.activity_headers:
            # Look for header as standalone line
            pattern = rf'\n({re.escape(header)}(?:[:\s][^\n]*)?)\n'

            for match in re.finditer(pattern, text):
                title = match.group(1).strip()
                start_pos = match.end()
                sections.append((title, start_pos, match.start()))

        # Sort by position
        sections.sort(key=lambda x: x[2])

        # Calculate end positions (start of next section)
        final_sections = []
        for i, (title, start_pos, title_pos) in enumerate(sections):
            if i < len(sections) - 1:
                end_pos = sections[i + 1][2]  # Start of next section
            else:
                end_pos = len(text)

            final_sections.append((title, start_pos, end_pos))

        return final_sections

    def extract_activity_content(self, text: str, start_pos: int, end_pos: int) -> Dict[str, Any]:
        """Extract structured content from an activity section"""
        content = text[start_pos:end_pos].strip()

        # Extract components
        result = {
            'full_text': content,
            'paragraphs': [],
            'timeframe': None,
            'materials': [],
            'guidance': [],
            'preparation': []
        }

        # Extract timeframe
        timeframe_match = re.search(r'(\d+(?:–|-)\d+\s*min|\d+\s*min)', content)
        if timeframe_match:
            result['timeframe'] = timeframe_match.group(1)

        # Extract materials section
        materials_match = re.search(r'Materials?\s*\n(.*?)(?=\n(?:Preparation|Guidance|Activity)|$)',
                                   content, re.DOTALL | re.IGNORECASE)
        if materials_match:
            materials_text = materials_match.group(1)
            # Extract bullet points
            result['materials'] = self._extract_bullets(materials_text)

        # Extract preparation section
        prep_match = re.search(r'Preparation\s*\n(.*?)(?=\n(?:Materials|Guidance|Activity)|$)',
                              content, re.DOTALL | re.IGNORECASE)
        if prep_match:
            prep_text = prep_match.group(1)
            result['preparation'] = self._extract_bullets(prep_text)

        # Extract guidance section
        guidance_match = re.search(r'Guidance\s*\n(.*?)(?=\n(?:Materials|Preparation|Activity)|$)',
                                  content, re.DOTALL | re.IGNORECASE)
        if guidance_match:
            guidance_text = guidance_match.group(1)
            result['guidance'] = self._extract_bullets(guidance_text)

        # Extract paragraphs (blocks of text)
        paragraphs = self._extract_paragraphs(content)
        result['paragraphs'] = paragraphs

        return result

    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        bullets = []

        # Pattern 1: • bullets
        for match in re.finditer(r'•\s*([^\n•]+)', text):
            bullets.append(match.group(1).strip())

        # Pattern 2: º bullets
        for match in re.finditer(r'º\s*([^\nº]+)', text):
            bullets.append(match.group(1).strip())

        return bullets

    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraph blocks from text"""
        # Split into lines
        lines = text.split('\n')

        paragraphs = []
        current_para = []

        for line in lines:
            line = line.strip()

            # Skip empty lines and very short lines
            if not line or len(line) < 10:
                if current_para:
                    para_text = ' '.join(current_para)
                    if len(para_text) > 30:
                        paragraphs.append(para_text)
                    current_para = []
                continue

            # Skip section headers
            if line in ['Materials', 'Preparation', 'Guidance', 'Activity']:
                continue

            current_para.append(line)

        # Add last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            if len(para_text) > 30:
                paragraphs.append(para_text)

        return paragraphs

    def format_as_html(self, activity_content: Dict[str, Any]) -> str:
        """Convert extracted activity content to HTML"""
        html_parts = []

        # Timeframe
        if activity_content.get('timeframe'):
            html_parts.append(f"<p><strong>Time:</strong> {activity_content['timeframe']}</p>")

        # Materials
        if activity_content.get('materials'):
            html_parts.append("<p><strong>Materials:</strong></p>")
            html_parts.append("<ul>")
            for material in activity_content['materials']:
                html_parts.append(f"<li>{material}</li>")
            html_parts.append("</ul>")

        # Preparation
        if activity_content.get('preparation'):
            html_parts.append("<p><strong>Preparation:</strong></p>")
            html_parts.append("<ul>")
            for prep in activity_content['preparation']:
                html_parts.append(f"<li>{prep}</li>")
            html_parts.append("</ul>")

        # Guidance
        if activity_content.get('guidance'):
            html_parts.append("<p><strong>Guidance:</strong></p>")
            html_parts.append("<ul>")
            for guide in activity_content['guidance']:
                html_parts.append(f"<li>{guide}</li>")
            html_parts.append("</ul>")

        # Paragraphs
        for para in activity_content.get('paragraphs', []):
            html_parts.append(f"<p>{para}</p>")

        return '\n'.join(html_parts)


class CurriculumConverterV3:
    """Enhanced converter with proper activity content extraction"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.entities = defaultdict(list)
        self.edges = []
        self.activity_extractor = ActivityContentExtractor()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_uuid(self) -> str:
        """Generate a unique identifier"""
        return str(uuid.uuid4())

    def create_entity(self, entity_type: str, title: str, **kwargs) -> Dict[str, Any]:
        """Create a standard entity"""
        identifier = self.generate_uuid()

        entity = {
            "identifier": identifier,
            "type": entity_type,
            "title": title,
            "label": kwargs.get("label", title),
            "is_student_facing": kwargs.get("is_student_facing", False),
            "sequence_num": kwargs.get("sequence_num", 1),
            "contents": kwargs.get("contents", [])
        }

        return entity

    def extract_title_from_pdf(self, pdf) -> str:
        """Extract lesson title from first page"""
        first_page = pdf.pages[0].extract_text() or ""
        lines = first_page.split('\n')

        # Look for lesson title patterns
        for line in lines[:10]:
            line = line.strip()
            if 'Lesson' in line and len(line) > 10:
                return line

        # Fallback
        return self.pdf_path.stem

    def extract_learning_goals(self, pdf) -> List[str]:
        """Extract learning goals from first few pages"""
        text = ""
        for page in pdf.pages[:3]:
            text += page.extract_text() or ""

        goals = []

        # Look for "Learning Goals" section
        lg_match = re.search(r'LEARNING GOALS?\s*:?\s*(.*?)(?=\n[A-Z\s]{3,}:|Standards|$)',
                            text, re.DOTALL | re.IGNORECASE)

        if lg_match:
            goals_text = lg_match.group(1)
            # Extract bullet points
            for match in re.finditer(r'[•●]\s*([^\n•●]+)', goals_text):
                goal = match.group(1).strip()
                if len(goal) > 20:
                    goals.append(goal)

        return goals

    def extract_standards(self, pdf) -> List[str]:
        """Extract learning standards"""
        text = ""
        for page in pdf.pages[:3]:
            text += page.extract_text() or ""

        standards = []

        # Pattern: GST.x.x.EF Description
        for match in re.finditer(r'(GST\.[\d.]+\.EF)\s+([^:]+):\s*([^\n]+)', text):
            code = match.group(1)
            title = match.group(2).strip()
            desc = match.group(3).strip()
            standards.append(f"{code} {title}: {desc}")

        return standards

    def convert(self):
        """Main conversion process"""
        print(f"Converting: {self.pdf_path.name}")
        print("-" * 80)

        with pdfplumber.open(self.pdf_path) as pdf:
            page_count = len(pdf.pages)
            print(f"  Pages: {page_count}")

            # Extract basic info
            lesson_title = self.extract_title_from_pdf(pdf)
            learning_goals = self.extract_learning_goals(pdf)
            standards = self.extract_standards(pdf)

            print(f"  Lesson: {lesson_title}")
            print(f"  Learning goals: {len(learning_goals)}")
            print(f"  Standards: {len(standards)}")

            # Create hierarchy
            course_id = self.create_course()
            unit_id = self.create_unit(course_id)
            section_id = self.create_section(unit_id)
            lesson_id = self.create_lesson(section_id, lesson_title, learning_goals, standards)

            # Detect PDF type and extract accordingly
            if page_count <= 3:
                # This is likely a single-activity PDF
                print(f"  Type: Single-activity PDF")
                activities_created = self.extract_single_activity_pdf(pdf, lesson_id)
            else:
                # This is a multi-activity lesson PDF
                print(f"  Type: Multi-activity lesson PDF")
                activities_created = self.extract_activities_with_content(pdf, lesson_id)

            print(f"  Activities: {activities_created}")

            # Save all entities
            self.save_entities()
            self.save_edges()

        print(f"✓ Conversion complete: {self.output_dir}")

        return {
            "lesson": lesson_title,
            "activities": activities_created,
            "learning_goals": len(learning_goals),
            "standards": len(standards)
        }

    def create_course(self) -> str:
        """Create course entity"""
        course = self.create_entity(
            "course",
            "Mathematics TK",
            sequence_num=1
        )
        self.entities["course"].append(course)

        # Root edge
        self.edges.append({
            "type": "edge",
            "identifier": course["identifier"],
            "node_type": "course",
            "parent_node_type": None,
            "parent_id": None
        })

        return course["identifier"]

    def create_unit(self, parent_id: str) -> str:
        """Create unit entity"""
        unit = self.create_entity(
            "unit",
            "Shapes and Numbers",
            sequence_num=1
        )
        self.entities["unit"].append(unit)

        self.edges.append({
            "type": "edge",
            "identifier": unit["identifier"],
            "node_type": "unit",
            "parent_node_type": "course",
            "parent_id": parent_id
        })

        return unit["identifier"]

    def create_section(self, parent_id: str) -> str:
        """Create section entity"""
        section = self.create_entity(
            "section",
            "Introduction to 2-D Shapes",
            sequence_num=1
        )
        self.entities["section"].append(section)

        self.edges.append({
            "type": "edge",
            "identifier": section["identifier"],
            "node_type": "section",
            "parent_node_type": "unit",
            "parent_id": parent_id
        })

        return section["identifier"]

    def create_lesson(self, parent_id: str, title: str,
                     learning_goals: List[str], standards: List[str]) -> str:
        """Create lesson entity with content"""
        contents = []

        # Add learning goals
        if learning_goals:
            goals_html = "<ul>\n"
            for goal in learning_goals:
                goals_html += f"<li>{goal}</li>\n"
            goals_html += "</ul>"

            contents.append({
                "title": "Learning Goals",
                "content": goals_html
            })

        # Add standards
        if standards:
            standards_html = "<ul>\n"
            for standard in standards:
                standards_html += f"<li>{standard}</li>\n"
            standards_html += "</ul>"

            contents.append({
                "title": "Standards Alignment",
                "content": standards_html
            })

        lesson = self.create_entity(
            "lesson",
            title,
            sequence_num=1,
            contents=contents
        )

        # Add standards and learning_goals as separate fields for completeness checking
        lesson["standards"] = standards
        lesson["learning_goals"] = learning_goals

        self.entities["lesson"].append(lesson)

        self.edges.append({
            "type": "edge",
            "identifier": lesson["identifier"],
            "node_type": "lesson",
            "parent_node_type": "section",
            "parent_id": parent_id
        })

        return lesson["identifier"]

    def extract_single_activity_pdf(self, pdf, parent_id: str) -> int:
        """Extract content from a single-activity PDF (1-3 pages)"""

        # Extract all text from the PDF
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text += text + "\n\n"

        # Get title from filename or first page
        activity_title = self.pdf_path.stem
        if "[" in activity_title and "]" in activity_title:
            # Extract title after bracket notation
            activity_title = activity_title.split("]")[-1].strip()

        # Extract structured content from the entire PDF
        activity_content = {
            'full_text': all_text,
            'paragraphs': [],
            'timeframe': None,
            'materials': [],
            'guidance': [],
            'preparation': []
        }

        # Extract sections
        # Materials
        materials_match = re.search(r'Materials?\s*\n(.*?)(?=\nPreparation|\nGuidance|\nActivity|\n[A-Z][a-z]+:|$)',
                                   all_text, re.DOTALL | re.IGNORECASE)
        if materials_match:
            materials_text = materials_match.group(1)
            activity_content['materials'] = self.activity_extractor._extract_bullets(materials_text)

        # Preparation
        prep_match = re.search(r'Preparation\s*\n(.*?)(?=\nMaterials|\nGuidance|\nActivity|\n[A-Z][a-z]+:|$)',
                              all_text, re.DOTALL | re.IGNORECASE)
        if prep_match:
            prep_text = prep_match.group(1)
            activity_content['preparation'] = self.activity_extractor._extract_bullets(prep_text)

        # Guidance/Activity
        guidance_match = re.search(r'(?:Guidance|Activity)\s*\n(.*?)(?=\nDifferentiation|$)',
                                  all_text, re.DOTALL | re.IGNORECASE)
        if guidance_match:
            guidance_text = guidance_match.group(1)
            activity_content['guidance'] = self.activity_extractor._extract_bullets(guidance_text)

        # Timeframe
        timeframe_match = re.search(r'(\d+(?:–|-)\d+\s*min|\d+\s*min)', all_text)
        if timeframe_match:
            activity_content['timeframe'] = timeframe_match.group(1)

        # Extract paragraphs
        activity_content['paragraphs'] = self.activity_extractor._extract_paragraphs(all_text)

        # Format as HTML
        content_html = self.activity_extractor.format_as_html(activity_content)

        # If no structured content extracted, include full text
        if not content_html or len(content_html) < 100:
            # Fall back to including all text as paragraphs
            paragraphs = [p for p in all_text.split('\n\n') if len(p.strip()) > 30]
            content_html = '\n'.join([f"<p>{p.strip()}</p>" for p in paragraphs[:10]])

        # Create content blocks
        contents = []
        if content_html:
            contents.append({
                "title": "Activity Details",
                "content": content_html
            })

        # Create single activity entity
        activity = self.create_entity(
            "activity",
            activity_title,
            sequence_num=1,
            contents=contents,
            is_student_facing=True
        )

        self.entities["activity"].append(activity)

        self.edges.append({
            "type": "edge",
            "identifier": activity["identifier"],
            "node_type": "activity",
            "parent_node_type": "lesson",
            "parent_id": parent_id
        })

        return 1

    def extract_activities_with_content(self, pdf, parent_id: str) -> int:
        """Extract activities WITH their full content - THIS IS THE KEY FIX"""

        # Get all text from activity pages
        all_text = self.activity_extractor.extract_all_text_from_activity_pages(pdf)

        # Find all activity sections
        activity_sections = self.activity_extractor.find_activity_sections(all_text)

        print(f"  Found {len(activity_sections)} activity sections")

        # Create activity entities with content
        for i, (title, start_pos, end_pos) in enumerate(activity_sections, 1):
            # Extract structured content
            activity_content = self.activity_extractor.extract_activity_content(
                all_text, start_pos, end_pos
            )

            # Format as HTML
            content_html = self.activity_extractor.format_as_html(activity_content)

            # Create content blocks
            contents = []
            if content_html:
                contents.append({
                    "title": "Activity Details",
                    "content": content_html
                })

            # Create activity entity
            activity = self.create_entity(
                "activity",
                title,
                sequence_num=i,
                contents=contents,
                is_student_facing=True
            )

            self.entities["activity"].append(activity)

            self.edges.append({
                "type": "edge",
                "identifier": activity["identifier"],
                "node_type": "activity",
                "parent_node_type": "lesson",
                "parent_id": parent_id
            })

        return len(activity_sections)

    def save_entities(self):
        """Save all entities to JSON files"""
        for entity_type, entity_list in self.entities.items():
            # Create folder
            folder = self.output_dir / entity_type
            folder.mkdir(exist_ok=True)

            # Save each entity
            for entity in entity_list:
                filename = folder / f"{entity['identifier']}.json"
                with open(filename, 'w') as f:
                    json.dump(entity, f, indent=2)

    def save_edges(self):
        """Save edges to JSONL file"""
        edges_file = self.output_dir / "edges.jsonl"
        with open(edges_file, 'w') as f:
            for edge in self.edges:
                f.write(json.dumps(edge) + '\n')


def main():
    # Default paths
    pdf_path = "/Users/yotam/PDF-JSON/Input/[TK.1.A1] Lesson_ Identifying 2-D Shapes.pdf"
    output_dir = "/Users/yotam/PDF-JSON/Output_V3"

    converter = CurriculumConverterV3(pdf_path, output_dir)
    result = converter.convert()

    print("\n" + "="*80)
    print("CONVERSION SUMMARY")
    print("="*80)
    print(f"Lesson: {result['lesson']}")
    print(f"Activities created: {result['activities']}")
    print(f"Learning goals: {result['learning_goals']}")
    print(f"Standards: {result['standards']}")
    print(f"\nOutput: {output_dir}")


if __name__ == "__main__":
    main()
