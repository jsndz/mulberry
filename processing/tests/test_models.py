"""Comprehensive Unit Tests for Mulberry Canonical Document Models."""

import json
import pytest
from pydantic import ValidationError

from processing.models import (
    Document,
    Page,
    DocumentMetadata,
    BoundingBox,
    CoordinateUnit,
    SourceMedia,
    TextElement,
    TextKind,
    TextStyle,
    DiagramElement,
    DiagramCategory,
    BoxPrimitive,
    CirclePrimitive,
    LinePrimitive,
    ArrowPrimitive,
    LabelPrimitive,
    ConnectionPrimitive,
    StructuredDiagramData,
    IllustratedDiagramData,
    ImageElement,
    TableElement,
    EquationElement,
)
from processing.exporter import create_realistic_example, generate_json_schema


class TestBoundingBox:
    def test_valid_bounding_box(self):
        box = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, unit=CoordinateUnit.PX)
        assert box.x == 10.0
        assert box.y == 20.0
        assert box.width == 100.0
        assert box.height == 50.0
        assert box.unit == CoordinateUnit.PX

    def test_negative_dimensions_invalid(self):
        with pytest.raises(ValidationError):
            BoundingBox(x=0.0, y=0.0, width=-10.0, height=50.0)
        with pytest.raises(ValidationError):
            BoundingBox(x=0.0, y=0.0, width=10.0, height=-5.0)


class TestTextElement:
    def test_text_element_heading(self):
        elem = TextElement(
            id="t1",
            kind=TextKind.HEADING,
            heading_level=1,
            content="Title",
            position=BoundingBox(x=0.0, y=0.0, width=100.0, height=20.0),
            confidence=0.99,
        )
        assert elem.type == "text"
        assert elem.kind == TextKind.HEADING
        assert elem.heading_level == 1
        assert elem.confidence == 0.99

    def test_text_element_bullet_and_numbered(self):
        bullet = TextElement(
            id="t2",
            kind=TextKind.BULLET,
            list_level=2,
            content="Item 1",
            position=BoundingBox(x=10.0, y=10.0, width=50.0, height=10.0),
        )
        assert bullet.list_level == 2

        num_item = TextElement(
            id="t3",
            kind=TextKind.NUMBERED_LIST,
            list_level=1,
            list_index=3,
            content="3. Third item",
            position=BoundingBox(x=10.0, y=20.0, width=50.0, height=10.0),
        )
        assert num_item.list_index == 3

    def test_invalid_confidence_range(self):
        with pytest.raises(ValidationError):
            TextElement(
                id="t_err",
                kind=TextKind.PARAGRAPH,
                content="Bad confidence",
                position=BoundingBox(x=0.0, y=0.0, width=10.0, height=10.0),
                confidence=1.5,
            )


class TestDiagramElement:
    def test_structured_diagram(self):
        diag = DiagramElement(
            id="d1",
            category=DiagramCategory.STRUCTURED,
            position=BoundingBox(x=0.0, y=0.0, width=300.0, height=200.0),
            confidence=0.95,
            structured_data=StructuredDiagramData(
                primitives=[
                    BoxPrimitive(
                        id="b1",
                        position=BoundingBox(x=10.0, y=10.0, width=50.0, height=30.0),
                        label="Start",
                    ),
                    CirclePrimitive(
                        id="c1",
                        position=BoundingBox(x=100.0, y=10.0, width=40.0, height=40.0),
                        label="End",
                    ),
                    ArrowPrimitive(
                        id="a1",
                        start_point={"x": 60.0, "y": 25.0},
                        end_point={"x": 100.0, "y": 25.0},
                    ),
                    ConnectionPrimitive(
                        id="conn1",
                        source_node_id="b1",
                        target_node_id="c1",
                        label="Next",
                    ),
                ]
            ),
        )
        assert diag.category == DiagramCategory.STRUCTURED
        assert len(diag.structured_data.primitives) == 4
        assert diag.structured_data.primitives[0].primitive_type == "box"

    def test_illustrated_diagram(self):
        diag = DiagramElement(
            id="d2",
            category=DiagramCategory.ILLUSTRATED,
            position=BoundingBox(x=0.0, y=0.0, width=400.0, height=300.0),
            illustrated_data=IllustratedDiagramData(
                image_ref="crops/diagram1.png",
                mime_type="image/png",
                caption="Hand-drawn circuit schematic",
            ),
        )
        assert diag.category == DiagramCategory.ILLUSTRATED
        assert diag.illustrated_data.image_ref == "crops/diagram1.png"


class TestDocumentSerialization:
    def test_realistic_example_roundtrip(self):
        doc = create_realistic_example()
        json_str = doc.model_dump_json()
        assert isinstance(json_str, str)

        # Deserialize back to Document
        parsed_doc = Document.model_validate_json(json_str)
        assert parsed_doc.id == doc.id
        assert len(parsed_doc.pages) == 1

        elements = parsed_doc.pages[0].elements
        assert len(elements) == 10

        # Check polymorphic element discrimination
        assert elements[0].type == "text"
        assert elements[0].kind == TextKind.HEADING
        assert elements[5].type == "diagram"
        assert elements[5].category == DiagramCategory.STRUCTURED
        assert elements[7].type == "diagram"
        assert elements[7].category == DiagramCategory.ILLUSTRATED

    def test_extensibility_stubs(self):
        page = Page(
            page_number=1,
            width=800.0,
            height=1000.0,
            elements=[
                ImageElement(
                    id="img1",
                    position=BoundingBox(x=0.0, y=0.0, width=200.0, height=150.0),
                    image_ref="photo.jpg",
                ),
                TableElement(
                    id="tbl1",
                    position=BoundingBox(x=0.0, y=160.0, width=400.0, height=200.0),
                    headers=["Col 1", "Col 2"],
                    rows=[["A", "B"], ["C", "D"]],
                ),
                EquationElement(
                    id="eq1",
                    position=BoundingBox(x=0.0, y=370.0, width=200.0, height=50.0),
                    latex="E = mc^2",
                    display_mode=True,
                ),
            ],
        )
        doc = Document(id="ext_doc", pages=[page])
        dumped = json.loads(doc.model_dump_json())
        reloaded = Document.model_validate(dumped)
        assert reloaded.pages[0].elements[0].type == "image"
        assert reloaded.pages[0].elements[1].type == "table"
        assert reloaded.pages[0].elements[2].type == "equation"

    def test_json_schema_generation(self):
        schema = generate_json_schema()
        assert "$defs" in schema or "properties" in schema
        assert "Document" in schema.get("title", "") or "Document" in schema.get("$anchor", "") or "properties" in schema
