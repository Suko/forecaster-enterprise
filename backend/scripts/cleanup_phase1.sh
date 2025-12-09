#!/bin/bash
# Phase 1 Cleanup Script
# Archives old scripts and reports that are superseded by comprehensive_model_comparison.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$SCRIPT_DIR/../reports"

echo "🧹 Phase 1 Cleanup"
echo "=================="

# Create archive directories
mkdir -p "$SCRIPT_DIR/archive"
mkdir -p "$REPORTS_DIR/archive"

echo ""
echo "📦 Archiving old scripts..."

# Archive superseded scripts
if [ -f "$SCRIPT_DIR/compare_darts_vs_ours.py" ]; then
    mv "$SCRIPT_DIR/compare_darts_vs_ours.py" "$SCRIPT_DIR/archive/"
    echo "  ✅ Archived: compare_darts_vs_ours.py"
fi

if [ -f "$SCRIPT_DIR/diagnose_chronos.py" ]; then
    mv "$SCRIPT_DIR/diagnose_chronos.py" "$SCRIPT_DIR/archive/"
    echo "  ✅ Archived: diagnose_chronos.py"
fi

if [ -f "$SCRIPT_DIR/investigate_sku001.py" ]; then
    mv "$SCRIPT_DIR/investigate_sku001.py" "$SCRIPT_DIR/archive/"
    echo "  ✅ Archived: investigate_sku001.py"
fi

if [ -f "$SCRIPT_DIR/test_ma7_with_enhanced_validator.py" ]; then
    mv "$SCRIPT_DIR/test_ma7_with_enhanced_validator.py" "$SCRIPT_DIR/archive/"
    echo "  ✅ Archived: test_ma7_with_enhanced_validator.py"
fi

# Move test_enhanced_validator.py to tests/
if [ -f "$SCRIPT_DIR/test_enhanced_validator.py" ]; then
    mkdir -p "$SCRIPT_DIR/../tests/test_forecasting"
    mv "$SCRIPT_DIR/test_enhanced_validator.py" "$SCRIPT_DIR/../tests/test_forecasting/"
    echo "  ✅ Moved: test_enhanced_validator.py → tests/test_forecasting/"
fi

echo ""
echo "📄 Archiving old reports..."

# Archive superseded reports
if [ -f "$REPORTS_DIR/SKU001_INVESTIGATION.md" ]; then
    mv "$REPORTS_DIR/SKU001_INVESTIGATION.md" "$REPORTS_DIR/archive/"
    echo "  ✅ Archived: SKU001_INVESTIGATION.md"
fi

if [ -f "$REPORTS_DIR/FORECAST_COMPARISON_TABLE.md" ]; then
    mv "$REPORTS_DIR/FORECAST_COMPARISON_TABLE.md" "$REPORTS_DIR/archive/"
    echo "  ✅ Archived: FORECAST_COMPARISON_TABLE.md"
fi

if [ -f "$REPORTS_DIR/MA7_VALIDATION_WITH_ENHANCED_VALIDATOR.md" ]; then
    mv "$REPORTS_DIR/MA7_VALIDATION_WITH_ENHANCED_VALIDATOR.md" "$REPORTS_DIR/archive/"
    echo "  ✅ Archived: MA7_VALIDATION_WITH_ENHANCED_VALIDATOR.md"
fi

if [ -f "$REPORTS_DIR/DARTS_VS_OURS_COMPARISON.md" ]; then
    mv "$REPORTS_DIR/DARTS_VS_OURS_COMPARISON.md" "$REPORTS_DIR/archive/"
    echo "  ✅ Archived: DARTS_VS_OURS_COMPARISON.md"
fi

echo ""
echo "📊 Keeping latest JSON reports..."
# Keep only the latest comprehensive comparison
LATEST_COMPREHENSIVE=$(ls -t "$REPORTS_DIR"/comprehensive_model_comparison_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_COMPREHENSIVE" ]; then
    echo "  ✅ Latest: $(basename "$LATEST_COMPREHENSIVE")"
    # Archive older comprehensive reports
    for file in "$REPORTS_DIR"/comprehensive_model_comparison_*.json; do
        if [ "$file" != "$LATEST_COMPREHENSIVE" ]; then
            mv "$file" "$REPORTS_DIR/archive/"
            echo "  ✅ Archived: $(basename "$file")"
        fi
    done
fi

# Keep latest forecast accuracy report
LATEST_ACCURACY=$(ls -t "$REPORTS_DIR"/forecast_accuracy_report_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_ACCURACY" ]; then
    echo "  ✅ Latest: $(basename "$LATEST_ACCURACY")"
    # Archive older accuracy reports
    for file in "$REPORTS_DIR"/forecast_accuracy_report_*.json; do
        if [ "$file" != "$LATEST_ACCURACY" ]; then
            mv "$file" "$REPORTS_DIR/archive/"
            echo "  ✅ Archived: $(basename "$file")"
        fi
    done
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Archived files:"
echo "   Scripts: $SCRIPT_DIR/archive/"
echo "   Reports: $REPORTS_DIR/archive/"
echo ""
echo "💡 To restore archived files:"
echo "   mv $SCRIPT_DIR/archive/*.py $SCRIPT_DIR/"
echo "   mv $REPORTS_DIR/archive/*.md $REPORTS_DIR/"

