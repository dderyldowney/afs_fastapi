#!/usr/bin/env python3
"""
Claude API Cost Calculator for AFS FastAPI Agricultural Robotics Platform.

Provides real-time cost calculation for Claude API usage, enabling accurate
budget tracking and cost optimization for safety-critical agricultural
robotics development operations.

Agricultural Context:
Multi-tractor coordination development requires careful AI budget management
due to extensive testing, safety validation, and compliance documentation
requiring substantial token usage for agricultural equipment certification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class UnsupportedModelError(Exception):
    """Exception raised when an unsupported Claude model is specified."""

    pass


@dataclass
class ConversationCost:
    """Data class representing cost parameters for a conversation."""

    input_tokens: int
    output_tokens: int
    model: str


@dataclass
class CostResult:
    """Result of cost calculation with detailed breakdown."""

    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal


@dataclass
class SessionCostSummary:
    """Summary of costs for an agricultural AI session."""

    session_id: str
    total_input_tokens: int
    total_output_tokens: int
    total_cost: Decimal
    agricultural_interactions: int
    safety_critical_interactions: int


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for agricultural budget analysis."""

    input_tokens: int
    input_cost: Decimal
    output_tokens: int
    output_cost: Decimal
    model: str

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost from input and output costs."""
        return self.input_cost + self.output_cost


@dataclass
class SessionCostData:
    """Session cost tracking data."""

    total_cost: Decimal
    agricultural_interactions: int = 0
    safety_critical_interactions: int = 0


class CostCalculator:
    """
    Claude API cost calculator for agricultural robotics platform.

    Converts token usage into real money costs based on current Claude pricing,
    enabling accurate budget tracking for safety-critical agricultural development.
    """

    # Current Claude API pricing (2025) - costs per million tokens
    MODEL_PRICING = {
        "claude-sonnet-4": {
            "input": Decimal("3.00"),  # $3.00 per million input tokens
            "output": Decimal("15.00"),  # $15.00 per million output tokens
        },
        "claude-haiku-3.5": {
            "input": Decimal("0.25"),  # $0.25 per million input tokens
            "output": Decimal("1.25"),  # $1.25 per million output tokens
        },
        "claude-opus-4.1": {
            "input": Decimal("15.00"),  # $15.00 per million input tokens
            "output": Decimal("75.00"),  # $75.00 per million output tokens
        },
    }

    def calculate_input_cost(self, tokens: int, model: str) -> Decimal:
        """Calculate cost for input tokens.

        Args:
            tokens: Number of input tokens
            model: Claude model name

        Returns:
            Cost in USD as Decimal

        Raises:
            UnsupportedModelError: If model is not supported
        """
        if model not in self.MODEL_PRICING:
            raise UnsupportedModelError(f"Unsupported model: {model}")

        cost_per_million = self.MODEL_PRICING[model]["input"]
        return (Decimal(str(tokens)) / Decimal("1000000")) * cost_per_million

    def calculate_output_cost(self, tokens: int, model: str) -> Decimal:
        """Calculate cost for output tokens.

        Args:
            tokens: Number of output tokens
            model: Claude model name

        Returns:
            Cost in USD as Decimal

        Raises:
            UnsupportedModelError: If model is not supported
        """
        if model not in self.MODEL_PRICING:
            raise UnsupportedModelError(f"Unsupported model: {model}")

        cost_per_million = self.MODEL_PRICING[model]["output"]
        return (Decimal(str(tokens)) / Decimal("1000000")) * cost_per_million

    def calculate_conversation_cost(self, conversation: ConversationCost) -> CostResult:
        """Calculate total cost for a conversation.

        Args:
            conversation: Conversation cost parameters

        Returns:
            Detailed cost breakdown
        """
        input_cost = self.calculate_input_cost(conversation.input_tokens, conversation.model)
        output_cost = self.calculate_output_cost(conversation.output_tokens, conversation.model)

        return CostResult(
            input_cost=input_cost, output_cost=output_cost, total_cost=input_cost + output_cost
        )

    def calculate_optimization_savings(self, optimizer_data: dict[str, Any]) -> Decimal:
        """Calculate cost savings from token optimization.

        Args:
            optimizer_data: Token optimization data from RealtimeTokenOptimizer

        Returns:
            Cost savings in USD as Decimal
        """
        tokens_saved = optimizer_data["total_tokens_saved"]
        model = optimizer_data["model"]

        # Assume savings are primarily input tokens (conservative estimate)
        return self.calculate_input_cost(tokens_saved, model)


class CostDisplayFormatter:
    """
    Format cost information for agricultural platform displays.

    Provides clear, readable cost formatting for agricultural technicians
    and project managers tracking AI usage during field operations.
    """

    def format_currency(self, amount: Decimal) -> str:
        """Format decimal amount as currency string.

        Args:
            amount: Decimal amount to format

        Returns:
            Formatted currency string (e.g., "$1.23")
        """
        return f"${amount:.2f}"

    def format_session_summary(self, summary: SessionCostSummary) -> str:
        """Format session cost summary for agricultural operations display.

        Args:
            summary: Session cost summary data

        Returns:
            Formatted session summary string
        """
        return (
            f"Session: {summary.session_id}\n"
            f"Total Cost: {self.format_currency(summary.total_cost)}\n"
            f"Interactions: {summary.agricultural_interactions} agricultural, "
            f"{summary.safety_critical_interactions} safety-critical"
        )

    def format_cost_breakdown(self, breakdown: CostBreakdown) -> str:
        """Format detailed cost breakdown for agricultural budget analysis.

        Args:
            breakdown: Cost breakdown data

        Returns:
            Formatted breakdown string
        """
        return (
            f"Cost Breakdown ({breakdown.model}):\n"
            f"Input: {breakdown.input_tokens:,} tokens → {self.format_currency(breakdown.input_cost)}\n"
            f"Output: {breakdown.output_tokens:,} tokens → {self.format_currency(breakdown.output_cost)}\n"
            f"Total: {self.format_currency(breakdown.total_cost)}"
        )


class SessionCostTracker:
    """
    Track costs for agricultural AI sessions in real-time.

    Integrates with existing session monitoring to provide cost data
    for agricultural project budget tracking and resource planning.
    """

    def __init__(self) -> None:
        """Initialize session cost tracker."""
        self.calculator = CostCalculator()
        self._session_data = SessionCostData(total_cost=Decimal("0"))

    def add_interaction(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        agricultural_context: bool = False,
        safety_critical: bool = False,
    ) -> None:
        """Add interaction to session cost tracking.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Claude model used
            agricultural_context: Whether interaction was agricultural-related
            safety_critical: Whether interaction was safety-critical
        """
        # Calculate cost for this interaction
        input_cost = self.calculator.calculate_input_cost(input_tokens, model)
        output_cost = self.calculator.calculate_output_cost(output_tokens, model)
        interaction_cost = input_cost + output_cost

        # Update session totals
        self._session_data.total_cost += interaction_cost

        if agricultural_context:
            self._session_data.agricultural_interactions += 1

        if safety_critical:
            self._session_data.safety_critical_interactions += 1

    def get_session_cost(self) -> SessionCostData:
        """Get current session cost data.

        Returns:
            Current session cost data
        """
        return self._session_data


class CostReportExporter:
    """
    Export cost data for agricultural project reporting.

    Generates cost reports for budget review, compliance documentation,
    and resource allocation planning for agricultural robotics projects.
    """

    def export_session_report(self, session_data: dict[str, Any]) -> str:
        """Export session cost report as JSON.

        Args:
            session_data: Session cost and metadata

        Returns:
            JSON-formatted report string
        """
        report = {
            "session_id": session_data["session_id"],
            "start_time": session_data["start_time"],
            "end_time": session_data["end_time"],
            "total_cost": str(session_data["total_cost"]),  # Convert Decimal to string
            "agricultural_context": {
                "interactions": session_data["agricultural_interactions"],
                "safety_interactions": session_data["safety_interactions"],
                "equipment_tested": session_data["equipment_tested"],
            },
        }

        return json.dumps(report, indent=2)
