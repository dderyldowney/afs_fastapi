#!/usr/bin/env python3
"""
Test suite for AI Processing Pipeline Token Optimization System.

Tests the integrated token optimization system across all AI processing stages:
pre-fill, prompt processing, generation, and decoding for agricultural robotics platform.
"""

import json
from unittest.mock import patch

import pytest

from afs_fastapi.services.ai_processing_pipeline import (
    AIProcessingPipeline,
    OptimizationLevel,
    PipelineContext,
    ProcessingStage,
    TargetFormat,
)


class TestAIProcessingPipeline:
    """Test suite for integrated AI processing pipeline optimization."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create temporary project structure for testing."""
        claude_dir = tmp_path / ".claude"
        context_dir = claude_dir / "context"
        context_dir.mkdir(parents=True)

        # Create essential context file
        essential_md = context_dir / "essential.md"
        essential_md.write_text("# Essential Context\n- Test content")

        # Create session state file
        session_state = {
            "session_metadata": {"context_level": "essential"},
            "compression_stats": {"reduction_percentage": 96.0},
        }
        session_state_file = context_dir / "session_state.json"
        session_state_file.write_text(json.dumps(session_state))

        return tmp_path

    @pytest.fixture
    def pipeline(self, mock_project_root):
        """Create AI processing pipeline instance for testing."""
        return AIProcessingPipeline(project_root=mock_project_root)

    def test_pipeline_initialization(self, pipeline):
        """Test AI processing pipeline initializes with proper configuration."""
        # RED: Test that pipeline initializes with correct stages
        assert pipeline.stages == [
            ProcessingStage.PRE_FILL,
            ProcessingStage.PROMPT_PROCESSING,
            ProcessingStage.GENERATION,
            ProcessingStage.DECODING,
        ]
        assert pipeline.optimization_level == OptimizationLevel.ADAPTIVE
        assert pipeline.agricultural_context_preserved is True

    def test_pre_fill_stage_optimization(self, pipeline):
        """Test pre-fill stage applies context compression optimization."""
        # RED: Test pre-fill stage reduces token usage through context optimization
        context = PipelineContext(
            user_input="Help me implement tractor coordination",
            session_context="Full agricultural robotics documentation",
            optimization_target=0.4,  # 40% reduction target
        )

        optimized_context = pipeline.optimize_pre_fill_stage(context)

        assert optimized_context.tokens_saved > 0
        assert optimized_context.agricultural_safety_preserved is True
        assert "tractor" in optimized_context.essential_content.lower()

    def test_prompt_processing_stage_optimization(self, pipeline):
        """Test prompt processing stage optimizes input formatting."""
        # RED: Test prompt processing reduces redundancy while preserving intent
        context = PipelineContext(
            user_input="Can you help me implement multi-tractor fleet coordination using ISO 11783 compliance with safety features and error handling?",
            session_context="Previous context about agricultural systems",
            optimization_target=0.3,  # 30% reduction target
        )

        optimized_prompt = pipeline.optimize_prompt_processing_stage(context)

        assert optimized_prompt.tokens_saved > 0
        assert "iso 11783" in optimized_prompt.processed_prompt.lower()
        assert "safety" in optimized_prompt.processed_prompt.lower()
        assert len(optimized_prompt.processed_prompt) < len(context.user_input)

    def test_generation_stage_optimization(self, pipeline):
        """Test generation stage applies response formatting optimization."""
        # RED: Test generation stage produces token-efficient responses
        context = PipelineContext(
            generated_response="Very long detailed response with lots of repetitive agricultural implementation details...",
            optimization_target=0.25,  # 25% reduction target
        )

        optimized_response = pipeline.optimize_generation_stage(context)

        assert optimized_response.tokens_saved > 0
        assert optimized_response.compression_applied is True
        assert optimized_response.educational_value_preserved is True

    @pytest.mark.parametrize(
        "target_format, expected_output, description",
        [
            (
                TargetFormat.BRIEF,
                "This is the first sentence.",
                "Brief format should extract only the first sentence of the first paragraph.",
            ),
            (
                TargetFormat.BULLET_POINTS,
                "- First item\n- Second item",
                "Bullet points format should extract only list items.",
            ),
            (
                TargetFormat.STANDARD,
                "# Main Title\n\nThis is the first sentence. This is the second sentence.\n\n- First item\n- Second item\n\n## Safety Section\n\nCritical safety info.",
                "Standard format should return the cleaned, full markdown.",
            ),
        ],
    )
    def test_decoding_stage_format_aware_parsing(
        self, pipeline, target_format, expected_output, description
    ):
        """Test format-aware structural parsing for various target formats."""
        context = PipelineContext(
            raw_output="# Main Title\n\nThis is the first sentence. This is the second sentence.\n\n- First item\n- Second item\n\n## Safety Section\n\nCritical safety info.",
            target_format=target_format,
        )

        optimized_output = pipeline.optimize_decoding_stage(context)

        assert optimized_output.final_output == expected_output, description
        assert optimized_output.format_optimized is True

    def test_decoding_stage_brief_preserves_safety_section(self, pipeline):
        """Verify 'brief' format always includes sections with 'safety' in the title."""
        raw_output = (
            "# Overview\n\nSome general info.\n\n"
            "## Agricultural Safety Compliance\n\nThis is a critical safety warning that must always be preserved.\n\n"
            "### Other Details\n\nMore info."
        )
        context = PipelineContext(raw_output=raw_output, target_format=TargetFormat.BRIEF)

        optimized_output = pipeline.optimize_decoding_stage(context)

        expected = "Some general info.\n\n## Agricultural Safety Compliance\n\nThis is a critical safety warning that must always be preserved."
        assert optimized_output.final_output == expected

    def test_decoding_stage_bullet_points_fallback(self, pipeline):
        """Verify 'bullet_points' format creates bullets from paragraphs if no list exists."""
        raw_output = "# Title\n\nFirst sentence. Second sentence."
        context = PipelineContext(raw_output=raw_output, target_format=TargetFormat.BULLET_POINTS)

        optimized_output = pipeline.optimize_decoding_stage(context)

        assert optimized_output.final_output == "- First sentence.\n- Second sentence."

    @pytest.mark.asyncio
    async def test_integrated_pipeline_execution(self, pipeline):
        """Test full pipeline integration across all four stages."""
        # RED: Test complete pipeline processes input through all optimization stages
        user_input = (
            "I need help implementing agricultural equipment safety monitoring with ISO compliance"
        )

        result = await pipeline.process_complete_pipeline(
            user_input=user_input, optimization_level=OptimizationLevel.AGGRESSIVE
        )

        assert result.total_tokens_saved > 0
        assert result.stages_completed == 4
        assert result.agricultural_compliance_maintained is True
        assert result.optimization_level == OptimizationLevel.AGGRESSIVE

    def test_adaptive_optimization_detection(self, pipeline):
        """Test pipeline adapts optimization level based on context."""
        # RED: Test adaptive mode adjusts optimization based on agricultural keywords
        safety_critical_input = "Emergency stop procedure for tractor collision detection"
        routine_input = "Show current git status"

        safety_result = pipeline.detect_optimization_level(safety_critical_input)
        routine_result = pipeline.detect_optimization_level(routine_input)

        assert safety_result == OptimizationLevel.CONSERVATIVE  # Preserve safety content
        assert routine_result == OptimizationLevel.AGGRESSIVE  # Maximum optimization

    @pytest.mark.asyncio
    async def test_agricultural_context_preservation(self, pipeline):
        """Test pipeline preserves critical agricultural and safety content."""
        # RED: Test agricultural and safety keywords are never optimized away
        context = PipelineContext(
            user_input="ISO 11783 tractor safety emergency protocols",
            optimization_target=0.8,  # High optimization that should preserve safety content
        )

        result = await pipeline.process_complete_pipeline(
            user_input=context.user_input, optimization_level=OptimizationLevel.AGGRESSIVE
        )

        output_lower = result.final_output.lower()
        assert "iso" in output_lower or "safety" in output_lower or "emergency" in output_lower
        assert result.agricultural_compliance_maintained is True

    @pytest.mark.asyncio
    async def test_token_budget_management(self, pipeline):
        """Test pipeline respects token budget constraints."""
        # RED: Test pipeline stays within specified token budgets
        token_budget = 1000  # Maximum tokens allowed

        result = await pipeline.process_with_budget(
            user_input="Complete agricultural robotics implementation guide",
            token_budget=token_budget,
        )

        assert result.estimated_tokens <= token_budget
        assert result.budget_exceeded is False
        assert result.optimization_applied is True

    @pytest.mark.asyncio
    async def test_cross_stage_coordination(self, pipeline):
        """Test stages coordinate optimization strategies effectively."""
        # RED: Test stages share optimization state and cumulative savings
        context = PipelineContext(user_input="Test coordination")

        # Mock stage processors to verify coordination
        with patch.object(pipeline, "_track_cumulative_optimization") as mock_track:
            await pipeline.process_complete_pipeline(
                user_input=context.user_input, optimization_level=OptimizationLevel.STANDARD
            )

            # Verify coordination tracking was called for each stage
            assert mock_track.call_count == 4  # One for each processing stage

    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, pipeline):
        """Test pipeline handles optimization failures gracefully."""
        # RED: Test pipeline falls back to standard processing on optimization errors
        with patch.object(pipeline, "optimize_pre_fill_stage") as mock_optimize:
            mock_optimize.side_effect = Exception("Optimization failed")

            result = await pipeline.process_complete_pipeline(
                user_input="Test input", optimization_level=OptimizationLevel.STANDARD
            )

            assert result.fallback_used is True
            assert result.final_output is not None  # Still produces output

    @pytest.mark.asyncio
    async def test_optimization_metrics_tracking(self, pipeline):
        """Test pipeline tracks comprehensive optimization metrics."""
        # RED: Test pipeline collects detailed performance metrics
        result = await pipeline.process_complete_pipeline(
            user_input="Agricultural robotics implementation",
            optimization_level=OptimizationLevel.STANDARD,
        )

        assert hasattr(result, "metrics")
        assert "total_tokens_saved" in result.metrics
        assert "processing_time_ms" in result.metrics
        assert "optimization_ratio" in result.metrics
        assert "stage_breakdown" in result.metrics


class TestPipelineContext:
    """Test pipeline context data structure."""

    def test_context_initialization(self):
        """Test pipeline context initializes with proper defaults."""
        context = PipelineContext(user_input="Test input")

        assert context.user_input == "Test input"
        assert context.optimization_target == 0.3  # Default 30% reduction
        assert context.agricultural_safety_preserved is True

    def test_context_agricultural_keyword_detection(self):
        """Test context detects agricultural keywords for preservation."""
        agricultural_context = PipelineContext(user_input="ISO 11783 tractor safety implementation")

        detected_keywords = agricultural_context.detect_agricultural_keywords()

        assert "iso" in detected_keywords
        assert "tractor" in detected_keywords
        assert "safety" in detected_keywords


class TestOptimizationLevels:
    """Test optimization level behavior."""

    def test_optimization_level_values(self):
        """Test optimization levels have correct reduction targets."""
        assert OptimizationLevel.CONSERVATIVE.reduction_target == 0.15  # 15%
        assert OptimizationLevel.STANDARD.reduction_target == 0.30  # 30%
        assert OptimizationLevel.AGGRESSIVE.reduction_target == 0.50  # 50%
        assert OptimizationLevel.ADAPTIVE.reduction_target == 0.30  # Default to standard
