---
id: quality_control
name: Single-Cell Quality Control
description: |
  Standard quality control workflow for single-cell RNA-seq data.
  Includes filtering, normalization, and QC metric visualization.
tags: [qc, preprocessing, scanpy]
---

# Single-Cell Quality Control Workflow

Standard workflow for quality control of single-cell RNA-seq data using Scanpy.

## Prerequisites

```python
import scanpy as sc
import numpy as np
import matplotlib.pyplot as plt

sc.settings.verbosity = 3
```

## 1. Calculate QC Metrics

```python
# Calculate mitochondrial gene percentage
adata.var['mt'] = adata.var_names.str.startswith('MT-')  # Human
# adata.var['mt'] = adata.var_names.str.startswith('mt-')  # Mouse

# Calculate ribosomal gene percentage (optional)
adata.var['ribo'] = adata.var_names.str.startswith(('RPS', 'RPL'))  # Human

# Calculate hemoglobin genes (optional, for blood samples)
adata.var['hb'] = adata.var_names.str.match('^HB[^P]')  # Human

# Compute QC metrics
sc.pp.calculate_qc_metrics(
    adata, 
    qc_vars=['mt', 'ribo', 'hb'],
    percent_top=None, 
    log1p=False, 
    inplace=True
)
```

## 2. Visualize QC Metrics

```python
# Violin plots of key metrics
fig, axes = plt.subplots(1, 3, figsize=(12, 4))

sc.pl.violin(adata, 'n_genes_by_counts', ax=axes[0], show=False)
axes[0].set_title('Genes per Cell')

sc.pl.violin(adata, 'total_counts', ax=axes[1], show=False)
axes[1].set_title('UMI Counts per Cell')

sc.pl.violin(adata, 'pct_counts_mt', ax=axes[2], show=False)
axes[2].set_title('% Mitochondrial')

plt.tight_layout()
plt.savefig('qc_metrics_violin.png', dpi=150, bbox_inches='tight')
plt.savefig('qc_metrics_violin.pdf', bbox_inches='tight')
plt.show()
```

```python
# Scatter plots for threshold selection
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

sc.pl.scatter(adata, x='total_counts', y='n_genes_by_counts', 
              color='pct_counts_mt', ax=axes[0], show=False)
axes[0].set_xlabel('Total Counts')
axes[0].set_ylabel('Genes Detected')

sc.pl.scatter(adata, x='total_counts', y='pct_counts_mt',
              ax=axes[1], show=False)
axes[1].set_xlabel('Total Counts')
axes[1].set_ylabel('% Mitochondrial')

plt.tight_layout()
plt.savefig('qc_scatter.png', dpi=150, bbox_inches='tight')
plt.show()
```

## 3. Determine Filtering Thresholds

> [!IMPORTANT]
> Thresholds should be determined by examining the data distributions.
> The values below are typical starting points; adjust based on your data.

```python
# Print summary statistics
print("Summary statistics:")
print(f"  n_genes_by_counts: {adata.obs['n_genes_by_counts'].describe()}")
print(f"  total_counts: {adata.obs['total_counts'].describe()}")
print(f"  pct_counts_mt: {adata.obs['pct_counts_mt'].describe()}")

# Common thresholds (adjust based on plots)
min_genes = 200       # Minimum genes per cell
max_genes = 5000      # Maximum genes per cell (doublet filter)
min_counts = 500      # Minimum UMI counts
max_mt_pct = 20       # Maximum mitochondrial percentage
```

## 4. Apply Filters

```python
print(f"Cells before filtering: {adata.n_obs}")

# Filter cells
sc.pp.filter_cells(adata, min_genes=min_genes)
adata = adata[adata.obs['n_genes_by_counts'] < max_genes, :]
adata = adata[adata.obs['total_counts'] >= min_counts, :]
adata = adata[adata.obs['pct_counts_mt'] < max_mt_pct, :]

print(f"Cells after filtering: {adata.n_obs}")

# Filter genes (keep genes expressed in at least N cells)
sc.pp.filter_genes(adata, min_cells=3)
print(f"Genes after filtering: {adata.n_vars}")
```

## 5. Normalization

```python
# Store raw counts for later
adata.layers['counts'] = adata.X.copy()

# Normalize to 10,000 counts per cell
sc.pp.normalize_total(adata, target_sum=1e4)

# Log transform
sc.pp.log1p(adata)

# Store normalized data
adata.raw = adata
```

## 6. Identify Highly Variable Genes

```python
# Find highly variable genes
sc.pp.highly_variable_genes(
    adata,
    min_mean=0.0125,
    max_mean=3,
    min_disp=0.5,
    n_top_genes=2000,  # Alternative: specify number
    batch_key=None,    # Set if batch correction needed
)

# Visualize
sc.pl.highly_variable_genes(adata)
plt.savefig('hvg_selection.png', dpi=150, bbox_inches='tight')

print(f"Highly variable genes: {sum(adata.var['highly_variable'])}")
```

## 7. Post-QC Summary

```python
# Generate QC report
qc_summary = f"""
## Quality Control Summary

### Before Filtering
- Cells: {n_cells_before}
- Genes: {n_genes_before}

### Filtering Thresholds
- Min genes per cell: {min_genes}
- Max genes per cell: {max_genes}
- Min UMI counts: {min_counts}
- Max % mitochondrial: {max_mt_pct}%

### After Filtering
- Cells: {adata.n_obs}
- Genes: {adata.n_vars}
- Highly variable genes: {sum(adata.var['highly_variable'])}

### Normalization
- Normalized to 10,000 counts per cell
- Log1p transformed
"""
print(qc_summary)
```

## Optional: Doublet Detection

```python
# Using scrublet for doublet detection
import scrublet as scr

# Run on raw counts
scrub = scr.Scrublet(adata.layers['counts'])
doublet_scores, predicted_doublets = scrub.scrub_doublets()

adata.obs['doublet_score'] = doublet_scores
adata.obs['predicted_doublet'] = predicted_doublets

# Filter doublets
print(f"Predicted doublets: {sum(predicted_doublets)}")
adata = adata[~adata.obs['predicted_doublet'], :]
```

## Tips

> [!TIP]
> - Always visualize distributions before setting thresholds
> - Different tissue types may require different thresholds
> - For FFPE or low-quality samples, use more lenient thresholds
> - Consider batch effects when determining thresholds

> [!WARNING]
> Overly aggressive filtering can remove rare cell populations.
> Underly lenient filtering can introduce noise and doublets.
