"""Generate interactive HTML visualization of detection results using Plotly."""

import json
from pathlib import Path
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd


def generate_html(results_file: Path, output_file: Path):
    """Generate interactive HTML dashboard with detection metrics and heatmaps."""
    with open(results_file) as f:
        data = json.load(f)

    results = data['results']
    detectors = ['file', 'magika', 'polyfile', 'polydet']

    polyglots = [r for r in results if r.get('is_polyglot', True)]
    monoglots = [r for r in results if not r.get('is_polyglot', True)]


    all_positives = {}
    all_fp = {}
    detect_rates = []
    exact_rates = []
    error_counts = []
    for name in detectors:
        #true positive = #detected as polyglots
        positives = sum(1 for p in polyglots if p['detectors'][name]['is_polyglot'])
        all_positives[name] = positives
        exact = sum(1 for p in polyglots
                    if p['detectors'][name]['is_polyglot']
                    and p['overt_format'] in p['detectors'][name]['detected_types']
                    and p['covert_format'] in p['detectors'][name]['detected_types']
                    and len(p['detectors'][name]['detected_types']) <= 2)
        error_count = sum(1 for p in polyglots if p['detectors'][name].get('error'))
        valid_count = len(polyglots) - error_count
        detect = (positives / valid_count * 100) if valid_count > 0 else 0
        exact_rate = (exact / valid_count * 100) if valid_count > 0 else 0
        detect_rates.append(detect)
        exact_rates.append(exact_rate)
        error_counts.append(error_count)
    fp_rates = []
    for name in detectors:
        #false positives
        fp_count = sum(1 for r in monoglots if r['detectors'][name]['is_polyglot'])
        all_fp[name] = fp_count
        error_count = sum(1 for r in monoglots if r['detectors'][name].get('error'))
        valid_count = len(monoglots) - error_count
        fp = (fp_count / valid_count * 100) if valid_count > 0 else 0
        fp_rates.append(fp)
  


    #build dict where we store by every detector by every generator fothe heatmpap both poly and exact
    by_generator = defaultdict(lambda: {det: {'poly': 0, 'exact' :0, 'total': 0} for det in detectors})
    for r in results:
        if r.get('is_polyglot'):
            gen = r['generator']
            covert = r['covert_format']
            overt = r['overt_format']
            for name in detectors:
                by_generator[gen][name]['total'] += 1
                if r['detectors'][name]['is_polyglot']:
                    by_generator[gen][name]['poly'] += 1
                types = r['detectors'][name]['detected_types']
                if overt in types and covert in types and len(types) <= 2:
                    by_generator[gen][name]['exact'] += 1

    generators = sorted([g for g in by_generator.keys() if g != 'monoglot' and g != 'source' and g != ''])

    # df for recall, exact rate, and fp rates combined
    metrics_df = pd.DataFrame({
        'Detector': detectors * 3,
        'Metric': ['Recall'] * len(detectors) + ['Exact Match'] * len(detectors) + ['FP Rate'] * len(detectors),
        'Value': detect_rates + exact_rates + fp_rates
    })

    # heatma df 
    heatmap_data = []
    heatmap_data_exact = []
    for gen in generators:
        for det in detectors:
            total = by_generator[gen][det]['total']
            poly = by_generator[gen][det]['poly']
            exact = by_generator[gen][det]['exact']
            rate = (poly / total * 100) if total > 0 else 0
            exact_rate = (exact / total * 100) if total > 0 else 0
            heatmap_data.append({
                'Generator': gen,
                'Detector': det,
                'Detection Rate (%)': rate,
                'Label': f'{poly}/{total}'
            })
            heatmap_data_exact.append({
                'Generator': gen,
                'Detector': det,
                'Detection Rate (%)': exact_rate,
                'Label': f'{exact}/{total}'
            })
    heatmap_df = pd.DataFrame(heatmap_data)
    heatmap_exact_df = pd.DataFrame(heatmap_data_exact)
    # subplot for the 3 graphs
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            "Recall and False Positive Rate",
            "Recall by Generator",
            "Exact Type Detection by Generator"
        ),
        specs=[[{"type": "bar"}], [{"type": "heatmap"}], [{"type": "heatmap"}]],
        vertical_spacing=0.1,
        row_heights=[0.2, 0.4, 0.4]
    )

    # display recall and fp rate using grouped bar
    fig_metrics = px.bar(
        metrics_df,
        x='Detector',
        y='Value',
        color='Metric',
        barmode='group',
        text_auto='.1f',
        color_discrete_map={'Recall': 'blue', 'Exact Match': 'green', 'FP Rate': 'red'}
    )
    fig_metrics.update_traces(texttemplate='%{y:.1f}%', textposition='outside')

    # add trace to subplot
    for trace in fig_metrics.data:
        fig.add_trace(trace, row=1, col=1)

    def create_trace(heatmap_df):
        #for heatmap
        #pivot df so have basically matrix of values and then the indexing->name for columns and rows (index)
        heatmap_pivot = heatmap_df.pivot(index='Generator', columns='Detector', values='Detection Rate (%)')
        #create label for each heatmap cell, the problem we pivot we lose label
        # there shoould be a easier way to do thsi but it works 
        label_pivot = heatmap_df.pivot(index='Generator', columns='Detector', values='Label')
        textarr = []
        for labelrow, valrow in zip(label_pivot.values, heatmap_pivot.values):
            rowtext = []
            for label, val in zip(labelrow, valrow):
                rowtext.append(f"{label}<br>{val:.1f}")
            textarr.append(rowtext)
        return go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns.tolist(),
            y=heatmap_pivot.index.tolist(),
            colorscale='RdYlGn',
            zmin=0,
            zmax=100,
            colorbar=dict(title='Detection Rate (%)', len=0.2, y=0.1),
            showscale=True,
            text=textarr,
            texttemplate='%{text}',
            textfont={"size": 10}
        )

    fig.add_trace(
        create_trace(heatmap_df),
        row=2, col=1
    )

    fig.add_trace(
        create_trace(heatmap_exact_df),
        row=3, col=1
    )
    # because adding trace can destroys
    fig.update_yaxes(title_text='Percentage (%)', row=1, col=1, range=[0, 100]) 
    fig.update_yaxes(title_text="Generator", row=2, col=1)
    fig.update_yaxes(title_text="Generator", row=3, col=1)
    fig.update_xaxes(title_text='Detector', row=1, col=1)
    fig.update_xaxes(title_text='Detector', row=2, col=1)
    fig.update_xaxes(title_text='Detector', row=3, col=1)
    fig.update_layout(
        height=2000,
        showlegend=True,
        legend=dict(yanchor='top', y=0.99, xanchor='right', x=1.08, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1), # adjusted for having it not inside the graph
        title_text=f"Polyglot Detection Analysis<br>Total files: {len(results)} | Timestamp: {data['timestamp']}",
        title_x=0.5,
        barmode='group'
    )
    fig.write_html(output_file, include_plotlyjs='cdn')

if __name__ == "__main__":
    results_file = Path("../generated/detection_results.json")
    output_file = Path("../generated/detection_visualization.html")
    generate_html(results_file, output_file)
    print(f"Generated: {output_file}")
