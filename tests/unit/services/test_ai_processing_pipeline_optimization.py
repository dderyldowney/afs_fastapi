
import unittest
from pathlib import Path
from unittest.mock import patch

from afs_fastapi.services.ai_processing_pipeline import AIProcessingPipeline, PipelineContext


class TestAIProcessingPipelineOptimization(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.pipeline = AIProcessingPipeline(project_root=self.project_root)

    def test_efficient_data_serialization(self):
        # This test is a placeholder for now, as we are not changing the serialization format.
        pass

    def test_selective_feature_extraction(self):
        user_input = "tell me about tractor safety"
        context = self.pipeline.optimize_pre_fill_stage(PipelineContext(user_input=user_input))
        self.assertIn("AFS FastAPI: Production-ready agricultural robotics platform.", context.essential_content)
        self.assertIn("ISO 18497: Agricultural machinery safety standards", context.essential_content)
        self.assertNotIn("ISOBUS communication", context.essential_content)

    def test_intelligent_caching(self):
        user_input = "what is the status of the tractor?"
        with patch.object(
            self.pipeline, "optimize_pre_fill_stage"
        ) as mock_optimize_pre_fill_stage:
            # First call, should call the pipeline
            result1 = self.pipeline.process_complete_pipeline(user_input)
            self.assertEqual(mock_optimize_pre_fill_stage.call_count, 1)

            # Second call, should not call the pipeline again
            result2 = self.pipeline.process_complete_pipeline(user_input)
            self.assertEqual(mock_optimize_pre_fill_stage.call_count, 1)

            # Check that the results are the same
            self.assertEqual(result1.final_output, result2.final_output)


if __name__ == "__main__":
    unittest.main()
