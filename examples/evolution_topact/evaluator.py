"""
Evaluator for TopACT Evolution.

Measures:
1. Speed (40% weight): Execution time of the full TopACT pipeline
2. Fidelity (60% weight): Output consistency with the original implementation
   - If fidelity < 90%, fidelity score is set to 0

The evaluator runs the complete TopACT pipeline:
  load data -> train SVM -> build spatial grid -> multiscale classify -> annotate
and compares the annotation output to a pre-computed reference.
"""

import multiprocessing
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np

# Use fork start method to avoid spawn issues in subprocess contexts (macOS)
try:
    multiprocessing.set_start_method("fork")
except RuntimeError:
    pass  # Already set


def evaluate(workspace_path: str) -> Dict[str, Any]:
    """
    Evaluate an evolved TopACT implementation.

    Args:
        workspace_path: Path to workspace containing the evolved topact/ package.

    Returns:
        Dictionary with metrics and fitness_weights.
    """
    # Clear cached topact modules to force reload from workspace
    for key in list(sys.modules.keys()):
        if key.startswith("topact"):
            del sys.modules[key]

    # Import topact from workspace (sys.path[0] is already workspace_path)
    try:
        from scipy import io
        import pandas as pd
        from topact.countdata import CountMatrix
        from topact.classifier import SVCClassifier, train_from_countmatrix
        from topact import spatial
    except Exception as e:
        return {"function_score": 0.0, "error": f"Import failed: {e}"}

    # Get data directory
    data_dir_str = os.environ.get("TOPACT_DATA_DIR", "")
    if not data_dir_str:
        return {"function_score": 0.0, "error": "TOPACT_DATA_DIR not set"}
    data_dir = Path(data_dir_str)

    # Load reference output and input data
    try:
        reference = np.loadtxt(data_dir / "reference_output.txt")

        mtx = io.mmread(str(data_dir / "scmatrix.mtx")).T
        with open(data_dir / "scgenes.txt") as f:
            genes = [line.rstrip() for line in f]
        with open(data_dir / "sclabels.txt") as f:
            labels = [line.rstrip() for line in f]

        df = pd.read_csv(data_dir / "spatial.csv")
    except Exception as e:
        return {"function_score": 0.0, "error": f"Data loading failed: {e}"}

    # Run the full TopACT pipeline and measure execution time
    try:
        start_time = time.time()

        # 1. Create count matrix and train classifier
        sc = CountMatrix(mtx, genes=genes)
        sc.add_metadata("celltype", labels)
        clf = SVCClassifier()
        train_from_countmatrix(clf, sc, "celltype")

        # 2. Build spatial grid
        sd = spatial.CountGrid.from_coord_table(
            df, genes=genes, count_col="counts", gene_col="gene"
        )

        # 3. Classify at multiple scales
        outfile = os.path.join(workspace_path, "outfile.npy")
        sd.classify_parallel(
            clf, min_scale=3, max_scale=9, num_proc=1, outfile=outfile
        )

        # 4. Extract annotations
        confidence_mtx = np.lib.format.open_memmap(outfile, mode="r")
        annotations = spatial.extract_image(confidence_mtx, 0.5)

        execution_time = time.time() - start_time

    except Exception as e:
        return {"function_score": 0.0, "error": f"Pipeline execution failed: {e}"}

    # Compute metrics
    try:
        # Fidelity: percentage of matching pixels
        total_pixels = reference.size
        matching_pixels = np.sum(annotations == reference)
        fidelity_pct = float(matching_pixels / total_pixels * 100)

        # Apply threshold: fidelity < 90% => score = 0
        if fidelity_pct < 90:
            fidelity_score = 0.0
        else:
            fidelity_score = fidelity_pct / 100.0

        # Speed score: higher is better (faster execution)
        speed_score = 1.0 / (1.0 + execution_time)

        return {
            "speed_score": speed_score,
            "fidelity_score": fidelity_score,
            "execution_time": execution_time,
            "fidelity_pct": fidelity_pct,
            "fitness_weights": {
                "speed_score": 0.4,
                "fidelity_score": 0.6,
            },
        }

    except Exception as e:
        return {"function_score": 0.0, "error": f"Metric computation failed: {e}"}
