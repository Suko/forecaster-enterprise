#!/usr/bin/env python3
"""
Generate Interactive Simulation Report

Creates an HTML report with charts showing:
- Real vs Simulated inventory levels over time
- Reorder flags (when orders were placed)
- Stockout periods
- Key metrics
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_simulation_data(json_file: str) -> Dict:
    """Load simulation results from JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def generate_html_report(data: Dict, output_file: str, item_id: Optional[str] = None):
    """
    Generate HTML report with interactive charts
    
    Args:
        data: Simulation response data
        output_file: Path to output HTML file
        item_id: Optional item ID to filter (if None, uses first item)
    """
    # Get daily comparisons
    daily_comparisons = data.get('daily_comparison', [])
    
    # Filter by item_id if provided
    if item_id:
        daily_comparisons = [d for d in daily_comparisons if d['item_id'] == item_id]
    elif daily_comparisons:
        # Use first item if not specified
        item_id = daily_comparisons[0]['item_id']
        daily_comparisons = [d for d in daily_comparisons if d['item_id'] == item_id]
    
    if not daily_comparisons:
        print(f"Error: No daily comparison data found for item {item_id}")
        return
    
    # Sort by date
    daily_comparisons.sort(key=lambda x: x['date'])
    
    # Extract data for charts
    dates = [d['date'] for d in daily_comparisons]
    simulated_stock = [d['simulated_stock'] for d in daily_comparisons]
    real_stock = [d['real_stock'] for d in daily_comparisons]
    actual_sales = [d.get('actual_sales', 0) or 0 for d in daily_comparisons]
    
    # Find reorder points (days with orders placed)
    reorder_dates = [d['date'] for d in daily_comparisons if d.get('order_placed')]
    reorder_stocks = [d['simulated_stock'] for d in daily_comparisons if d.get('order_placed')]
    reorder_quantities = [d.get('order_quantity', 0) for d in daily_comparisons if d.get('order_placed')]
    
    # Find stockout periods
    simulated_stockouts = [i for i, d in enumerate(daily_comparisons) if d['simulated_stockout']]
    real_stockouts = [i for i, d in enumerate(daily_comparisons) if d['real_stockout']]
    
    # Get metrics
    results = data.get('results', {})
    improvements = data.get('improvements', {})
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulation Report - {item_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #1a1a1a;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 20px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 600;
            color: #1a1a1a;
        }}
        .metric-improvement {{
            font-size: 14px;
            margin-top: 4px;
        }}
        .improvement-positive {{
            color: #10b981;
        }}
        .improvement-negative {{
            color: #ef4444;
        }}
        .chart-container {{
            position: relative;
            height: 500px;
            margin-bottom: 40px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
        .info-section {{
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid #e5e7eb;
        }}
        .info-section h2 {{
            font-size: 20px;
            margin-bottom: 15px;
            color: #1a1a1a;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .info-item {{
            font-size: 14px;
        }}
        .info-label {{
            color: #6b7280;
            margin-bottom: 4px;
        }}
        .info-value {{
            color: #1a1a1a;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Simulation Report</h1>
        <div class="subtitle">
            Item: {item_id} | Period: {data.get('start_date')} to {data.get('end_date')} | 
            Total Days: {data.get('total_days')} | Status: {data.get('status')}
        </div>
        <div style="background: #dbeafe; border: 1px solid #3b82f6; border-radius: 6px; padding: 12px; margin-bottom: 20px; font-size: 13px; color: #1e40af;">
            <strong>ℹ️ Note on Real Inventory:</strong> Real inventory values come from <code>stock_on_date</code> in the database 
            (historical stock levels). When <code>stock_on_date</code> is not available, values are calculated from previous day minus sales. 
            <strong>Stockout rates and service levels are the primary comparison metrics.</strong>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Stockout Rate</div>
                <div class="metric-value">
                    Sim: {results.get('stockout_rate', {}).get('simulated', 0):.2%}<br>
                    Real: {results.get('stockout_rate', {}).get('real', 0):.2%}
                </div>
                <div class="metric-improvement improvement-positive">
                    ↓ {improvements.get('stockout_reduction', 0):.1%} reduction
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Service Level</div>
                <div class="metric-value">
                    Sim: {results.get('service_level', {}).get('simulated', 0):.2%}<br>
                    Real: {results.get('service_level', {}).get('real', 0):.2%}
                </div>
                <div class="metric-improvement improvement-positive">
                    ↑ {improvements.get('service_level_improvement', 0):.1%} improvement
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Average Inventory Value</div>
                <div class="metric-value">
                    Sim: ${float(str(results.get('inventory_value', {}).get('simulated', 0))):,.2f}<br>
                    Real: ${float(str(results.get('inventory_value', {}).get('real', 0))):,.2f}
                </div>
                <div class="metric-improvement" style="font-size: 11px; color: #6b7280; margin-top: 4px;">
                    ℹ️ Real inventory from stock_on_date (historical data)
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Orders Placed</div>
                <div class="metric-value">{len(reorder_dates)}</div>
                <div class="metric-improvement">
                    Avg: {data.get('total_days', 1) / max(len(reorder_dates), 1):.1f} days between orders
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="inventoryChart"></canvas>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #3b82f6;"></div>
                <span>Simulated Inventory</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ef4444;"></div>
                <span>Real Inventory</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f59e0b;"></div>
                <span>Daily Sales</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #10b981; width: 20px; height: 4px;"></div>
                <span>Reorder Points (Orders Placed)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(239, 68, 68, 0.2);"></div>
                <span>Stockout Periods</span>
            </div>
        </div>
        
        <div class="info-section">
            <h2>Order Timeline</h2>
            <div class="info-grid">
"""
    
    # Add order timeline
    for i, (date, stock, qty) in enumerate(zip(reorder_dates, reorder_stocks, reorder_quantities), 1):
        html += f"""
                <div class="info-item">
                    <div class="info-label">Order #{i}</div>
                    <div class="info-value">{date}</div>
                    <div class="info-label">Qty: {qty:.0f} units | Stock: {stock:.1f}</div>
                </div>
"""
    
    html += """
            </div>
        </div>
    </div>
    
    <script>
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {
        const canvas = document.getElementById('inventoryChart');
        if (!canvas) {
            console.error('Canvas element not found!');
            return;
        }
        const ctx = canvas.getContext('2d');
        
        // Prepare data
        const dates = """ + json.dumps(dates) + """;
        const simulatedStock = """ + json.dumps(simulated_stock) + """;
        const realStock = """ + json.dumps(real_stock) + """;
        const actualSales = """ + json.dumps(actual_sales) + """;
        const reorderDates = """ + json.dumps(reorder_dates) + """;
        const reorderStocks = """ + json.dumps(reorder_stocks) + """;
        const reorderQuantities = """ + json.dumps(reorder_quantities) + """;
        const simulatedStockouts = """ + json.dumps(simulated_stockouts) + """;
        const realStockouts = """ + json.dumps(real_stockouts) + """;
        
        // Find max value for dual y-axis scaling
        const maxStock = Math.max(...simulatedStock, ...realStock, 1);
        const maxSales = Math.max(...actualSales, 1);
        
        // Prepare reorder point data - create array matching dates length
        // with null values except at reorder dates
        const reorderPointData = dates.map((date, idx) => {
            const reorderIdx = reorderDates.indexOf(date);
            if (reorderIdx !== -1) {
                return reorderStocks[reorderIdx];
            }
            return null;
        });
        
        // Store reorder metadata for tooltips (by date)
        const reorderMetadata = {};
        reorderDates.forEach((date, idx) => {
            reorderMetadata[date] = {
                stock: reorderStocks[idx],
                qty: reorderQuantities[idx]
            };
        });
        
        // Prepare stockout regions (using background color datasets)
        function groupConsecutive(arr) {
            if (arr.length === 0) return [];
            const groups = [];
            let start = arr[0];
            let end = arr[0];
            
            for (let i = 1; i < arr.length; i++) {
                if (arr[i] === end + 1) {
                    end = arr[i];
                } else {
                    groups.push({ start, end });
                    start = arr[i];
                    end = arr[i];
                }
            }
            groups.push({ start, end });
            return groups;
        }
        
        // Create stockout background datasets
        const stockoutDatasets = [];
        const simulatedStockoutGroups = groupConsecutive(simulatedStockouts);
        simulatedStockoutGroups.forEach((group, idx) => {
            const stockoutData = dates.map((_, i) => {
                if (i >= group.start && i <= group.end) {
                    return maxStock;
                }
                return null;
            });
            stockoutDatasets.push({
                label: idx === 0 ? 'Simulated Stockout Periods' : '',
                data: stockoutData,
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                borderColor: 'rgba(239, 68, 68, 0.3)',
                borderWidth: 0,
                fill: true,
                pointRadius: 0,
                order: 0
            });
        });
        
        const realStockoutGroups = groupConsecutive(realStockouts);
        realStockoutGroups.forEach((group, idx) => {
            const stockoutData = dates.map((_, i) => {
                if (i >= group.start && i <= group.end) {
                    return maxStock;
                }
                return null;
            });
            stockoutDatasets.push({
                label: idx === 0 ? 'Real Stockout Periods' : '',
                data: stockoutData,
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderColor: 'rgba(239, 68, 68, 0.2)',
                borderWidth: 0,
                borderDash: [5, 5],
                fill: true,
                pointRadius: 0,
                order: 0
            });
        });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    ...stockoutDatasets,
                    {
                        label: 'Simulated Inventory',
                        data: simulatedStock,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y',
                        order: 2
                    },
                    {
                        label: 'Real Inventory',
                        data: realStock,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y',
                        order: 2
                    },
                    {
                        label: 'Daily Sales',
                        data: actualSales,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y1',
                        order: 2,
                        borderDash: [5, 5]
                    },
                    {
                        label: 'Reorder Points',
                        data: reorderPointData,
                        borderColor: '#10b981',
                        backgroundColor: '#10b981',
                        borderWidth: 0,
                        pointRadius: function(context) {
                            return context.parsed.y !== null ? 8 : 0;
                        },
                        pointHoverRadius: function(context) {
                            return context.parsed.y !== null ? 10 : 0;
                        },
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#10b981',
                        pointBorderWidth: 2,
                        pointStyle: function(context) {
                            return context.parsed.y !== null ? 'triangle' : 'circle';
                        },
                        pointRotation: function(context) {
                            return context.parsed.y !== null ? 180 : 0;
                        },
                        showLine: false,
                        order: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: { size: 12 },
                            filter: function(item) {
                                return item.text !== ''; // Hide empty labels
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label === 'Reorder Points' && context.parsed.y !== null) {
                                    const date = dates[context.dataIndex];
                                    const meta = reorderMetadata[date];
                                    if (meta) {
                                        return `Order: ${meta.qty.toFixed(0)} units | Stock: ${meta.stock.toFixed(1)}`;
                                    }
                                }
                                if (context.dataset.label === 'Daily Sales') {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' units';
                                }
                                if (context.dataset.label !== 'Reorder Points') {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' units';
                                }
                                return '';
                            },
                            title: function(context) {
                                return dates[context[0].dataIndex] || '';
                            },
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date',
                            font: { size: 12, weight: 'bold' }
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: { size: 10 }
                        }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Stock Level (units)',
                            font: { size: 12, weight: 'bold' }
                        },
                        beginAtZero: true,
                        ticks: {
                            font: { size: 10 }
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Sales (units/day)',
                            font: { size: 12, weight: 'bold' }
                        },
                        beginAtZero: true,
                        ticks: {
                            font: { size: 10 }
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            },
            plugins: []
        });
        }); // End DOMContentLoaded
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_file}")
    print(f"   Open in browser to view interactive charts")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_simulation_report.py <simulation_json_file> [output_html_file] [item_id]")
        print("\nExample:")
        print("  python generate_simulation_report.py /tmp/sim_1year.json report.html M5_HOBBIES_1_004")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'simulation_report.html'
    item_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    data = load_simulation_data(json_file)
    generate_html_report(data, output_file, item_id)

