"""Generate publication-quality PDF figures for LaTeX embedding using Matplotlib."""
"""GENERATED USING AI"""
import json
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
# Use LaTeX-friendly settings for publication-quality figures
matplotlib.rcParams.update({
    'font.size': 14,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 20,
    'font.family': 'serif',
    'text.usetex': False,  # Set True if LaTeX is installed
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})


def generate_latex_figures(results_file: Path, output_dir: Path):
    """Generate separate PDF figures suitable for LaTeX embedding."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(results_file) as f:
        data = json.load(f)

    results = data['results']
    detectors = ['file', 'magika', 'polyfile', 'polydet']
    detector_labels = ['File', 'Magika', 'PolyFile', 'PolyDet']

    polyglots = [r for r in results if r.get('is_polyglot', True)]
    monoglots = [r for r in results if not r.get('is_polyglot', True)]

    # Calculate metrics
    detect_rates = []
    exact_rates = []
    fp_rates = []

    for name in detectors:
        positives = sum(1 for p in polyglots if p['detectors'][name]['is_polyglot'])
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

    for name in detectors:
        fp_count = sum(1 for r in monoglots if r['detectors'][name]['is_polyglot'])
        error_count = sum(1 for r in monoglots if r['detectors'][name].get('error'))
        valid_count = len(monoglots) - error_count
        fp = (fp_count / valid_count * 100) if valid_count > 0 else 0
        fp_rates.append(fp)

    # Build generator data
    by_generator = defaultdict(lambda: {det: {'poly': 0, 'exact': 0, 'total': 0} for det in detectors})
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

    generators = sorted([g for g in by_generator.keys() if g not in ('monoglot', 'source', '')])

    # === Figure 1: Bar chart for Recall, Exact Match, FP Rate ===
    fig1, ax1 = plt.subplots(figsize=(10, 5))

    x = np.arange(len(detectors))
    width = 0.25

    bars1 = ax1.bar(x - width, detect_rates, width, label='Recall', color='#2166ac', edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x, exact_rates, width, label='Exact Match', color='#4daf4a', edgecolor='black', linewidth=0.5)
    bars3 = ax1.bar(x + width, fp_rates, width, label='FP Rate', color='#d62728', edgecolor='black', linewidth=0.5)

    ax1.set_ylabel('Percentage (%)')
    ax1.set_xlabel('Detector')
    ax1.set_xticks(x)
    ax1.set_xticklabels(detector_labels)
    ax1.set_ylim(0, 105)
    ax1.legend(loc='upper right', frameon=True, fancybox=False, edgecolor='black')
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    fig1.savefig(output_dir / 'metrics_comparison.pdf', format='pdf')
    fig1.savefig(output_dir / 'metrics_comparison.png', format='png')
    plt.close(fig1)
    print(f"Generated: {output_dir / 'metrics_comparison.pdf'}")

    # === Figure 2: Heatmap for Recall by Generator ===
    def create_heatmap(data_key, title, filename):
        # Build matrix
        matrix = np.zeros((len(generators), len(detectors)))
        annotations = []

        for i, gen in enumerate(generators):
            row_annotations = []
            for j, det in enumerate(detectors):
                total = by_generator[gen][det]['total']
                value = by_generator[gen][det][data_key]
                rate = (value / total * 100) if total > 0 else 0
                matrix[i, j] = rate
                row_annotations.append(f'{value}/{total}\n{rate:.0f}%')
            annotations.append(row_annotations)

        fig, ax = plt.subplots(figsize=(8, max(6, len(generators) * 0.5)))

        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

        # Set ticks
        ax.set_xticks(np.arange(len(detectors)))
        ax.set_yticks(np.arange(len(generators)))
        ax.set_xticklabels(detector_labels)
        ax.set_yticklabels(generators)

        # Add text annotations
        for i in range(len(generators)):
            for j in range(len(detectors)):
                text_color = 'white' if matrix[i, j] < 40 or matrix[i, j] > 80 else 'black'
                ax.text(j, i, annotations[i][j],
                       ha='center', va='center', fontsize=10,
                       color=text_color, fontweight='bold')

        ax.set_xlabel('Detector')
        ax.set_ylabel('Generator')

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Detection Rate (%)')

        plt.tight_layout()
        fig.savefig(output_dir / f'{filename}.pdf', format='pdf')
        fig.savefig(output_dir / f'{filename}.png', format='png')
        plt.close(fig)
        print(f"Generated: {output_dir / f'{filename}.pdf'}")

    create_heatmap('poly', 'Recall by Generator', 'recall_heatmap')
    create_heatmap('exact', 'Exact Type Detection by Generator', 'exact_heatmap')

    # === Figure 3: Combined figure (optional, for single-page overview) ===
    fig_combined, axes = plt.subplots(3, 1, figsize=(10, 14),
                                       gridspec_kw={'height_ratios': [1, 1.5, 1.5]})

    # Subplot 1: Bar chart
    ax = axes[0]
    x = np.arange(len(detectors))
    width = 0.25

    bars1 = ax.bar(x - width, detect_rates, width, label='Recall', color='#2166ac', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x, exact_rates, width, label='Exact Match', color='#4daf4a', edgecolor='black', linewidth=0.5)
    bars3 = ax.bar(x + width, fp_rates, width, label='FP Rate', color='#d62728', edgecolor='black', linewidth=0.5)

    ax.set_ylabel('Percentage (%)')
    ax.set_xlabel('Detector')
    ax.set_xticks(x)
    ax.set_xticklabels(detector_labels)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', frameon=True, fancybox=False, edgecolor='black')
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title('(a) Recall and False Positive Rate', fontweight='bold', pad=10)

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 2),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    # Subplot 2 & 3: Heatmaps
    def add_heatmap(ax, data_key, title):
        matrix = np.zeros((len(generators), len(detectors)))
        annotations = []

        for i, gen in enumerate(generators):
            row_annotations = []
            for j, det in enumerate(detectors):
                total = by_generator[gen][det]['total']
                value = by_generator[gen][det][data_key]
                rate = (value / total * 100) if total > 0 else 0
                matrix[i, j] = rate
                row_annotations.append(f'{value}/{total}\n{rate:.0f}%')
            annotations.append(row_annotations)

        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

        ax.set_xticks(np.arange(len(detectors)))
        ax.set_yticks(np.arange(len(generators)))
        ax.set_xticklabels(detector_labels)
        ax.set_yticklabels(generators)

        for i in range(len(generators)):
            for j in range(len(detectors)):
                text_color = 'white' if matrix[i, j] < 40 or matrix[i, j] > 80 else 'black'
                ax.text(j, i, annotations[i][j],
                       ha='center', va='center', fontsize=9,
                       color=text_color, fontweight='bold')

        ax.set_xlabel('Detector')
        ax.set_ylabel('Generator')
        ax.set_title(title, fontweight='bold', pad=10)

        return im

    im2 = add_heatmap(axes[1], 'poly', '(b) Recall by Generator')
    im3 = add_heatmap(axes[2], 'exact', '(c) Exact Type Detection by Generator')

    # Add single colorbar
    fig_combined.subplots_adjust(right=0.85)
    cbar_ax = fig_combined.add_axes([0.88, 0.15, 0.03, 0.5])
    cbar = fig_combined.colorbar(im2, cax=cbar_ax)
    cbar.set_label('Detection Rate (%)')

    plt.tight_layout(rect=[0, 0, 0.85, 1])
    fig_combined.savefig(output_dir / 'combined_analysis.pdf', format='pdf')
    fig_combined.savefig(output_dir / 'combined_analysis.png', format='png')
    plt.close(fig_combined)
    print(f"Generated: {output_dir / 'combined_analysis.pdf'}")


if __name__ == "__main__":
    results_file = Path("../generated/detection_results.json")
    output_dir = Path("../generated/figures")
    generate_latex_figures(results_file, output_dir)
    print(f"\nAll figures saved to: {output_dir}")
