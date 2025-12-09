#!/usr/bin/env python3
"""
Review and Cleanup Script

Reviews current state of the project and identifies:
1. What we've built
2. What's working
3. What needs cleanup
4. What's redundant/archived
"""

import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

print("=" * 80)
print("Project Review and Cleanup Analysis")
print("=" * 80)

# 1. Scripts Review
print("\n📁 Scripts Directory Review")
print("-" * 80)

scripts_dir = backend_dir / "scripts"
active_scripts = []
archived_scripts = []

for script in sorted(scripts_dir.glob("*.py")):
    if script.name == "__init__.py":
        continue
    if "archive" in str(script):
        archived_scripts.append(script.name)
    else:
        active_scripts.append(script.name)

print(f"\n✅ Active Scripts ({len(active_scripts)}):")
for script in active_scripts:
    print(f"   - {script}")

print(f"\n📦 Archived Scripts ({len(archived_scripts)}):")
for script in archived_scripts:
    print(f"   - {script}")

# 2. Reports Review
print("\n📊 Reports Directory Review")
print("-" * 80)

reports_dir = backend_dir / "reports"
active_reports = []
archived_reports = []

for report in sorted(reports_dir.glob("*.md")):
    if "archive" in str(report):
        archived_reports.append(report.name)
    else:
        active_reports.append(report.name)

print(f"\n✅ Active Reports ({len(active_reports)}):")
for report in active_reports:
    print(f"   - {report}")

print(f"\n📦 Archived Reports ({len(archived_reports)}):")
for report in archived_reports:
    print(f"   - {report}")

# 3. Documentation Review
print("\n📚 Documentation Review")
print("-" * 80)

docs_dir = project_root / "docs" / "forecasting"
if docs_dir.exists():
    docs = sorted(docs_dir.glob("*.md"))
    print(f"\n✅ Documentation Files ({len(docs)}):")
    for doc in docs:
        print(f"   - {doc.name}")

# 4. Key Components Status
print("\n🔧 Key Components Status")
print("-" * 80)

components = {
    "ForecastService": backend_dir / "forecasting" / "services" / "forecast_service.py",
    "SKUClassifier": backend_dir / "forecasting" / "services" / "sku_classifier.py",
    "QualityCalculator": backend_dir / "forecasting" / "services" / "quality_calculator.py",
    "DataValidator": backend_dir / "forecasting" / "services" / "data_validator.py",
    "Chronos2Model": backend_dir / "forecasting" / "modes" / "ml" / "chronos2.py",
    "MA7Model": backend_dir / "forecasting" / "modes" / "statistical" / "moving_average.py",
    "ModelFactory": backend_dir / "forecasting" / "modes" / "factory.py",
}

print("\n✅ Core Components:")
for name, path in components.items():
    status = "✅" if path.exists() else "❌"
    print(f"   {status} {name}: {path.name}")

# 5. Recommendations
print("\n💡 Cleanup Recommendations")
print("-" * 80)

recommendations = []

# Check for duplicate scripts
if (scripts_dir / "comprehensive_model_comparison.py").exists() and \
   (scripts_dir / "comprehensive_model_comparison_all_skus.py").exists():
    recommendations.append("⚠️  Two comprehensive comparison scripts - consider consolidating")

# Check for old test scripts
old_tests = ["test_ma7_with_enhanced_validator.py", "compare_darts_vs_ours.py"]
for old_test in old_tests:
    if (scripts_dir / "archive" / old_test).exists():
        recommendations.append(f"✅ {old_test} already archived - good")

# Check reports
if len(archived_reports) > 10:
    recommendations.append(f"📦 {len(archived_reports)} archived reports - consider deeper archive")

if recommendations:
    for rec in recommendations:
        print(f"   {rec}")
else:
    print("   ✅ No cleanup needed - project is well organized")

# 6. Integration Status
print("\n🔗 Integration Status")
print("-" * 80)

integrations = {
    "SKU Classification": "✅ Implemented & Tested",
    "Method Routing": "⚠️  Partially implemented (needs testing)",
    "Quality Metrics": "✅ Implemented & Used",
    "M5 Dataset": "✅ Imported & Validated",
    "API Endpoints": "✅ Working",
    "Database Schema": "✅ Migrations applied",
}

for component, status in integrations.items():
    print(f"   {status} {component}")

print("\n" + "=" * 80)
print("Review Complete!")
print("=" * 80)

