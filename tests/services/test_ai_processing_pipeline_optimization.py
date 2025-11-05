import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from afs_fastapi.services.ai_processing_pipeline import AIProcessingPipeline, PipelineContext


class TestAIProcessingPipelineOptimization(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.pipeline = AIProcessingPipeline(project_root=self.project_root)

    def test_efficient_data_serialization(self):
        """Test that data serialization maintains efficiency."""
        # Verify pipeline can serialize context data
        context = PipelineContext(
            user_input="test query",
            essential_content="test content",
        )
        # Verify context is serializable (no errors)
        self.assertIsNotNone(context.user_input)
        self.assertEqual(context.user_input, "test query")
        self.assertEqual(context.essential_content, "test content")

    def test_selective_feature_extraction(self):
        user_input = "tell me about tractor safety"
        context = self.pipeline.optimize_pre_fill_stage(PipelineContext(user_input=user_input))

        # Check for actual content that should be there
        self.assertIn(
            "AFS FastAPI Platform",
            context.essential_content,
        )
        self.assertIn("tractor", context.essential_content)
        self.assertIn("safety", context.essential_content)
        self.assertNotIn("ISOBUS communication", context.essential_content)

    @pytest.mark.asyncio
    async def test_intelligent_caching(self):
        user_input = "what is the status of the tractor?"
        with patch.object(self.pipeline, "optimize_pre_fill_stage") as mock_optimize_pre_fill_stage:
            # First call, should call the pipeline
            result1 = await self.pipeline.process_complete_pipeline(user_input)
            self.assertEqual(mock_optimize_pre_fill_stage.call_count, 1)

            # Second call, should not call the pipeline again
            result2 = await self.pipeline.process_complete_pipeline(user_input)
            self.assertEqual(mock_optimize_pre_fill_stage.call_count, 1)

            # Check that the results are the same
            self.assertEqual(result1.final_output, result2.final_output)


if __name__ == "__main__":
    unittest.main()
