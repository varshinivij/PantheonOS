from typing import Any
import math

import numpy as np
from topact.countdata import CountMatrix


def log_fold_change(old, new, base=2):
    return math.log(new/old, base)


def expression_modulo_metadata(count_matrix: CountMatrix,
                               header: str
                               ) -> tuple[list[str], Any]:
    metadata_factors = list(set(count_matrix.metadata[header]))
    average_expressions = []
    for factor in metadata_factors:
        samples = list(count_matrix.match_by_metadata(header, factor))
        expression = np.array(count_matrix.expression(samples).sum(axis=0))
        average_expression = expression / len(samples)
        average_expressions.append(average_expression)
    total_expression = np.vstack(average_expressions)
    return metadata_factors, total_expression


def filter_genes(count_matrix: CountMatrix,
                 header: str,
                 expr_threshold: float,
                 diff_threshold: float
                 ) -> list[str]:
    _, expression = expression_modulo_metadata(count_matrix, header)
    highly_expressed = highly_expressed_columns(expression, expr_threshold)
    diff_expressed = differentially_expressed(expression, diff_threshold)
    to_keep = sorted(list(set(highly_expressed).intersection(set(diff_expressed))))
    genes_to_keep = [count_matrix.genes[i] for i in to_keep]
    count_matrix.filter_genes(genes_to_keep)
    return genes_to_keep


def highly_expressed_columns(array, threshold=0.0625/500):
    array = np.asarray(array)
    return np.nonzero(np.any(array >= threshold, axis=0))[0].tolist()


def differentially_expressed(array, threshold=0.5):
    array = np.asarray(array, dtype=float)
    averages = array.mean(axis=0)

    # log_fold_change(avg, val) > threshold  <=>  log(val/avg, base=2) > threshold
    # Use natural log and convert base by dividing by ln(2).
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = array / averages[None, :]
        lfc = np.log(ratio) / np.log(2)

    keep = np.any((array > 0) & (lfc > threshold), axis=0)
    return np.nonzero(keep)[0].tolist()
