---
id: sam_cell_segmentation
name: SAM-Based Cell Segmentation
description: |
  Cell segmentation using Segment Anything Model (SAM) adaptations:
  CellSAM, micro-sam, and SAMCell. Covers automatic and interactive
  segmentation modes.
tags: [segmentation, sam, cellsam, micro-sam, interactive, foundation-model]
---

# SAM-Based Cell Segmentation

This skill covers cell segmentation tools built on the Segment Anything
Model (SAM), adapted for microscopy. These tools leverage SAM's powerful
vision transformer backbone with microscopy-specific fine-tuning.

## 1. Tool Selection

| Tool | Mode | 3D | Interactive | Best for |
|------|------|-----|-------------|----------|
| CellSAM | Fully automatic | No | No | Diverse cell types, spatial tx |
| micro-sam | Auto + interactive | Yes | Yes | Annotation, tracking, 3D |
| SAMCell | Automatic | No | No | Label-free brightfield |

## 2. CellSAM

CellSAM combines a CellFinder detection network (generates bounding-box
prompts automatically) with a fine-tuned SAM decoder for fully automatic
cell segmentation.

### Installation

```bash
pip install cellsam
```

### Basic Usage

```python
from cellsam import segment_cellular_image

masks = segment_cellular_image(
    img,
    device='cuda',
    # CellFinder auto-generates bounding box prompts
)
```

> [!TIP]
> CellSAM is also available as a web app at cellsam.deepcell.org and as a
> napari plugin, making it accessible without writing any code.

## 3. micro-sam

micro-sam provides both automatic instance segmentation and interactive
annotation through a napari plugin. It supports 2D, 3D, and time-series
data with microscopy-specialized SAM models.

### Installation

```bash
pip install micro_sam
```

### Automatic Instance Segmentation (AIS)

```python
from micro_sam.automatic_segmentation import automatic_instance_segmentation

masks = automatic_instance_segmentation(
    img,
    model_type="vit_b_lm",  # light microscopy generalist
    # or "vit_b_em_organelles" for electron microscopy
)
```

Available model types:
- `vit_b_lm` -- light microscopy generalist (fluorescence, phase contrast)
- `vit_b_em_organelles` -- electron microscopy organelle segmentation
- `vit_l_lm` -- larger ViT-L model for light microscopy (more accurate, slower)

### Interactive Segmentation (napari)

```bash
# Launch napari plugin
micro_sam.napari
```

Click points or draw boxes on cells for instant segmentation. Fine-tune
on your data through the napari interface for domain-specific adaptation.

### 3D Segmentation

```python
from micro_sam.automatic_segmentation import automatic_instance_segmentation

masks_3d = automatic_instance_segmentation(
    volume,
    model_type="vit_b_lm",
    ndim=3,
)
```

micro-sam handles 3D segmentation by extending SAM's 2D predictions across
slices with a specialized decoder, producing volumetric instance masks.

### Cell Tracking (Time-Series)

micro-sam also supports tracking cells across time points in timelapse
data, linking segmented instances frame-to-frame through the interactive
napari interface.

## 4. SAMCell (Label-Free)

SAMCell is designed for label-free imaging modalities (brightfield, phase
contrast, DIC) where fluorescent markers are not available.

### Installation

```bash
pip install samcell
```

### Basic Usage

```python
from samcell import SAMCellPredictor

predictor = SAMCellPredictor()
masks = predictor.predict(brightfield_img)
```

SAMCell is optimized for transmitted-light microscopy where cell boundaries
are low-contrast and traditional thresholding methods fail.

## Common Pitfalls

1. **General SAM is not for cells**: Vanilla SAM/SAM2/SAM3 perform poorly
   on microscopy data (AP ~0.27 vs specialized tools ~0.54). Always use
   microscopy-adapted versions (CellSAM, micro-sam, SAMCell).

2. **micro-sam model choice**: Use `vit_b_lm` for light microscopy,
   `vit_b_em_organelles` for EM. Using the wrong model type produces
   significantly degraded results.

3. **CellSAM on unusual morphologies**: CellFinder may miss very small or
   densely packed cells. Check detection quality before trusting the output
   masks, especially on crowded fields of view.

4. **GPU memory**: SAM ViT models are large (~400MB+ weights). ViT-H
   requires 16GB+ VRAM. Use ViT-B or ViT-T variants for smaller GPUs,
   or run on CPU with slower inference.

5. **Multi-channel images**: micro-sam averages multi-channel inputs to a
   single channel, losing channel-specific information. For multiplexed or
   highly multi-channel data, consider InstanSeg's ChannelNet instead,
   which handles arbitrary channel counts natively.
