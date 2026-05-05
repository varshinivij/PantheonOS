---
id: cellpose_segmentation
name: Cell Segmentation with Cellpose
description: |
  Cell and nucleus segmentation using Cellpose 3 and Cellpose-SAM.
  Covers model selection, GPU/CPU inference, image restoration,
  fine-tuning, and 3D segmentation.
tags: [segmentation, cellpose, cellpose-sam, nucleus, cell, 3d]
---

# Cell Segmentation with Cellpose

Cellpose is a generalist deep-learning model for cell and nucleus
segmentation. This skill covers Cellpose 3 (image restoration) and
Cellpose-SAM (highest accuracy).

## 1. Prerequisites

```bash
pip install "cellpose[gui]"  # includes GUI
# or minimal:
pip install cellpose
```

GPU is optional but recommended. Works on CPU, CUDA, and Apple MPS.

## 2. Model Selection

| Model | Description | When to use |
|-------|-------------|-------------|
| `cyto3` | Super-generalist (9 datasets) | Default for most cells |
| `nuclei` | Nuclear segmentation | Nuclei only (DAPI/Hoechst) |
| `cyto` | Original cytoplasm model | Legacy, use cyto3 instead |
| `cellpose_sam` | ViT-L SAM backbone + flow fields | Best accuracy, slower |

## 3. Basic Segmentation

```python
from cellpose import models

model = models.Cellpose(model_type='cyto3', gpu=True)

# Single image
masks, flows, styles, diams = model.eval(
    img,
    diameter=None,       # auto-estimate
    channels=[0, 0],     # [cytoplasm, nucleus] channel indices
    flow_threshold=0.4,
    cellprob_threshold=0,
)
```

**Channels parameter explained**:
- `[0, 0]` -- grayscale (single channel or average of channels)
- `[2, 1]` -- green = cytoplasm, red = nucleus
- `[0, 3]` -- grayscale cytoplasm, blue = nucleus
- `[1, 0]` -- red = cytoplasm, no nucleus channel
- The order is always `[cyto_channel, nuc_channel]`
- Channel indices: 0 = grayscale, 1 = red, 2 = green, 3 = blue

## 4. Batch Processing

```python
from cellpose import io

files = io.get_image_files('/path/to/images/')
masks_list = model.eval(
    files,
    diameter=None,
    channels=[0, 0],
    batch_size=8,
)
```

## 5. Image Restoration (Cellpose 3)

Cellpose 3 integrates image restoration (denoising, deblurring, upsampling)
directly into the segmentation pipeline:

```python
from cellpose import denoise

# Denoise before segmentation
dn_model = denoise.DenoiseModel(model_type='cyto3', gpu=True)
masks, flows, styles, diams = dn_model.eval(
    img,
    channels=[0, 0],
    diameter=None,
    # Restoration options:
    restore_type='denoise_cyto3',  # or 'deblur_cyto3', 'upsample_cyto3'
)
```

Available `restore_type` values:
- `denoise_cyto3` / `denoise_nuclei` -- remove Poisson/Gaussian noise
- `deblur_cyto3` / `deblur_nuclei` -- correct optical blur
- `upsample_cyto3` / `upsample_nuclei` -- super-resolve low-resolution images

## 6. Fine-Tuning on Custom Data

```python
from cellpose import models, io

model = models.CellposeModel(model_type='cyto3', gpu=True)
train_data, train_labels = io.load_train_test('/path/to/training/')

model.train(
    train_data, train_labels,
    channels=[0, 0],
    n_epochs=100,
    learning_rate=0.1,
    save_path='/path/to/model/',
)
```

Training data format: pairs of images and 16-bit label masks where each
cell has a unique integer ID. Place `_img.tif` and `_masks.tif` files in
the same directory.

## 7. 3D Segmentation

```python
masks_3d = model.eval(
    volume,          # (Z, Y, X) or (Z, Y, X, C)
    diameter=None,
    channels=[0, 0],
    do_3D=True,      # true 3D
    # or stitch_threshold=0.5 for 2D+stitch approach
)
```

Two approaches:
- `do_3D=True` -- true volumetric segmentation (slower, more accurate for
  isotropic voxels)
- `stitch_threshold=0.5` -- segment each Z-plane in 2D, then stitch masks
  across planes using IoU (faster, better for anisotropic data)

## 8. Using Cellpose-SAM

```python
model = models.Cellpose(model_type='cellpose_sam', gpu=True)
# Same API as above, just slower but more accurate
masks, flows, styles, diams = model.eval(
    img,
    diameter=None,
    channels=[0, 0],
)
```

Cellpose-SAM replaces the default U-Net backbone with a ViT-L encoder from
SAM while keeping Cellpose's flow-field prediction head. The API is identical
to standard Cellpose.

## Common Pitfalls

1. **diameter matters**: Wrong diameter = bad results. Use `diameter=None`
   for auto-estimation, or measure from a few cells in pixels. If cells are
   ~30px across, set `diameter=30`.

2. **channels confusion**: `[0,0]` = grayscale. `[2,1]` = green cytoplasm,
   red nucleus. `[0,3]` = grayscale + blue nucleus. The order is
   `[cyto_channel, nuc_channel]`, where 0 means grayscale.

3. **flow_threshold too strict**: Default 0.4 is good for most cases.
   Increase to 0.8 for over-segmentation cleanup, decrease for
   under-segmented images.

4. **GPU memory**: Large images may OOM. Use `tile=True` for automatic
   tiling, or resize images before segmentation.

5. **3D vs stitch**: `do_3D=True` is true volumetric but slow.
   `stitch_threshold=0.5` is faster (2D per-plane + z-stitching) and often
   sufficient, especially when Z-spacing is larger than XY pixel size.

6. **Cellpose-SAM speed**: ~3-5x slower than cyto3 due to ViT backbone.
   Use cyto3 for screening, cellpose_sam for final results.
