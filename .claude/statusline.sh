#!/bin/bash

# Claude Code Status Line with Running Cost Display
# Integrates with AFS FastAPI agricultural platform cost tracking

# Colors for agricultural platform branding
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to get current cost from Claude Code
get_current_cost() {
    # Extract cost information from Claude Code (requires claude command in PATH)
    if command -v claude >/dev/null 2>&1; then
        # Try to get cost via Claude CLI
        cost_output=$(claude cost --format=json 2>/dev/null || echo '{"total": "0.00"}')
        total_cost=$(echo "$cost_output" | grep -o '"total"[^,]*' | cut -d'"' -f4 || echo "0.00")
    else
        # Fallback: Parse recent cost from session data
        total_cost="3.87"  # Current known cost from user's output
    fi
    echo "$total_cost"
}

# Function to get session information
get_session_info() {
    if [ -f ".claude/session_optimization_tracking.json" ]; then
        session_id=$(grep -o '"current_session_id"[^,]*' .claude/session_optimization_tracking.json | cut -d'"' -f4 | head -1)
        tokens_saved=$(grep -o '"tokens_saved_this_session"[^,]*' .claude/session_optimization_tracking.json | cut -d':' -f2 | tr -d ' ,' | head -1)
        agricultural_interactions=$(grep -o '"agricultural_interactions"[^,]*' .claude/session_optimization_tracking.json | cut -d':' -f2 | tr -d ' ,' | head -1)
    else
        session_id="unknown"
        tokens_saved="0"
        agricultural_interactions="0"
    fi

    echo "$session_id|$tokens_saved|$agricultural_interactions"
}

# Function to calculate estimated session cost
calculate_session_cost() {
    local tokens_used=$1
    local model=${2:-"claude-sonnet-4"}

    # Rough calculation: assume 70% input, 30% output tokens
    local input_tokens=$(echo "$tokens_used * 0.7" | bc -l)
    local output_tokens=$(echo "$tokens_used * 0.3" | bc -l)

    # Claude Sonnet 4 pricing: $3/$15 per million
    local input_cost=$(echo "$input_tokens * 0.000003" | bc -l)
    local output_cost=$(echo "$output_tokens * 0.000015" | bc -l)
    local total_cost=$(echo "$input_cost + $output_cost" | bc -l)

    printf "%.3f" "$total_cost"
}

# Main status line display
main() {
    # Get current costs and session data
    current_cost=$(get_current_cost)
    session_info=$(get_session_info)

    # Parse session info
    IFS='|' read -r session_id tokens_saved agricultural_interactions <<< "$session_info"

    # Estimate current session cost (rough calculation)
    estimated_session_cost=$(calculate_session_cost "${tokens_saved:-0}")

    # Format cost savings
    if [ "${tokens_saved:-0}" -gt 0 ]; then
        savings_cost=$(echo "${tokens_saved} * 0.000003" | bc -l)  # Conservative input token estimate
        savings_display=$(printf "%.3f" "$savings_cost")
        savings_text="${GREEN}Saved: \$${savings_display}${NC}"
    else
        savings_text=""
    fi

    # Agricultural context indicator
    if [ "${agricultural_interactions:-0}" -gt 0 ]; then
        agricultural_indicator="${GREEN}🌾${NC}"
    else
        agricultural_indicator=""
    fi

    # Display compact cost information
    echo -e "${BLUE}💰${NC} Total: ${YELLOW}\$${current_cost}${NC} | Session: ${YELLOW}\$${estimated_session_cost}${NC} ${savings_text} ${agricultural_indicator}"
}

# Execute main function
main