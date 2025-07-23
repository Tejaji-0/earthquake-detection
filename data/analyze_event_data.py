#!/usr/bin/env python3
"""
Analysis script for earthquake data before and after major events.
This script analyzes the extracted data to provide insights about foreshocks and aftershocks.
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

def analyze_event_data(event_analysis_dir):
    """
    Analyze the extracted event data to provide insights.
    
    Args:
        event_analysis_dir: Directory containing event analysis results
    
    Returns:
        Dictionary with analysis results
    """
    # Load processing summary
    summary_file = os.path.join(event_analysis_dir, 'processing_summary.json')
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    print(f"=== Earthquake Event Analysis ===")
    print(f"Processing Date: {summary['processing_date']}")
    print(f"Total Major Events Processed: {summary['total_events_processed']}")
    
    # Analyze before/after patterns
    events_with_before = [e for e in summary['events'] if e['before_count'] > 0]
    events_with_after = [e for e in summary['events'] if e['after_count'] > 0]
    events_with_both = [e for e in summary['events'] if e['before_count'] > 0 and e['after_count'] > 0]
    
    print(f"\nEvent Pattern Analysis:")
    print(f"Events with foreshocks (before): {len(events_with_before)} ({len(events_with_before)/len(summary['events'])*100:.1f}%)")
    print(f"Events with aftershocks (after): {len(events_with_after)} ({len(events_with_after)/len(summary['events'])*100:.1f}%)")
    print(f"Events with both fore- and aftershocks: {len(events_with_both)} ({len(events_with_both)/len(summary['events'])*100:.1f}%)")
    
    # Find events with most activity
    top_before = sorted(summary['events'], key=lambda x: x['before_count'], reverse=True)[:10]
    top_after = sorted(summary['events'], key=lambda x: x['after_count'], reverse=True)[:10]
    
    print(f"\nTop 10 Events with Most Foreshocks:")
    for i, event in enumerate(top_before, 1):
        if event['before_count'] > 0:
            print(f"{i:2d}. {event['event'][:60]}... - {event['before_count']} foreshocks")
    
    print(f"\nTop 10 Events with Most Aftershocks:")
    for i, event in enumerate(top_after, 1):
        if event['after_count'] > 0:
            print(f"{i:2d}. {event['event'][:60]}... - {event['after_count']} aftershocks")
    
    # Analyze by time periods
    events_by_decade = {}
    for event in summary['events']:
        # Extract year from directory name (format: event_YYYYMMDD_...)
        try:
            dir_parts = event['directory'].split('_')
            if len(dir_parts) >= 2 and dir_parts[1].isdigit() and len(dir_parts[1]) >= 4:
                year = int(dir_parts[1][:4])
            else:
                # Skip events with invalid directory format
                continue
            decade = (year // 10) * 10
        except (ValueError, IndexError):
            # Skip events with invalid directory format
            continue
        
        if decade not in events_by_decade:
            events_by_decade[decade] = {'total': 0, 'with_before': 0, 'with_after': 0, 'before_total': 0, 'after_total': 0}
        
        events_by_decade[decade]['total'] += 1
        events_by_decade[decade]['before_total'] += event['before_count']
        events_by_decade[decade]['after_total'] += event['after_count']
        
        if event['before_count'] > 0:
            events_by_decade[decade]['with_before'] += 1
        if event['after_count'] > 0:
            events_by_decade[decade]['with_after'] += 1
    
    print(f"\nAnalysis by Decade:")
    print(f"{'Decade':<10} {'Events':<8} {'W/Fore':<8} {'W/After':<9} {'Total Fore':<12} {'Total After':<12}")
    print("-" * 65)
    for decade in sorted(events_by_decade.keys()):
        data = events_by_decade[decade]
        print(f"{decade}s{'':<6} {data['total']:<8} {data['with_before']:<8} {data['with_after']:<9} {data['before_total']:<12} {data['after_total']:<12}")
    
    return {
        'summary': summary,
        'events_with_before': events_with_before,
        'events_with_after': events_with_after,
        'events_with_both': events_with_both,
        'top_before': top_before[:10],
        'top_after': top_after[:10],
        'by_decade': events_by_decade
    }

def create_visualization(analysis_results, output_dir):
    """Create visualizations of the analysis results."""
    
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Earthquake Event Analysis: Before and After Major Events', fontsize=16, fontweight='bold')
    
    # 1. Pie chart of event patterns
    ax1 = axes[0, 0]
    patterns = ['Only Aftershocks', 'Only Foreshocks', 'Both', 'Neither']
    
    only_after = len(analysis_results['events_with_after']) - len(analysis_results['events_with_both'])
    only_before = len(analysis_results['events_with_before']) - len(analysis_results['events_with_both'])
    both = len(analysis_results['events_with_both'])
    neither = analysis_results['summary']['total_events_processed'] - only_after - only_before - both
    
    sizes = [only_after, only_before, both, neither]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    
    wedges, texts, autotexts = ax1.pie(sizes, labels=patterns, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Distribution of Event Patterns')
    
    # 2. Bar chart of top events with most activity
    ax2 = axes[0, 1]
    top_events = analysis_results['top_after'][:8]  # Top 8 for better visibility
    event_names = [e['event'].split(' - ')[1][:30] + '...' if ' - ' in e['event'] else e['event'][:30] + '...' for e in top_events]
    after_counts = [e['after_count'] for e in top_events]
    
    bars = ax2.barh(range(len(event_names)), after_counts, color='lightcoral')
    ax2.set_yticks(range(len(event_names)))
    ax2.set_yticklabels(event_names, fontsize=8)
    ax2.set_xlabel('Number of Aftershocks')
    ax2.set_title('Top Events by Aftershock Count')
    ax2.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        if width > 0:
            ax2.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(int(width)), ha='left', va='center', fontsize=8)
    
    # 3. Timeline analysis by decade
    ax3 = axes[1, 0]
    decades = sorted(analysis_results['by_decade'].keys())
    total_events = [analysis_results['by_decade'][d]['total'] for d in decades]
    with_before = [analysis_results['by_decade'][d]['with_before'] for d in decades]
    with_after = [analysis_results['by_decade'][d]['with_after'] for d in decades]
    
    x = np.arange(len(decades))
    width = 0.25
    
    bars1 = ax3.bar(x - width, total_events, width, label='Total Events', color='lightblue', alpha=0.8)
    bars2 = ax3.bar(x, with_before, width, label='With Foreshocks', color='orange', alpha=0.8)
    bars3 = ax3.bar(x + width, with_after, width, label='With Aftershocks', color='green', alpha=0.8)
    
    ax3.set_xlabel('Decade')
    ax3.set_ylabel('Number of Events')
    ax3.set_title('Event Activity by Decade')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"{d}s" for d in decades])
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Scatter plot of before vs after counts
    ax4 = axes[1, 1]
    before_counts = [e['before_count'] for e in analysis_results['summary']['events']]
    after_counts = [e['after_count'] for e in analysis_results['summary']['events']]
    
    # Only plot events that have some activity
    active_events = [(b, a) for b, a in zip(before_counts, after_counts) if b > 0 or a > 0]
    if active_events:
        before_active, after_active = zip(*active_events)
        ax4.scatter(before_active, after_active, alpha=0.6, s=30, color='purple')
    
    ax4.set_xlabel('Foreshocks Count')
    ax4.set_ylabel('Aftershocks Count')
    ax4.set_title('Foreshocks vs Aftershocks')
    ax4.grid(True, alpha=0.3)
    
    # Add correlation info if there's enough data
    if len(active_events) > 1:
        corr = np.corrcoef(before_active, after_active)[0, 1]
        ax4.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax4.transAxes, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the visualization
    output_file = os.path.join(output_dir, 'earthquake_analysis_visualization.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nVisualization saved to: {output_file}")

def main():
    """Main analysis function."""
    event_analysis_dir = 'event_analysis'
    
    if not os.path.exists(event_analysis_dir):
        print(f"Error: {event_analysis_dir} directory not found!")
        print("Please run the extract_event_data.py script first.")
        return
    
    # Perform analysis
    analysis_results = analyze_event_data(event_analysis_dir)
    
    # Create visualizations
    try:
        create_visualization(analysis_results, event_analysis_dir)
    except Exception as e:
        print(f"Warning: Could not create visualizations: {e}")
        print("Analysis completed successfully, but visualization failed.")
    
    # Save detailed analysis results
    output_file = os.path.join(event_analysis_dir, 'detailed_analysis.json')
    
    # Convert results to JSON-serializable format
    serializable_results = {
        'analysis_date': datetime.now().isoformat(),
        'total_events': analysis_results['summary']['total_events_processed'],
        'events_with_foreshocks': len(analysis_results['events_with_before']),
        'events_with_aftershocks': len(analysis_results['events_with_after']),
        'events_with_both': len(analysis_results['events_with_both']),
        'top_foreshock_events': [{'event': e['event'], 'count': e['before_count']} for e in analysis_results['top_before'] if e['before_count'] > 0],
        'top_aftershock_events': [{'event': e['event'], 'count': e['after_count']} for e in analysis_results['top_after'] if e['after_count'] > 0],
        'decade_analysis': analysis_results['by_decade']
    }
    
    with open(output_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\nDetailed analysis saved to: {output_file}")
    print(f"\n=== Analysis Complete ===")
    print(f"Data for {analysis_results['summary']['total_events_processed']} major earthquake events has been extracted and analyzed.")
    print(f"Each event folder contains:")
    print(f"  - Event metadata (event_metadata.json)")
    print(f"  - Before event data (before_event.csv) - if foreshocks exist")
    print(f"  - After event data (after_event.csv) - if aftershocks exist")

if __name__ == "__main__":
    main()
