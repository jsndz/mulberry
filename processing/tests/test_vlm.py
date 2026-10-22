"""Comprehensive unit tests for the Mulberry VLM module."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
from pydantic import ValidationError
import torch

from processing.canonical import Document, TextKind
from processing.vlm import (
    InferenceError,
    InvalidImageError,
    MalformedOutputError,
    ModelLoadError,
    RuntimeInfo,
    SchemaValidationError,
    VLMBlock,
    VLMBlockType,
    VLMConfig,
    VLMListItem,
    VLMService,
    VLMStructuredOutput,
    VLM_SYSTEM_PROMPT,
    VLM_USER_PROMPT,
    detect_device,
    detect_dtype,
    get_runtime_info,
)
from processing.vlm.model import VLMModelManager
from processing.vlm.processor import VLMOutputProcessor


class TestVLMRuntime:
    """Test CUDA detection, CPU fallback, and dtype selection."""

    def test_detect_device_with_cuda(self):
        with patch("torch.cuda.is_available", return_value=True), patch(
            "torch.cuda.device_count", return_value=1
        ):
            assert detect_device() == "cuda"
            assert detect_device("auto") == "cuda"
            assert detect_device("cuda") == "cuda"
            assert detect_device("cpu") == "cpu"

    def test_detect_device_cpu_fallback(self):
        with patch("torch.cuda.is_available", return_value=False):
            assert detect_device() == "cpu"
            assert detect_device("auto") == "cpu"
            assert detect_device("cuda") == "cpu"  # Graceful fallback to CPU
            assert detect_device("cpu") == "cpu"

    def test_detect_dtype_cuda_bf16_supported(self):
        with patch("torch.cuda.is_bf16_supported", return_value=True):
            dtype = detect_dtype("cuda")
            assert dtype == torch.bfloat16

    def test_detect_dtype_cuda_bf16_unsupported(self):
        with patch("torch.cuda.is_bf16_supported", return_value=False):
            dtype = detect_dtype("cuda")
            assert dtype == torch.float16

    def test_detect_dtype_cpu(self):
        assert detect_dtype("cpu") == torch.float32

    def test_detect_dtype_explicit_preference(self):
        assert detect_dtype("cuda", "bfloat16") == torch.bfloat16
        assert detect_dtype("cuda", "float16") == torch.float16
        assert detect_dtype("cpu", "float32") == torch.float32
        assert detect_dtype("cuda", torch.float16) == torch.float16

    def test_get_runtime_info(self):
        with patch("torch.cuda.is_available", return_value=False):
            info = get_runtime_info(preferred_device="cpu")
            assert isinstance(info, RuntimeInfo)
            assert info.device == "cpu"
            assert info.dtype == torch.float32
            assert info.cuda_available is False


class TestVLMConfig:
    """Test configuration defaults and parameters."""

    def test_default_config(self):
        config = VLMConfig()
        assert config.model_name == "Qwen/Qwen3-VL-4B-Instruct"
        assert config.device is None
        assert config.dtype is None
        assert config.temperature == 0.1
        assert config.top_p == 0.95
        assert config.max_new_tokens == 4096

    def test_custom_config(self):
        config = VLMConfig(
            model_name="custom-vlm",
            device="cpu",
            dtype="float32",
            temperature=0.2,
            max_new_tokens=1024,
        )
        assert config.model_name == "custom-vlm"
        assert config.device == "cpu"
        assert config.temperature == 0.2
        assert config.max_new_tokens == 1024


class TestVLMPrompts:
    """Test prompt templates."""

    def test_prompts_defined(self):
        assert "handwritten" in VLM_SYSTEM_PROMPT.lower()
        assert "JSON" in VLM_SYSTEM_PROMPT
        assert "blocks" in VLM_USER_PROMPT


class TestVLMSchemasAndCanonicalValidation:
    """Test structured parsing, headings, paragraphs, lists, unclear text, and canonical conversion."""

    def test_valid_heading_block(self):
        block = VLMBlock(type=VLMBlockType.HEADING, level=2, text="Notes on Biology")
        assert block.type == VLMBlockType.HEADING
        assert block.level == 2
        assert block.text == "Notes on Biology"

    def test_heading_block_requires_text(self):
        with pytest.raises(ValidationError):
            VLMBlock(type=VLMBlockType.HEADING, text="")

    def test_valid_paragraph_block(self):
        block = VLMBlock(type=VLMBlockType.PARAGRAPH, text="Cell membrane consists of phospholipid bilayer.")
        assert block.type == VLMBlockType.PARAGRAPH
        assert block.text.startswith("Cell")

    def test_paragraph_block_requires_text(self):
        with pytest.raises(ValidationError):
            VLMBlock(type=VLMBlockType.PARAGRAPH, text=None)

    def test_valid_bullet_list_block(self):
        block = VLMBlock(
            type=VLMBlockType.LIST,
            list_type="bullet",
            items=[
                VLMListItem(text="Lipids", level=1),
                VLMListItem(text="Proteins", level=1),
            ],
        )
        assert block.list_type == "bullet"
        assert len(block.items) == 2
        assert block.items[0].text == "Lipids"

    def test_valid_numbered_list_block_from_strings(self):
        block = VLMBlock(
            type=VLMBlockType.LIST,
            list_type="numbered",
            items=["First point", "Second point"],  # Strings normalized automatically
        )
        assert block.list_type == "numbered"
        assert len(block.items) == 2
        assert block.items[0].text == "First point"
        assert block.items[0].index == 1
        assert block.items[1].index == 2

    def test_unclear_block_handling(self):
        block = VLMBlock(type=VLMBlockType.UNCLEAR, text="[unclear: enzyme rate]")
        assert block.type == VLMBlockType.UNCLEAR
        assert "[unclear" in block.text

        block_empty = VLMBlock(type=VLMBlockType.UNCLEAR)
        assert block_empty.text == "[unclear]"

    def test_to_canonical_document_conversion(self):
        output = VLMStructuredOutput(
            blocks=[
                VLMBlock(type=VLMBlockType.HEADING, level=1, text="Main Title", confidence=0.98),
                VLMBlock(type=VLMBlockType.PARAGRAPH, text="Introductory paragraph.", confidence=0.95),
                VLMBlock(
                    type=VLMBlockType.LIST,
                    list_type="bullet",
                    items=[
                        VLMListItem(text="Point A", level=1),
                        VLMListItem(text="Point B", level=2),
                    ],
                    confidence=0.92,
                ),
                VLMBlock(
                    type=VLMBlockType.LIST,
                    list_type="numbered",
                    items=[
                        VLMListItem(text="Step 1", level=1, index=1),
                        VLMListItem(text="Step 2", level=1, index=2),
                    ],
                    confidence=0.94,
                ),
                VLMBlock(type=VLMBlockType.UNCLEAR, text="[illegible date]"),
            ]
        )

        doc = output.to_canonical_document(width=800.0, height=1200.0, doc_id="doc_test_123", source_file="notes.jpg")
        assert isinstance(doc, Document)
        assert doc.id == "doc_test_123"
        assert len(doc.pages) == 1
        page = doc.pages[0]
        assert page.width == 800.0
        assert page.height == 1200.0
        assert page.source_media.file_path == "notes.jpg"

        elements = page.elements
        assert len(elements) == 7  # 1 heading + 1 para + 2 bullets + 2 numbered items + 1 unclear

        # Check heading element
        assert elements[0].type == "text"
        assert elements[0].kind == TextKind.HEADING
        assert elements[0].heading_level == 1
        assert elements[0].content == "Main Title"
        assert elements[0].confidence == 0.98

        # Check paragraph element
        assert elements[1].type == "text"
        assert elements[1].kind == TextKind.PARAGRAPH
        assert elements[1].content == "Introductory paragraph."

        # Check bullet list elements
        assert elements[2].type == "text"
        assert elements[2].kind == TextKind.BULLET
        assert elements[2].list_level == 1
        assert elements[2].content == "Point A"

        assert elements[3].type == "text"
        assert elements[3].kind == TextKind.BULLET
        assert elements[3].list_level == 2
        assert elements[3].content == "Point B"

        # Check numbered list elements
        assert elements[4].type == "text"
        assert elements[4].kind == TextKind.NUMBERED_LIST
        assert elements[4].list_index == 1
        assert elements[4].content == "Step 1"

        assert elements[5].type == "text"
        assert elements[5].kind == TextKind.NUMBERED_LIST
        assert elements[5].list_index == 2
        assert elements[5].content == "Step 2"

        # Check unclear element
        assert elements[6].type == "text"
        assert elements[6].kind == TextKind.PARAGRAPH
        assert elements[6].content == "[illegible date]"

        # Validate canonical JSON serialization and roundtrip
        json_data = doc.model_dump_json()
        reloaded = Document.model_validate_json(json_data)
        assert reloaded.id == doc.id


class TestVLMOutputProcessor:
    """Test JSON extraction, parsing, and malformed output handling."""

    def setup_method(self):
        self.processor = VLMOutputProcessor()

    def test_extract_json_from_code_fence(self):
        raw = """Here is the result:
```json
{
  "blocks": [
    {"type": "heading", "level": 1, "text": "Notes"}
  ]
}
```
Hope this helps!"""
        extracted = self.processor.extract_json_string(raw)
        assert extracted.startswith("{") and extracted.endswith("}")

    def test_extract_json_with_think_tags(self):
        raw = """<think>Thinking about handwriting...</think>
{
  "blocks": [
    {"type": "paragraph", "text": "Hello world"}
  ]
}"""
        extracted = self.processor.extract_json_string(raw)
        assert "<think>" not in extracted
        assert "Hello world" in extracted

    def test_parse_and_validate_success(self):
        raw = """```json
{
  "blocks": [
    {"type": "heading", "level": 1, "text": "Meeting Notes"},
    {"type": "paragraph", "text": "Discussion on Q3 targets."},
    {
      "type": "list",
      "list_type": "bullet",
      "items": [{"text": "Action item 1", "level": 1}]
    }
  ]
}
```"""
        result = self.processor.parse_and_validate(raw)
        assert isinstance(result, VLMStructuredOutput)
        assert len(result.blocks) == 3

    def test_parse_malformed_json_raises_error(self):
        raw = "This is not json: { invalid_key: ... "
        with pytest.raises(MalformedOutputError):
            self.processor.parse_and_validate(raw)

    def test_parse_invalid_schema_raises_error(self):
        # Heading without text
        raw = '{"blocks": [{"type": "heading", "level": 1}]}'
        with pytest.raises(SchemaValidationError):
            self.processor.parse_and_validate(raw)


class TestVLMModelReuseAndSingleton:
    """Test model manager singleton and model reuse."""

    def test_singleton_reuse(self):
        mgr1 = VLMModelManager.get_singleton()
        mgr2 = VLMModelManager.get_singleton()
        assert mgr1 is mgr2

    def test_load_error_wrapped(self):
        mgr = VLMModelManager(VLMConfig(model_name="non_existent_fake_model_12345"))
        with patch("transformers.AutoProcessor.from_pretrained", side_effect=Exception("Model not found")):
            with pytest.raises(ModelLoadError):
                mgr.load()

    def test_inference_error_wrapped(self):
        mgr = VLMModelManager()
        mgr._is_loaded = True
        mgr.model = MagicMock()
        mgr.processor = MagicMock()
        mgr.processor.apply_chat_template.return_value = "prompt"
        mgr.processor.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mgr.model.generate.side_effect = RuntimeError("CUDA out of memory")

        img = Image.new("RGB", (100, 100))
        with pytest.raises(InferenceError):
            mgr.generate(img, "prompt")


class TestVLMService:
    """Test high-level VLMService image inputs and processing pipeline."""

    def test_invalid_image_path_not_found(self):
        service = VLMService()
        with pytest.raises(InvalidImageError, match="not found"):
            service.process("/path/to/non_existent_image_12345.jpg")

    def test_invalid_image_corrupted(self, tmp_path: Path):
        bad_file = tmp_path / "bad.jpg"
        bad_file.write_bytes(b"not an image at all")

        service = VLMService()
        with pytest.raises(InvalidImageError, match="Failed to open/decode"):
            service.process(bad_file)

    def test_invalid_image_type(self):
        service = VLMService()
        with pytest.raises(InvalidImageError, match="Unsupported image input type"):
            service.process(12345)  # type: ignore

    def test_service_end_to_end_mocked(self, tmp_path: Path):
        test_img_path = tmp_path / "notes.png"
        img = Image.new("RGB", (600, 800), color="white")
        img.save(test_img_path)

        mock_manager = MagicMock(spec=VLMModelManager)
        mock_manager.is_loaded = True
        mock_manager.generate.return_value = """```json
{
  "blocks": [
    {"type": "heading", "level": 1, "text": "Calculus Notes", "confidence": 0.99},
    {"type": "paragraph", "text": "Integration by parts formula: integral u dv = uv - integral v du.", "confidence": 0.97},
    {
      "type": "list",
      "list_type": "numbered",
      "items": [
        {"text": "Choose u using LIATE rule", "level": 1, "index": 1},
        {"text": "Compute du and v", "level": 1, "index": 2}
      ],
      "confidence": 0.95
    }
  ]
}
```"""

        service = VLMService(model_manager=mock_manager)

        # Test with path
        doc = service.process(test_img_path)
        assert isinstance(doc, Document)
        assert len(doc.pages) == 1
        page = doc.pages[0]
        assert page.width == 600.0
        assert page.height == 800.0
        assert len(page.elements) == 4  # 1 heading + 1 paragraph + 2 numbered list items
        assert page.elements[0].content == "Calculus Notes"
        assert page.elements[0].kind == TextKind.HEADING
        assert page.elements[2].kind == TextKind.NUMBERED_LIST
        assert page.elements[2].list_index == 1

        # Test with PIL image directly
        doc_pil = service.process(img)
        assert isinstance(doc_pil, Document)
        assert len(doc_pil.pages[0].elements) == 4
