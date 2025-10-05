"""AFS FastAPI Services Module.

Business logic and coordination services for agricultural robotics platform.
This module contains distributed systems components for multi-tractor
fleet coordination, synchronization, and AI processing pipeline optimization.
"""

from .agricultural_ai_integration import AgriculturalAIIntegration, agricultural_ai
from .ai_processing_manager import AIProcessingManager, ai_processing_manager
from .ai_processing_pipeline import (
    AIProcessingPipeline,
    OptimizationLevel,
    PipelineContext,
    PipelineResult,
    ProcessingStage,
)
from .synchronization import VectorClock

__all__ = [
    "VectorClock",
    "AIProcessingPipeline",
    "AIProcessingManager",
    "ai_processing_manager",
    "AgriculturalAIIntegration",
    "agricultural_ai",
    "ProcessingStage",
    "OptimizationLevel",
    "PipelineContext",
    "PipelineResult",
]
