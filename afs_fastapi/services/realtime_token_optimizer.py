#!/usr/bin/env python3
"""
Real-time Token Optimization System for AFS FastAPI.

Provides live conversation optimization, token monitoring, and dynamic
adjustment of AI interactions for maximum efficiency while preserving
agricultural safety compliance.
"""

from __future__ import annotations

import json
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .ai_processing_pipeline import AIProcessingPipeline, OptimizationLevel


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation with optimization metadata."""

    timestamp: datetime
    user_input: str
    ai_response: str
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    optimization_level: OptimizationLevel
    agricultural_keywords: list[str] = field(default_factory=list)
    safety_critical: bool = False

    @property
    def reduction_percentage(self) -> float:
        """Calculate token reduction percentage for this turn."""
        if self.original_tokens == 0:
            return 0.0
        return (self.tokens_saved / self.original_tokens) * 100


@dataclass
class ConversationMetrics:
    """Real-time conversation optimization metrics."""

    total_turns: int = 0
    total_tokens_saved: int = 0
    total_original_tokens: int = 0
    average_reduction: float = 0.0
    agricultural_turns: int = 0
    safety_critical_turns: int = 0
    optimization_failures: int = 0

    def update_from_turn(self, turn: ConversationTurn) -> None:
        """Update metrics from a conversation turn."""
        self.total_turns += 1
        self.total_tokens_saved += turn.tokens_saved
        self.total_original_tokens += turn.original_tokens

        if turn.agricultural_keywords:
            self.agricultural_turns += 1
        if turn.safety_critical:
            self.safety_critical_turns += 1

        # Recalculate average
        if self.total_original_tokens > 0:
            self.average_reduction = (self.total_tokens_saved / self.total_original_tokens) * 100


class RealTimeTokenOptimizer:
    """
    Real-time token optimization system for live conversations.

    Monitors ongoing AI conversations, applies dynamic optimization,
    and maintains conversation context while maximizing token efficiency.
    """

    def __init__(self, project_root: Path | None = None, max_history: int = 50) -> None:
        """Initialize real-time token optimizer."""
        self.project_root = project_root or Path.cwd()
        self.max_history = max_history

        # Initialize core pipeline
        self.pipeline = AIProcessingPipeline(project_root)

        # Conversation management
        self.conversation_history: deque[ConversationTurn] = deque(maxlen=max_history)
        self.current_session_id = self._generate_session_id()
        self.session_start = datetime.now()

        # Real-time metrics
        self.metrics = ConversationMetrics()
        self.optimization_callbacks: list[Callable[[ConversationTurn], None]] = []

        # Dynamic optimization settings
        self.adaptive_mode = True
        self.token_budget_per_turn = 2000  # Maximum tokens per conversation turn
        self.emergency_optimization_threshold = 0.8  # Trigger aggressive optimization at 80% budget

        # Context compression settings
        self.context_window_size = 10  # Number of recent turns to maintain
        self.context_compression_ratio = 0.3  # Compress older context to 30%

        # Agricultural safety monitoring
        self.safety_keywords = {
            "emergency",
            "stop",
            "critical",
            "danger",
            "fault",
            "collision",
            "brake",
            "shutdown",
            "abort",
            "malfunction",
            "alert",
        }
        self.agricultural_keywords = {
            "iso",
            "11783",
            "18497",
            "tractor",
            "equipment",
            "field",
            "agricultural",
            "farming",
            "harvest",
            "cultivation",
            "isobus",
        }

    def _generate_session_id(self) -> str:
        """Generate unique session identifier."""
        return f"session_{int(time.time())}"

    def optimize_conversation_turn(
        self,
        user_input: str,
        ai_response: str = "",
        force_optimization_level: OptimizationLevel | None = None,
    ) -> ConversationTurn:
        """
        Optimize a single conversation turn in real-time.

        Args:
            user_input: User's input message
            ai_response: AI's response (if available)
            force_optimization_level: Override automatic optimization level detection

        Returns:
            ConversationTurn with optimization results
        """
        timestamp = datetime.now()

        # Detect agricultural and safety keywords
        input_text = f"{user_input} {ai_response}".lower()
        agricultural_keywords = [kw for kw in self.agricultural_keywords if kw in input_text]
        safety_critical = any(kw in input_text for kw in self.safety_keywords)

        # Determine optimization level
        if force_optimization_level:
            optimization_level = force_optimization_level
        elif safety_critical:
            optimization_level = OptimizationLevel.CONSERVATIVE
        elif agricultural_keywords:
            optimization_level = OptimizationLevel.STANDARD
        else:
            optimization_level = self._adaptive_optimization_level()

        # Apply conversation context optimization
        contextualized_input = self._apply_context_optimization(user_input)

        # Process through pipeline with budget enforcement
        try:
            if ai_response:
                # Optimize existing response
                original_tokens = self._estimate_tokens(user_input + ai_response)

                # Apply budget-aware optimization
                if original_tokens > self.token_budget_per_turn:
                    # Force aggressive optimization when over budget
                    optimization_level = OptimizationLevel.AGGRESSIVE

                # Note: pipeline.process_complete_pipeline is async and cannot be called
                # from this synchronous context. Skipping async pipeline optimization.
                optimized_response = ai_response

                # Enforce budget constraints by truncating if necessary
                combined_optimized = contextualized_input + " " + optimized_response
                optimized_tokens = self._estimate_tokens(combined_optimized)

                # If still over budget, apply emergency compression
                if optimized_tokens > self.token_budget_per_turn:
                    # Truncate response to fit budget
                    budget_ratio = self.token_budget_per_turn / optimized_tokens
                    target_length = int(
                        len(optimized_response) * budget_ratio * 0.8
                    )  # 80% of budget for safety
                    optimized_response = optimized_response[:target_length] + "..."
                    optimized_tokens = self._estimate_tokens(
                        contextualized_input + optimized_response
                    )

            else:
                # Optimize input only
                original_tokens = self._estimate_tokens(user_input)

                # Apply budget enforcement to input
                if original_tokens > self.token_budget_per_turn:
                    # Truncate input if too long
                    budget_ratio = self.token_budget_per_turn / original_tokens
                    target_length = int(len(contextualized_input) * budget_ratio * 0.9)
                    contextualized_input = contextualized_input[:target_length] + "..."

                # Note: pipeline.process_complete_pipeline is async and cannot be called
                # from this synchronous context. Skipping async pipeline optimization.
                optimized_response = ""
                optimized_tokens = self._estimate_tokens(contextualized_input)

            tokens_saved = max(0, original_tokens - optimized_tokens)

        except Exception:
            # Fallback on optimization failure
            self.metrics.optimization_failures += 1
            try:
                original_tokens = self._estimate_tokens(user_input + ai_response)
            except Exception:
                # If token estimation fails, use approximate estimate based on character count
                original_tokens = (
                    len(user_input + ai_response) // 4
                )  # Rough estimate: ~4 chars per token
            optimized_tokens = original_tokens
            tokens_saved = 0
            optimized_response = ai_response

        # Create conversation turn
        turn = ConversationTurn(
            timestamp=timestamp,
            user_input=contextualized_input,
            ai_response=optimized_response,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=tokens_saved,
            optimization_level=optimization_level,
            agricultural_keywords=agricultural_keywords,
            safety_critical=safety_critical,
        )

        # Update conversation history and metrics
        self.conversation_history.append(turn)
        self.metrics.update_from_turn(turn)

        # Trigger callbacks
        for callback in self.optimization_callbacks:
            try:
                callback(turn)
            except Exception:
                pass  # Don't let callback failures break optimization

        return turn

    def _apply_context_optimization(self, user_input: str) -> str:
        """Apply conversation context optimization to reduce redundancy."""
        if len(self.conversation_history) == 0:
            return user_input

        # Get recent context
        recent_turns = list(self.conversation_history)[-self.context_window_size :]

        # Build context summary for redundancy detection
        recent_topics = set()
        for turn in recent_turns:
            # Extract key topics from previous inputs
            words = re.findall(r"\b\w+\b", turn.user_input.lower())
            significant_words = [
                w
                for w in words
                if len(w) > 3
                and w
                not in {
                    "the",
                    "and",
                    "for",
                    "are",
                    "but",
                    "not",
                    "you",
                    "all",
                    "can",
                    "had",
                    "her",
                    "was",
                    "one",
                    "our",
                    "out",
                    "day",
                    "get",
                    "has",
                    "him",
                    "his",
                    "how",
                    "its",
                    "new",
                    "now",
                    "old",
                    "see",
                    "two",
                    "who",
                    "boy",
                    "did",
                    "does",
                    "help",
                    "need",
                    "want",
                    "please",
                    "could",
                    "would",
                    "should",
                }
            ]
            recent_topics.update(significant_words)

        # Remove redundant references if context is available
        optimized_input = user_input
        current_words = user_input.lower().split()

        # Remove phrases that reference previous context redundantly
        redundant_phrases = [
            r"\bas\s+mentioned\s+before\b",
            r"\blike\s+we\s+discussed\b",
            r"\bin\s+the\s+previous\s+conversation\b",
            r"\bcontinuing\s+from\s+earlier\b",
        ]

        for pattern in redundant_phrases:
            optimized_input = re.sub(pattern, "", optimized_input, flags=re.IGNORECASE)

        # Compress repetitive topic references
        if len(recent_topics) > 5:
            # If many topics have been discussed, assume context and compress
            for topic in recent_topics:
                if topic in current_words and len(topic) > 4:
                    # Replace with shorter reference if not agricultural/safety term
                    if (
                        topic not in self.agricultural_keywords
                        and topic not in self.safety_keywords
                    ):
                        pattern = r"\b" + re.escape(topic) + r"\b"
                        if optimized_input.lower().count(topic) > 1:
                            # Replace second and subsequent occurrences
                            optimized_input = re.sub(
                                pattern, "it", optimized_input, count=1, flags=re.IGNORECASE
                            )

        # Clean up extra whitespace
        optimized_input = re.sub(r"\s+", " ", optimized_input).strip()

        # Ensure we have some content
        return optimized_input if optimized_input else user_input

    def detect_optimization_level(self, user_input: str) -> OptimizationLevel:
        """
        Detect appropriate optimization level based on input content analysis.

        Safety-critical and agricultural content gets conservative optimization,
        routine operations get aggressive optimization.
        """
        input_lower = user_input.lower()

        # Safety-critical keywords require conservative optimization
        safety_keywords = ["emergency", "safety", "critical", "stop", "collision", "fault"]
        if any(keyword in input_lower for keyword in safety_keywords):
            return OptimizationLevel.CONSERVATIVE

        # Agricultural technical keywords require standard optimization
        agricultural_keywords = ["iso", "11783", "18497", "tractor", "equipment"]
        if any(keyword in input_lower for keyword in agricultural_keywords):
            return OptimizationLevel.STANDARD

        # Routine operations can use aggressive optimization
        routine_keywords = ["status", "git", "list", "show", "display"]
        if any(keyword in input_lower for keyword in routine_keywords):
            return OptimizationLevel.AGGRESSIVE

        # Default to standard optimization
        return OptimizationLevel.STANDARD

    def _adaptive_optimization_level(self) -> OptimizationLevel:
        """Determine optimization level based on conversation state and budget pressure."""
        if not self.adaptive_mode:
            return OptimizationLevel.STANDARD

        # Calculate current token usage rate
        if len(self.conversation_history) == 0:
            return OptimizationLevel.STANDARD

        recent_turns = list(self.conversation_history)[-5:]  # Last 5 turns
        avg_tokens_per_turn = sum(turn.optimized_tokens for turn in recent_turns) / len(
            recent_turns
        )

        # Check budget pressure
        budget_pressure = avg_tokens_per_turn / self.token_budget_per_turn

        if budget_pressure > self.emergency_optimization_threshold:
            return OptimizationLevel.AGGRESSIVE
        elif budget_pressure > 0.6:
            return OptimizationLevel.STANDARD
        else:
            return OptimizationLevel.CONSERVATIVE

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        return max(1, len(text) // 4)

    def get_conversation_summary(self) -> dict[str, Any]:
        """Get comprehensive conversation optimization summary."""
        session_duration = datetime.now() - self.session_start

        # Calculate recent performance (last 10 turns)
        recent_turns = list(self.conversation_history)[-10:]
        recent_savings = sum(turn.tokens_saved for turn in recent_turns)
        recent_original = sum(turn.original_tokens for turn in recent_turns)
        recent_reduction = (recent_savings / recent_original * 100) if recent_original > 0 else 0.0

        # Identify optimization patterns
        optimization_levels = [turn.optimization_level.value for turn in self.conversation_history]
        level_counts = {
            level: optimization_levels.count(level) for level in set(optimization_levels)
        }

        return {
            "session_id": self.current_session_id,
            "session_duration_minutes": session_duration.total_seconds() / 60,
            "total_metrics": {
                "turns": self.metrics.total_turns,
                "tokens_saved": self.metrics.total_tokens_saved,
                "original_tokens": self.metrics.total_original_tokens,
                "average_reduction_percent": self.metrics.average_reduction,
                "agricultural_turns": self.metrics.agricultural_turns,
                "safety_critical_turns": self.metrics.safety_critical_turns,
                "optimization_failures": self.metrics.optimization_failures,
            },
            "recent_performance": {
                "turns": len(recent_turns),
                "tokens_saved": recent_savings,
                "reduction_percent": recent_reduction,
            },
            "optimization_patterns": {
                "level_distribution": level_counts,
                "adaptive_mode": self.adaptive_mode,
                "current_budget_per_turn": self.token_budget_per_turn,
            },
            "conversation_health": {
                "context_window_size": len(self.conversation_history),
                "agricultural_focus_percent": (
                    self.metrics.agricultural_turns / max(1, self.metrics.total_turns)
                )
                * 100,
                "safety_awareness_percent": (
                    self.metrics.safety_critical_turns / max(1, self.metrics.total_turns)
                )
                * 100,
            },
        }

    def optimize_conversation_history(self) -> tuple[str, int]:
        """
        Optimize entire conversation history for context compression.

        Returns:
            Tuple of (compressed_history, tokens_saved)
        """
        if len(self.conversation_history) == 0:
            return "", 0

        # Separate recent vs older history
        cutoff = max(1, len(self.conversation_history) - self.context_window_size)
        recent_history = list(self.conversation_history)[cutoff:]
        older_history = list(self.conversation_history)[:cutoff]

        # Preserve recent history fully
        recent_text = []
        for turn in recent_history:
            recent_text.append(f"User: {turn.user_input}")
            if turn.ai_response:
                recent_text.append(f"AI: {turn.ai_response}")

        recent_history_text = "\n".join(recent_text)

        # Compress older history
        if older_history:
            # Create summary of older conversation
            older_topics = set()
            agricultural_mentioned = False
            safety_mentioned = False

            for turn in older_history:
                if turn.agricultural_keywords:
                    agricultural_mentioned = True
                if turn.safety_critical:
                    safety_mentioned = True

                # Extract key topics
                words = re.findall(r"\b\w+\b", turn.user_input.lower())
                significant_words = [w for w in words if len(w) > 4][:3]  # Top 3 per turn
                older_topics.update(significant_words)

            # Build compressed summary
            summary_parts = ["[Previous conversation covered:"]
            if agricultural_mentioned:
                summary_parts.append("agricultural equipment")
            if safety_mentioned:
                summary_parts.append("safety protocols")

            # Add key topics (limit to avoid bloat)
            key_topics = list(older_topics)[:5]
            if key_topics:
                summary_parts.append(f"topics: {', '.join(key_topics)}")

            summary_parts.append("]")
            older_summary = " ".join(summary_parts)
        else:
            older_summary = ""

        # Combine compressed older + full recent
        if older_summary:
            compressed_history = f"{older_summary}\n\n{recent_history_text}"
        else:
            compressed_history = recent_history_text

        # Calculate savings
        original_total_tokens = sum(
            self._estimate_tokens(f"{t.user_input} {t.ai_response}")
            for t in self.conversation_history
        )
        compressed_tokens = self._estimate_tokens(compressed_history)
        tokens_saved = max(0, original_total_tokens - compressed_tokens)

        return compressed_history, tokens_saved

    def register_optimization_callback(self, callback: Callable[[ConversationTurn], None]) -> None:
        """Register callback to be called after each optimization."""
        self.optimization_callbacks.append(callback)

    def set_token_budget(self, budget: int) -> None:
        """Set token budget per conversation turn."""
        self.token_budget_per_turn = max(100, budget)  # Minimum reasonable budget

    def enable_adaptive_mode(self, enabled: bool = True) -> None:
        """Enable or disable adaptive optimization mode."""
        self.adaptive_mode = enabled

    def reset_session(self) -> dict[str, Any]:
        """Reset current session and return final metrics."""
        final_summary = self.get_conversation_summary()

        # Reset state
        self.conversation_history.clear()
        self.current_session_id = self._generate_session_id()
        self.session_start = datetime.now()
        self.metrics = ConversationMetrics()

        return final_summary

    def export_session_data(self, output_path: Path | None = None) -> Path:
        """Export session data for analysis."""
        if output_path is None:
            output_path = (
                self.project_root
                / ".claude"
                / "optimization_sessions"
                / f"{self.current_session_id}.json"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare export data
        export_data = {
            "session_summary": self.get_conversation_summary(),
            "conversation_turns": [
                {
                    "timestamp": turn.timestamp.isoformat(),
                    "user_input": turn.user_input,
                    "ai_response": turn.ai_response,
                    "original_tokens": turn.original_tokens,
                    "optimized_tokens": turn.optimized_tokens,
                    "tokens_saved": turn.tokens_saved,
                    "optimization_level": turn.optimization_level.value,
                    "agricultural_keywords": turn.agricultural_keywords,
                    "safety_critical": turn.safety_critical,
                    "reduction_percentage": turn.reduction_percentage,
                }
                for turn in self.conversation_history
            ],
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return output_path


class ConversationOptimizationMiddleware:
    """
    Middleware component for integrating real-time optimization into conversation flows.

    Provides seamless integration with existing conversation systems while
    maintaining agricultural safety compliance and optimization transparency.
    """

    def __init__(self, optimizer: RealTimeTokenOptimizer) -> None:
        """Initialize middleware with optimizer instance."""
        self.optimizer = optimizer
        self.optimization_enabled = True
        self.debug_mode = False

    def process_user_input(self, user_input: str) -> tuple[str, dict[str, Any]]:
        """
        Process user input with optimization.

        Returns:
            Tuple of (optimized_input, optimization_metadata)
        """
        if not self.optimization_enabled:
            return user_input, {"optimization_applied": False}

        # Apply input-specific optimization
        turn = self.optimizer.optimize_conversation_turn(user_input=user_input)

        optimization_metadata: dict[str, Any] = {
            "optimization_applied": True,
            "original_tokens": turn.original_tokens,
            "optimized_tokens": turn.optimized_tokens,
            "tokens_saved": turn.tokens_saved,
            "optimization_level": turn.optimization_level.value,
            "agricultural_keywords": turn.agricultural_keywords,
            "safety_critical": turn.safety_critical,
            "reduction_percentage": turn.reduction_percentage,
        }

        if self.debug_mode:
            optimization_metadata["debug_info"] = {
                "original_input": user_input,
                "conversation_history_size": len(self.optimizer.conversation_history),
                "session_metrics": self.optimizer.get_conversation_summary(),
            }

        return turn.user_input, optimization_metadata

    def process_ai_response(
        self, ai_response: str, user_input: str = ""
    ) -> tuple[str, dict[str, Any]]:
        """
        Process AI response with optimization.

        Returns:
            Tuple of (optimized_response, optimization_metadata)
        """
        if not self.optimization_enabled:
            return ai_response, {"optimization_applied": False}

        # Apply response optimization
        turn = self.optimizer.optimize_conversation_turn(
            user_input=user_input, ai_response=ai_response
        )

        optimization_metadata: dict[str, Any] = {
            "optimization_applied": True,
            "original_tokens": turn.original_tokens,
            "optimized_tokens": turn.optimized_tokens,
            "tokens_saved": turn.tokens_saved,
            "optimization_level": turn.optimization_level.value,
            "agricultural_keywords": turn.agricultural_keywords,
            "safety_critical": turn.safety_critical,
            "reduction_percentage": turn.reduction_percentage,
        }

        return turn.ai_response, optimization_metadata

    def get_optimization_status(self) -> dict[str, Any]:
        """Get current optimization status and metrics."""
        return {
            "enabled": self.optimization_enabled,
            "debug_mode": self.debug_mode,
            "session_summary": self.optimizer.get_conversation_summary(),
            "recent_performance": self._get_recent_performance(),
        }

    def _get_recent_performance(self) -> dict[str, Any]:
        """Get recent optimization performance metrics."""
        recent_turns = list(self.optimizer.conversation_history)[-5:]
        if not recent_turns:
            return {"turns": 0, "average_reduction": 0.0}

        total_reduction = sum(turn.reduction_percentage for turn in recent_turns)
        return {
            "turns": len(recent_turns),
            "average_reduction": total_reduction / len(recent_turns),
            "total_tokens_saved": sum(turn.tokens_saved for turn in recent_turns),
        }

    def enable_optimization(self, enabled: bool = True) -> None:
        """Enable or disable optimization processing."""
        self.optimization_enabled = enabled

    def enable_debug_mode(self, enabled: bool = True) -> None:
        """Enable or disable debug mode for detailed optimization info."""
        self.debug_mode = enabled
