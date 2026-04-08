#!/bin/bash
# Check if MCP self-reflection tools are being used

LOG_FILE="P:/packages/reasoning/mcp_usage.log"

echo "=== MCP Self-Reflection Usage Monitor ==="
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ No usage log found"
    echo ""
    echo "This means Claude hasn't called the self_reflect or critique_response tools yet."
    echo ""
    echo "Possible reasons:"
    echo "  1. Tool descriptions aren't compelling enough"
    echo "  2. Claude doesn't know when to use them"
    echo "  3. MCP server needs restart"
    echo ""
    echo "Next steps:"
    echo "  1. Restart Claude Code to reload MCP server with updated descriptions"
    echo "  2. Monitor this log file for activity"
    echo "  3. If still no activity, consider making tool descriptions more explicit"
    exit 1
fi

# Count total calls
TOTAL_CALLS=$(wc -l < "$LOG_FILE")

echo "✅ Found usage log: $TOTAL_CALLS total tool calls"
echo ""

# Show recent calls
echo "Recent activity:"
echo "-------------------"
tail -n 10 "$LOG_FILE" | while IFS= read -r line; do
    TIMESTAMP=$(echo "$line" | jq -r '.timestamp' 2>/dev/null)
    TOOL=$(echo "$line" | jq -r '.tool' 2>/dev/null)
    RESULT=$(echo "$line" | jq -r '.result' 2>/dev/null)
    DURATION=$(echo "$line" | jq -r '.duration_ms' 2>/dev/null)

    if [ -n "$TIMESTAMP" ]; then
        echo "  • $TOOL: $RESULT (${DURATION}ms)"
    fi
done

echo ""
echo "Summary by result:"
echo "-------------------"
jq -r '.result' "$LOG_FILE" 2>/dev/null | sort | uniq -c | sort -rn

echo ""
echo "Usage:"
echo "  Run this script periodically to check if tools are being used"
echo "  Watch the log file in real-time: tail -f $LOG_FILE"
