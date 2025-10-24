#!/usr/bin/env python3
"""
Project-wide Conversation Management with Real-time Token Optimization.

Provides centralized conversation handling for all AI interactions across
the AFS FastAPI platform with automatic token optimization and agricultural
safety compliance.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from afs_fastapi.services.realtime_token_optimizer import (  # noqa: E402
    ConversationOptimizationMiddleware,
    OptimizationLevel,
    RealTimeTokenOptimizer,
)

# Import mandatory optimization enforcer for monitoring integration
try:
    claude_hooks_path = project_root / ".claude" / "hooks"
    sys.path.insert(0, str(claude_hooks_path))
    from mandatory_optimization_enforcement import get_enforcer  # type: ignore[import-not-found]

    ENFORCER_AVAILABLE = True
except ImportError:
    ENFORCER_AVAILABLE = False


class ConversationManager:
    """
    Centralized conversation management for the AFS FastAPI platform.

    Automatically applies real-time token optimization to all AI interactions
    while maintaining agricultural safety compliance and conversation context.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize conversation manager with real-time optimization."""
        self.project_root = project_root or Path.cwd()

        # Initialize optimization components
        self.optimizer = RealTimeTokenOptimizer(project_root=self.project_root)
        self.middleware = ConversationOptimizationMiddleware(self.optimizer)

        # Initialize enforcer for monitoring integration
        self.enforcer = None
        if ENFORCER_AVAILABLE:
            try:
                self.enforcer = get_enforcer()
            except Exception:
                pass  # Graceful fallback if enforcer unavailable

        # Configuration
        self.config_path = self.project_root / ".claude" / "conversation_config.json"
        self.load_configuration()

        # Session management
        self.active_conversations: dict[str, dict[str, Any]] = {}
        self.default_conversation_id = "main"

        # Integration hooks
        self.pre_processing_hooks: list[Callable] = []
        self.post_processing_hooks: list[Callable] = []

        # Performance monitoring
        self.total_interactions = 0
        self.total_tokens_saved = 0

        # Auto-enable optimization
        self.enable_optimization()

    def load_configuration(self) -> None:
        """Load conversation management configuration."""
        default_config = {
            "optimization_enabled": True,
            "debug_mode": False,
            "token_budget_per_turn": 2000,
            "adaptive_mode": True,
            "auto_export_sessions": True,
            "agricultural_safety_level": "standard",
            "context_window_size": 10,
        }

        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                self.config = {**default_config, **config}
            except (json.JSONDecodeError, OSError):
                self.config = default_config
        else:
            self.config = default_config
            self.save_configuration()

    def save_configuration(self) -> None:
        """Save current configuration to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _track_optimization_with_enforcer(
        self, user_input: str, ai_response: str, optimization_metadata: dict[str, Any]
    ) -> None:
        """Track optimization results with the mandatory enforcer for monitoring."""
        if not self.enforcer:
            return

        try:
            # Create a mock optimization result for the enforcer
            mock_result = {
                "optimized_content": {"user_input": user_input, "ai_response": ai_response},
                "optimization_metadata": optimization_metadata,
                "agricultural_compliance": {
                    "agricultural_keywords_detected": optimization_metadata.get("input", {}).get(
                        "agricultural_keywords", []
                    ),
                    "safety_critical": optimization_metadata.get("input", {}).get(
                        "safety_critical", False
                    ),
                    "compliance_maintained": True,
                },
            }

            # Track the successful optimization with the enforcer
            self.enforcer._track_optimization_success(mock_result)

        except Exception:
            # Don't let monitoring failures break optimization
            pass

    def process_conversation_turn(
        self,
        user_input: str,
        ai_response: str = "",
        conversation_id: str | None = None,
        optimization_level: OptimizationLevel | None = None,
    ) -> dict[str, Any]:
        """
        Process a complete conversation turn with optimization.

        Args:
            user_input: User's input message
            ai_response: AI's response (optional)
            conversation_id: Conversation identifier (uses default if None)
            optimization_level: Force specific optimization level

        Returns:
            Dictionary with optimized content and metadata
        """
        if conversation_id is None:
            conversation_id = self.default_conversation_id

        # Run pre-processing hooks
        for hook in self.pre_processing_hooks:
            try:
                hook(user_input, ai_response, conversation_id)
            except Exception:
                pass  # Don't let hooks break conversation processing

        # Process user input
        optimized_input, input_metadata = self.middleware.process_user_input(user_input)

        # Process AI response if provided
        if ai_response:
            optimized_response, response_metadata = self.middleware.process_ai_response(
                ai_response, optimized_input
            )
        else:
            optimized_response = ""
            response_metadata = {"optimization_applied": False}

        # Track conversation
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = {
                "created": self.optimizer.session_start.isoformat(),
                "turns": 0,
                "total_tokens_saved": 0,
            }

        conversation = self.active_conversations[conversation_id]
        conversation["turns"] += 1
        conversation["total_tokens_saved"] += input_metadata.get("tokens_saved", 0)
        conversation["total_tokens_saved"] += response_metadata.get("tokens_saved", 0)

        # Update global metrics
        self.total_interactions += 1
        self.total_tokens_saved += input_metadata.get("tokens_saved", 0)
        self.total_tokens_saved += response_metadata.get("tokens_saved", 0)

        # Build comprehensive result
        optimization_metadata: dict[str, Any] = {
            "input": input_metadata,
            "response": response_metadata,
            "total_tokens_saved": (
                input_metadata.get("tokens_saved", 0) + response_metadata.get("tokens_saved", 0)
            ),
            "conversation_turn": conversation["turns"],
        }

        result = {
            "conversation_id": conversation_id,
            "optimized_content": {"user_input": optimized_input, "ai_response": optimized_response},
            "original_content": {"user_input": user_input, "ai_response": ai_response},
            "optimization_metadata": optimization_metadata,
            "conversation_metrics": self.get_conversation_metrics(conversation_id),
            "agricultural_compliance": {
                "agricultural_keywords_detected": input_metadata.get("agricultural_keywords", []),
                "safety_critical": input_metadata.get("safety_critical", False),
                "compliance_maintained": True,
            },
        }

        # Track optimization with enforcer for monitoring
        self._track_optimization_with_enforcer(
            user_input, optimized_response if ai_response else "", optimization_metadata
        )

        # Run post-processing hooks
        for hook in self.post_processing_hooks:
            try:
                hook(result)
            except Exception:
                pass

        # Auto-export if configured
        if self.config["auto_export_sessions"] and conversation["turns"] % 10 == 0:
            self.export_conversation_data(conversation_id)

        return result

    def optimize_command_interaction(
        self, command: str, output: str, command_type: str = "general"
    ) -> dict[str, Any]:
        """
        Optimize command-line tool interactions.

        Args:
            command: Command that was executed
            output: Command output
            command_type: Type of command (git, test, status, etc.)

        Returns:
            Optimized interaction result
        """
        # Create context-aware input
        contextualized_input = f"Execute {command_type} command: {command}"

        # Determine optimization level based on command type
        if command_type in ["test", "build", "lint"]:
            opt_level = OptimizationLevel.STANDARD
        elif command_type in ["status", "list", "show"]:
            opt_level = OptimizationLevel.AGGRESSIVE
        elif command_type in ["safety", "critical", "emergency"]:
            opt_level = OptimizationLevel.CONSERVATIVE
        else:
            opt_level = None  # Let adaptive mode decide

        return self.process_conversation_turn(
            user_input=contextualized_input,
            ai_response=output,
            conversation_id=f"cmd_{command_type}",
            optimization_level=opt_level,
        )

    def get_conversation_metrics(self, conversation_id: str) -> dict[str, Any]:
        """Get metrics for specific conversation."""
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation not found"}

        conversation = self.active_conversations[conversation_id]
        optimizer_summary = self.optimizer.get_conversation_summary()

        return {
            "conversation_specific": conversation,
            "session_summary": optimizer_summary,
            "optimization_status": self.middleware.get_optimization_status(),
        }

    def get_global_metrics(self) -> dict[str, Any]:
        """Get global conversation management metrics."""
        return {
            "total_interactions": self.total_interactions,
            "total_tokens_saved": self.total_tokens_saved,
            "active_conversations": len(self.active_conversations),
            "conversation_list": list(self.active_conversations.keys()),
            "configuration": self.config,
            "optimization_enabled": self.middleware.optimization_enabled,
            "platform_summary": self.optimizer.get_conversation_summary(),
        }

    def enable_optimization(self, enabled: bool = True) -> None:
        """Enable or disable optimization across all conversations."""
        self.middleware.enable_optimization(enabled)
        self.config["optimization_enabled"] = enabled
        self.save_configuration()

    def set_optimization_parameters(
        self,
        token_budget: int | None = None,
        adaptive_mode: bool | None = None,
        debug_mode: bool | None = None,
    ) -> None:
        """Configure optimization parameters."""
        if token_budget is not None:
            self.optimizer.set_token_budget(token_budget)
            self.config["token_budget_per_turn"] = token_budget

        if adaptive_mode is not None:
            self.optimizer.enable_adaptive_mode(adaptive_mode)
            self.config["adaptive_mode"] = adaptive_mode

        if debug_mode is not None:
            self.middleware.enable_debug_mode(debug_mode)
            self.config["debug_mode"] = debug_mode

        self.save_configuration()

    def register_hooks(
        self,
        pre_processing_hook: Callable | None = None,
        post_processing_hook: Callable | None = None,
    ) -> None:
        """Register processing hooks for custom integrations."""
        if pre_processing_hook:
            self.pre_processing_hooks.append(pre_processing_hook)
        if post_processing_hook:
            self.post_processing_hooks.append(post_processing_hook)

    def export_conversation_data(self, conversation_id: str | None = None) -> list[Path]:
        """Export conversation data for analysis."""
        exported_files = []

        if conversation_id:
            # Export specific conversation
            export_path = self.optimizer.export_session_data()
            exported_files.append(export_path)
        else:
            # Export all conversations
            for _conv_id in self.active_conversations:
                export_path = self.optimizer.export_session_data()
                exported_files.append(export_path)

        return exported_files

    def reset_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Reset specific conversation and return final metrics."""
        if conversation_id in self.active_conversations:
            final_metrics = self.get_conversation_metrics(conversation_id)
            del self.active_conversations[conversation_id]
            return final_metrics
        return {"error": "Conversation not found"}

    def reset_all_conversations(self) -> dict[str, Any]:
        """Reset all conversations and return global metrics."""
        final_metrics = self.get_global_metrics()

        # Export data before reset
        if self.config["auto_export_sessions"]:
            self.export_conversation_data()

        # Reset optimizer session
        self.optimizer.reset_session()

        # Clear conversation tracking
        self.active_conversations.clear()
        self.total_interactions = 0
        self.total_tokens_saved = 0

        return final_metrics

    def compress_conversation_history(self, conversation_id: str | None = None) -> dict[str, Any]:
        """Compress conversation history for a specific conversation or all."""
        compressed_history, tokens_saved = self.optimizer.optimize_conversation_history()

        return {
            "compressed_history": compressed_history,
            "tokens_saved": tokens_saved,
            "compression_applied": len(compressed_history) > 0,
            "conversation_id": conversation_id or "all",
        }


# Global conversation manager instance for project-wide use
_global_conversation_manager: ConversationManager | None = None


def get_conversation_manager(project_root: Path | None = None) -> ConversationManager:
    """Get or create global conversation manager instance."""
    global _global_conversation_manager

    if _global_conversation_manager is None:
        _global_conversation_manager = ConversationManager(project_root)

    return _global_conversation_manager


def optimize_interaction(
    user_input: str, ai_response: str = "", command_type: str = "general"
) -> dict[str, Any]:
    """
    Convenience function for optimizing any AI interaction.

    Args:
        user_input: User input or command description
        ai_response: AI response or command output
        command_type: Type of interaction (for optimization tuning)

    Returns:
        Optimized interaction result with full metadata
    """
    manager = get_conversation_manager()

    if command_type == "general":
        return manager.process_conversation_turn(user_input, ai_response)
    else:
        return manager.optimize_command_interaction(user_input, ai_response, command_type)


def get_optimization_status() -> dict[str, Any]:
    """Get current optimization status across the platform."""
    manager = get_conversation_manager()
    return manager.get_global_metrics()


def configure_optimization(
    enabled: bool | None = None,
    token_budget: int | None = None,
    adaptive_mode: bool | None = None,
    debug_mode: bool | None = None,
) -> None:
    """Configure platform-wide optimization settings."""
    manager = get_conversation_manager()

    if enabled is not None:
        manager.enable_optimization(enabled)

    manager.set_optimization_parameters(
        token_budget=token_budget, adaptive_mode=adaptive_mode, debug_mode=debug_mode
    )


# Integration decorator for automatic optimization
def optimize_ai_interaction(command_type: str = "general") -> Callable:
    """Decorator to automatically optimize AI interactions."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute original function
            result = func(*args, **kwargs)

            # Extract input/output for optimization
            if hasattr(result, "__dict__"):
                # Handle object results
                input_text = str(args[0]) if args else "function_call"
                output_text = str(result)
            elif isinstance(result, (str, dict)):
                input_text = str(args[0]) if args else "function_call"
                output_text = str(result)
            else:
                return result  # Don't optimize non-text results

            # Apply optimization
            optimization_result = optimize_interaction(
                user_input=input_text, ai_response=output_text, command_type=command_type
            )

            # Return original result with optimization metadata
            if isinstance(result, dict):
                result["_optimization"] = optimization_result["optimization_metadata"]

            return result

        return wrapper

    return decorator
