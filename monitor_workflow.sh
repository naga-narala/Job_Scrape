#!/bin/bash
# Workflow Monitor Script

cd /Users/b/Desktop/Projects/Job_Scrape

echo "════════════════════════════════════════════════════════════════"
echo "🔍 WORKFLOW MONITOR"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if workflow is running
if [ -f workflow.pid ]; then
    PID=$(cat workflow.pid)
    if ps -p $PID > /dev/null 2>&1; then
        ELAPSED=$(ps -p $PID -o etime= | xargs)
        CPU=$(ps -p $PID -o %cpu= | xargs)
        MEM=$(ps -p $PID -o %mem= | xargs)
        echo "✅ STATUS: Running"
        echo "📊 PID: $PID"
        echo "⏱️  Elapsed: $ELAPSED"
        echo "💻 CPU: ${CPU}%"
        echo "🧠 Memory: ${MEM}%"
    else
        echo "⚠️  STATUS: Stopped"
        echo "Last PID: $PID (no longer running)"
    fi
else
    echo "⚠️  STATUS: Not running"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 PROGRESS (Last 20 lines)"
echo "════════════════════════════════════════════════════════════════"
tail -20 workflow_run.log 2>/dev/null | sed 's/^/  /'

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📈 LOG SIZE: $(ls -lh workflow_run.log 2>/dev/null | awk '{print $5}')"
echo "📝 LOG LINES: $(wc -l < workflow_run.log 2>/dev/null || echo 0)"
echo ""
echo "To monitor in real-time: tail -f workflow_run.log"
echo "To stop workflow: kill $(cat workflow.pid 2>/dev/null || echo 'N/A')"
echo "════════════════════════════════════════════════════════════════"
