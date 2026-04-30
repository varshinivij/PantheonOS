---
id: spatial_skills_index
name: Spatial Omics Skills Index
description: |
  Skills for spatial transcriptomics analysis including single-cell to spatial
  mapping (MOSCOT), 3D visualization (PyVista), and related spatial workflows.
tags: [spatial, mapping, 3d, visualization, moscot, pyvista]
---

# Spatial Omics Skills

Skills for spatial transcriptomics data analysis, mapping, and visualization.

## Available Skills

### Single-Cell to Spatial Mapping

Map scRNA-seq to spatial data using optimal transport (MOSCOT) for gene
imputation and cell type transfer.

**Skill file**: [single_cell_spatial_mapping.md](./single_cell_spatial_mapping.md)

**When to use**:
- You have paired scRNA-seq and spatial transcriptomics data
- You want to impute genes not measured in the spatial modality
- You want to transfer cell type annotations to spatial coordinates

### 3D Spatial Data Visualization

Interactive 3D visualization and rotating GIF animations for spatial data
with PyVista.

**Skill file**: [visualize_3d_spatial.md](./visualize_3d_spatial.md)

**When to use**:
- Your spatial data has 3D coordinates
- You want to visualize gene expression or cell types in 3D
- You want to create rotating GIF animations

### Spatial 3D Slice Alignment (Spateo)

Align serial spatial transcriptomics sections into a 3D volume using
Spateo morpho_align with pairwise rigid registration.

**Skill file**: [spatial_3d_alignment.md](./spatial_3d_alignment.md)

**When to use**:
- You have serial tissue sections that need 3D reconstruction
- You want morphology + expression-based slice registration
- You need rigid transformations between consecutive sections

### Spatial Cell-Cell Interaction (Spateo LR)

Infer ligand-receptor interactions between spatially adjacent cell types
using Spateo's two-group CCI analysis with permutation testing.

**Skill file**: [spatial_cci.md](./spatial_cci.md)

**When to use**:
- You want to find LR interactions constrained by spatial proximity
- You have imputed spatial data with mapped cell type labels
- You want to compare spatial vs non-spatial CCI results
