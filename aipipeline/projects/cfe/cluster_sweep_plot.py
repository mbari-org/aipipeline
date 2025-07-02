import os
import json
import re
import matplotlib.pyplot as plt

root_dir = '/Users/dcline/Dropbox/data/ISIIS/hawaii/'
total_clusters = []
cluster_coverages = []
annotations = []

def parse_coverage(coverage_str):
    """Extract float value from string like '0.63 (63.46%)'"""
    match = re.match(r"([\d.]+)", coverage_str)
    return float(match.group(1)) if match else None

# Traverse directory and extract fields
for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith('.json'):
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    stats = data.get('statistics', {})
                    params = data.get('dataset', {}).get('clustering_parameters', {})

                    total = stats.get('total_clusters')
                    coverage = stats.get('cluster_coverage')
                    mcs = params.get('min_cluster_size')
                    ms = params.get('min_samples')
                    alpha = params.get('alpha')
                    epsilon = params.get('cluster_selection_epsilon')

                    if all(v is not None for v in [total, coverage, mcs, ms, alpha, epsilon]):
                        cov_value = parse_coverage(coverage)
                        if cov_value is not None:
                            total_clusters.append(total)
                            cluster_coverages.append(cov_value)
                            annotations.append(
                                f"mcs={mcs}, ms={ms}, α={alpha}, ε={epsilon}"
                            )
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

# Plotting
plt.figure(figsize=(14, 8))
plt.scatter(total_clusters, cluster_coverages, alpha=0.7)

# Annotate each point with rotated labels
for x, y, label in zip(total_clusters, cluster_coverages, annotations):
    plt.annotate(
        label,
        (x, y),
        fontsize=14,  # Increased font size
        alpha=0.6,
        rotation=30,
        rotation_mode='anchor',
        ha='left',
        va='bottom'
    )

plt.xlabel("Total Clusters", fontsize=18)
plt.ylabel("Cluster Coverage", fontsize=18)
plt.title("Total Clusters vs Cluster Coverage with Clustering Parameters\n Hawaii 2025 ISIIS", fontsize=20)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.grid(True)
plt.tight_layout()

# Save figure
output_path = "cluster_vs_coverage_with_params_hawaii2025.png"
plt.savefig(output_path, dpi=300)
print(f"Figure saved to {output_path}")

# Show plot
plt.show()