"""
Tests for the AIProcessingPipeline's dynamic context assembly feature.

Validates the keyword-driven context loading from context_library.json,
ensuring the pre-fill stage is optimized correctly based on user input.

Agricultural Context:
This testing is critical for ensuring that the AI assistant receives relevant
and minimal context for its tasks. For example, when a user asks about
"ISO 11783", the system must provide the specific ISOBUS context without
loading irrelevant data, optimizing token usage and response accuracy for
safety-critical agricultural operations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afs_fastapi.services.ai_processing_pipeline import AIProcessingPipeline, PipelineContext

# A mock context library, mirroring the structure of the real one
MOCK_CONTEXT_LIBRARY = {
    "core_context": {
        "id": "core_context",
        "content": "AFS FastAPI Core: 6 mandatory rules.",
    },
    "context_snippets": [
        {
            "id": "tdd",
            "keywords": ["tdd", "test-first", "test"],
            "content": "TDD is RED-GREEN-REFACTOR.",
        },
        {
            "id": "isobus",
            "keywords": ["isobus", "iso 11783"],
            "content": "ISOBUS for tractor-implement communication.",
        },
        {
            "id": "crdt",
            "keywords": ["crdt", "sync"],
            "content": "CRDT for multi-tractor sync.",
        },
    ],
}


@pytest.fixture
def pipeline(tmp_path: Path) -> AIProcessingPipeline:
    """Fixture to create an AIProcessingPipeline with a mock context library."""
    claude_dir = tmp_path / ".claude"
    context_dir = claude_dir / "context"
    context_dir.mkdir(parents=True)

    # Create the mock context library file
    library_file = context_dir / "context_library.json"
    library_file.write_text(json.dumps(MOCK_CONTEXT_LIBRARY))

    # Create a dummy essential.md as the pipeline expects it
    (context_dir / "essential.md").touch()

    return AIProcessingPipeline(project_root=tmp_path)


class TestAIProcessingPipelineDynamicContext:
    """Test suite for the keyword-driven dynamic context assembly."""

    def test_dynamic_context_with_single_keyword(self, pipeline: AIProcessingPipeline):
        """Verify context assembly for a prompt with one matching keyword."""
        context = PipelineContext(user_input="How does tdd work?")
        result_context = pipeline.optimize_pre_fill_stage(context)

        assert "AFS FastAPI Core: 6 mandatory rules." in result_context.essential_content
        assert "Context for 'tdd': TDD is RED-GREEN-REFACTOR." in result_context.essential_content
        assert "isobus" not in result_context.essential_content.lower()

    def test_dynamic_context_with_multiple_keywords(self, pipeline: AIProcessingPipeline):
        """Verify context assembly for a prompt with multiple keywords."""
        context = PipelineContext(user_input="Explain isobus and crdt.")
        result_context = pipeline.optimize_pre_fill_stage(context)

        assert "AFS FastAPI Core: 6 mandatory rules." in result_context.essential_content
        assert (
            "Context for 'isobus': ISOBUS for tractor-implement communication."
            in result_context.essential_content
        )
        assert (
            "Context for 'crdt': CRDT for multi-tractor sync." in result_context.essential_content
        )
        assert "tdd" not in result_context.essential_content.lower()

    def test_dynamic_context_with_no_matching_keywords(self, pipeline: AIProcessingPipeline):
        """Verify that only core context is loaded when no keywords match."""
        context = PipelineContext(user_input="What is the weather like?")
        result_context = pipeline.optimize_pre_fill_stage(context)

        # Should only contain the core context
        assert result_context.essential_content == "AFS FastAPI Core: 6 mandatory rules."

    def test_dynamic_context_is_case_insensitive(self, pipeline: AIProcessingPipeline):
        """Verify that keyword matching is not case-sensitive."""
        context = PipelineContext(user_input="Tell me about ISO 11783.")
        result_context = pipeline.optimize_pre_fill_stage(context)

        assert "AFS FastAPI Core: 6 mandatory rules." in result_context.essential_content
        assert (
            "Context for 'iso 11783': ISOBUS for tractor-implement communication."
            in result_context.essential_content
        )

    def test_dynamic_context_token_savings_calculation(self, pipeline: AIProcessingPipeline):
        """Verify the token savings calculation is correct."""
        # Input that matches one snippet
        context = PipelineContext(user_input="tdd")
        result_context = pipeline.optimize_pre_fill_stage(context)

        # Expected content: core_context + tdd_snippet
        expected_content = (
            "AFS FastAPI Core: 6 mandatory rules.\n\n"
            "Context for 'tdd': TDD is RED-GREEN-REFACTOR."
        )
        assert result_context.essential_content == expected_content

        # Calculation based on implementation:
        # original_tokens is hardcoded to 3000
        # optimized_tokens is len(essential_content) // 4
        original_tokens = 3000
        optimized_tokens = len(expected_content) // 4
        expected_savings = original_tokens - optimized_tokens

        assert result_context.tokens_saved == expected_savings

    def test_dynamic_context_handles_empty_library(self, tmp_path: Path):
        """Test graceful fallback when context_library.json is empty or malformed."""
        claude_dir = tmp_path / ".claude"
        context_dir = claude_dir / "context"
        context_dir.mkdir(parents=True)
        (context_dir / "context_library.json").write_text("{}")  # Empty JSON

        pipeline = AIProcessingPipeline(project_root=tmp_path)
        context = PipelineContext(user_input="test")
        result_context = pipeline.optimize_pre_fill_stage(context)

        # Should fall back to the default content defined in the method
        assert result_context.essential_content == "AFS FastAPI Platform."


class TestAIProcessingPipelinePromptDistillation:
    """Test suite for the context-aware prompt distillation logic."""

    def test_prompt_distillation_removes_matched_keywords(self, pipeline: AIProcessingPipeline):
        """Verify that non-protected keywords are removed from the prompt after pre-fill."""
        # The user asks about 'tdd', which is a non-protected keyword.
        context = PipelineContext(user_input="Can you please explain tdd?")

        # 1. Run pre-fill to populate matched_keywords
        context = pipeline.optimize_pre_fill_stage(context)
        assert "tdd" in context.user_input.lower()

        # 2. Run prompt processing to test distillation
        result_context = pipeline.optimize_prompt_processing_stage(context)

        # Layer 1 (heuristics) removes "Can you please explain".
        # Layer 2 (distillation) should remove "tdd".
        # The final prompt should be empty, then fall back to the original.
        # Let's refine the test case to be more realistic.
        context.user_input = "Can you explain the tdd process?"
        context = pipeline.optimize_pre_fill_stage(context)
        result_context = pipeline.optimize_prompt_processing_stage(context)

        # "Can you explain the" is removed by heuristics.
        # "tdd" is removed by distillation.
        # "process" remains.
        assert result_context.processed_prompt == "process"

    def test_prompt_distillation_protects_safety_keywords(self, pipeline: AIProcessingPipeline):
        """Verify that protected keywords like 'isobus' and 'crdt' are not removed."""
        context = PipelineContext(user_input="Tell me about isobus and crdt for safety.")

        # 1. Run pre-fill to populate context
        context = pipeline.optimize_pre_fill_stage(context)
        assert "isobus" in context.user_input.lower()
        # Note: "crdt" is not in agricultural keywords list

        # 2. Run prompt processing
        result_context = pipeline.optimize_prompt_processing_stage(context)

        # Layer 1 removes "Tell me about".
        # Layer 2 should NOT remove "isobus" or "crdt" as they are protected.
        assert result_context.processed_prompt == "isobus and crdt for safety"

    def test_prompt_distillation_fallback_on_empty_result(self, pipeline: AIProcessingPipeline):
        """Verify fallback when distillation makes the prompt empty."""
        context = PipelineContext(user_input="tdd")
        context = pipeline.optimize_pre_fill_stage(context)
        result_context = pipeline.optimize_prompt_processing_stage(context)

        # Heuristics do nothing. Distillation removes "tdd", making it empty.
        # The fallback should restore the original prompt.
        assert result_context.processed_prompt == "tdd"
