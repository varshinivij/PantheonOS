---
id: cell_segmentation_index
name: Cell Segmentation Skills Index
description: |
  Cell and nucleus segmentation tools for microscopy images.
  Covers Cellpose, SAM-based methods, and other SOTA approaches.
tags: [segmentation, cellpose, sam, stardist, nucleus, cell]
---

# Cell & Nucleus Segmentation Skills

Instance segmentation tools for cells and nuclei in microscopy images.
Use the tool selection guide below to choose the right method, then load
the corresponding skill file for detailed usage.

## Tool Selection Guide

Use this decision flowchart to pick the best tool for your task:

| Goal | Recommended Tool |
|------|-----------------|
| Best overall accuracy | Cellpose-SAM (v4.x) |
| Fastest inference | InstanSeg |
| Low quality / noisy images | Cellpose 3 (image restoration) |
| Interactive annotation / 3D / tracking | micro-sam |
| Multiplexed (any number of channels) | InstanSeg (ChannelNet) |
| Round nuclei only | StarDist |
| Whole-cell (nucleus + membrane) | Mesmer / DeepCell |
| Spatial transcriptomics (transcript-level) | Segger |
| Fully automatic, no prompts needed | CellSAM |
| Joint segmentation + classification | CelloType |

> [!TIP]
> When in doubt, start with **Cellpose `cyto3`** for cells or **Cellpose `nuclei`**
> for nuclei. These are the most robust general-purpose defaults. Switch to
> Cellpose-SAM if you need the best possible accuracy and can tolerate slower
> inference.

## Available Skills

### Cellpose

General-purpose cell and nucleus segmentation using Cellpose 3 and
Cellpose-SAM. Covers model selection, GPU/CPU inference, image restoration,
fine-tuning, and 3D segmentation.

**Skill file**: [cellpose.md](./cellpose.md)

**When to use**:
- Default choice for most cell or nucleus segmentation tasks
- Need image denoising/deblurring before segmentation
- Fine-tuning on custom training data
- 3D volumetric segmentation

### SAM-Based Cell Segmentation

Cell segmentation using Segment Anything Model adaptations: CellSAM,
micro-sam, and SAMCell. Covers automatic and interactive segmentation modes.

**Skill file**: [sam_based.md](./sam_based.md)

**When to use**:
- Need interactive point/box-prompt segmentation in napari
- Fully automatic segmentation with no parameter tuning (CellSAM)
- 3D segmentation or cell tracking (micro-sam)
- Label-free brightfield/phase-contrast images (SAMCell)
