"""Classes and methods for array-based spatial transcriptomics analysis."""

import itertools
from typing import Iterable, Iterator, Sequence, cast
from multiprocessing import Process, Queue
from warnings import simplefilter

import numpy as np
import numpy.typing as npt
from scipy import sparse
from topact.countdata import CountTable
from topact.classifier import Classifier, SVCClassifier
from topact import densetools


def combine_coords(coords: Iterable[int]) -> str:
    """Combines a tuple of ints into a unique string identifier."""
    return ','.join(map(str, coords))


def split_coords(ident: str) -> tuple[int, ...]:
    """Splits a unique identifier into its corresponding coordinates.

    Args:
        ident: A string of the form '{x1},{x2},...,{xn}'.

    Returns:
        A tuple of integers (x1, x2, ..., xn).
    """
    return tuple(map(int, ident.split(','))) if ident else ()


def first_coord(ident: str) -> int:
    """Obtains the first coordinate from a unique identifier.

    Args:
        ident: A string of the form '{x1},{x2},...,{xn}' where n>=1.

    Returns:
        The integer x1.
    """
    return split_coords(ident)[0]


def second_coord(ident: str) -> int:
    """Obtains the first coordinate from a unique identifier.

    Args:
        ident: A string of the form '{x1},{x2},...,{xn}' where n >= 2.

    Returns:
        The integer x2.
    """
    return split_coords(ident)[1]


def cartesian_product(x: npt.ArrayLike, y: npt.ArrayLike) -> npt.NDArray:
    """Computes the cartesian products of two 1-d vectors.

    Args:
        x: The first vector
        y: The second vector

    Returns:
        An array of shape (len(x) * len(y), 2) whose rows are precisely all
        possible tuples with first value in x and second value in y.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    return np.transpose([np.tile(x, len(y)),
                         np.repeat(y, len(x))])


def square_nbhd(point: tuple[int, int],
                scale: int,
                x_range: tuple[int, int],
                y_range: tuple[int, int]
                ) -> Iterator[tuple[int, int]]:
    """All coordinates in a square neighbourhood about a point.

    Args:
        point: the (x,y) coordinates of the point
        scale: the radius of the square
        x_range: the least and greatest acceptable x values
        y_range: the least and greated acceptable y values

    Yields:
        All tuples (i,j) satisfying the following:
            - x_range[0] <= i <= x_range[1]
            - y_range[0] <= j <= y_range[1]
            - d(x,i) <= scale
            - d(y,j) <= scale
    """
    x, y = point
    x_min, x_max = x_range
    y_min, y_max = y_range
    x_min = max(x_min, x - scale)
    x_max = min(x_max, x + scale)
    y_min = max(y_min, y - scale)
    y_max = min(y_max, y + scale)
    return itertools.product(range(x_min, x_max+1), range(y_min, y_max+1))


def square_nbhd_vec(point: tuple[int, int],
                    scale: int,
                    x_range: tuple[int, int],
                    y_range: tuple[int, int]
                    ) -> npt.NDArray:
    """Returns a 2D array of all coords in a square nbhd about a point

    Args:
        point: the (x,y) coordinates of the point
        scale: the radius of the square
        x_range: the least and greatest acceptable x values
        y_range: the least and greated acceptable y values

    Returns:
        An array A of shape (n*m, 2) where n = x_range[1] - x_range[0] + 1
        and m = y_range[1] - y_range[0] + 1, whose rows are precisely the
        elements of square_nbhd(point, scale, x_range, y_range).
    """
    x, y = point
    x_min, x_max = x_range
    y_min, y_max = y_range
    if x_max < x_min or y_max < y_min:
        return np.empty((0,2))
    x_min = max(x_min, x - scale)
    x_max = min(x_max, x + scale)
    y_min = max(y_min, y - scale)
    y_max = min(y_max, y + scale)
    return cartesian_product(np.arange(x_min, x_max + 1),
                             np.arange(y_min, y_max + 1))


def extract_classifications(confidence_matrix: npt.NDArray,
                            threshold: float
                            ) -> dict[tuple[int, int], int]:
    """Extracts a dictionary of all spot classifications given the threshold.

    Args:
        confidence_matrix:
            A matrix X such that X[i, j, s, c] is the confidence that the
            cell type of spot (i, j) is c at scale s.
        threshold:
            The confidence threshold.

    Returns:
        A dictionary d such that (i, j) is in d if and only if there is some
        scale s and cell type c so that confidence_matrix[i, j, s, c] >= threshold.
        Moreover, d[x,y] is the value of c corresponding to the lowest such
        value of s.

    Notes:
        If multiple classes exceed the threshold at the first qualifying scale,
        the smallest class index is chosen (matches numpy argmax tie-breaking).
    """
    hit = confidence_matrix >= threshold  # (H, W, S, C)
    has_any = hit.any(axis=3)  # (H, W, S)
    any_pixel = has_any.any(axis=2)  # (H, W)

    if not np.any(any_pixel):
        return {}

    # First scale index where any class hits threshold, per pixel
    first_s = np.argmax(has_any, axis=2)  # (H, W), valid only where any_pixel True

    # For pixels that qualify, find the (lowest) class index at that first scale
    coords = np.argwhere(any_pixel)  # (K, 2) with rows [i, j]
    i = coords[:, 0]
    j = coords[:, 1]
    s = first_s[i, j]
    hit_at_first = hit[i, j, s, :]  # (K, C) boolean
    cell_type = np.argmax(hit_at_first, axis=1).astype(int, copy=False)

    return {(int(ii), int(jj)): int(ct) for ii, jj, ct in zip(i, j, cell_type)}


def extract_image(confidence_matrix: npt.NDArray,
                  threshold: float
                  ) -> npt.NDArray:
    classifications = extract_classifications(confidence_matrix, threshold)

    image = np.empty(confidence_matrix.shape[:2])
    image[:] = np.nan

    for (i, j), c in classifications.items():
        image[i, j] = c

    return image


class ExpressionGrid:
    """A spatial grid equipped with gene expressions.

    An ExpressionGrid encapsulates a 2D grid. For each coordinate (x,y) in the
    grid, we have a corresponding gene expression vector where each entry
    counts the number of reads of its corresponding gene.

    Attributes:
        x_min: The smallest x coordinate in the grid.
        y_min: The smallest y coordinate in the grid.
        x_max: The largest x coordinate in the grid.
        y_max: The largest y coordinate in the grid.
        height: The height of the grid.
        width: The width of the grid.
    """
    def __init__(self,
                 table,
                 genes: Sequence[str],
                 gene_col: str = "gene",
                 count_col: str = "count"
                 ):
        """Inits grid with expression readingsfrom a dataframe.

        Args:
            table: A dataframe of spot-level gene counts.
                Each row in the dataframe corresponds to a reading of one
                gene at one spot.
                Columns:
                    x: The x coordinate of the reading.
                    y: The y coordinate of the reading.
                    {gene_col}: The gene detected by the reading.
                    {count_col}: The number of transcripts measured.
            genes:
                A full list of all genes under consideration, in order. This
                should match the list of genes used for other CountData
                intended to be compared with this sample.
            gene_col:
                A string labelling the column containing gene names.
            count_col:
                A string labelling the column containing transcript counts.
        """
        self.x_min, self.x_max = table.x.min(), table.x.max()
        self.y_min, self.y_max = table.y.min(), table.y.max()
        self.height: int = self.x_max - self.x_min + 1
        self.width: int = self.y_max - self.y_min + 1

        # Cache for per-scale box bounds (x1,x2,y1,y2) and (+1) variants
        self._box_bounds_cache: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}

        # Optional cached dense cube / integral image for all genes (fast path).
        self._dense_X: npt.NDArray | None = None
        self._integral_X: npt.NDArray | None = None
        self._integral_ready: bool = False

        gene_to_idx = {g: i for i, g in enumerate(genes)}
        num_genes = len(genes)

        # Build sparse matrix via COO (much faster than lil assignment)
        xs = table.x.to_numpy()
        ys = table.y.to_numpy()
        flat = self.width * (xs - self.x_min) + (ys - self.y_min)

        # Vectorized gene mapping via pandas Series.map (avoids Python-level loop)
        gene_idx = table[gene_col].map(gene_to_idx).to_numpy(copy=False)
        if np.isnan(gene_idx).any():
            unknown = table.loc[np.isnan(gene_idx), gene_col].unique()
            raise ValueError(f"Unknown genes encountered in table[{gene_col}]: {unknown}")
        gene_idx = gene_idx.astype(np.int32, copy=False)

        data = table[count_col].to_numpy(dtype=np.float32, copy=False)

        matrix = sparse.coo_matrix((data, (flat, gene_idx)),
                                   shape=(int(self.height) * int(self.width), int(num_genes)))
        self.matrix = matrix.tocsc()
        self.num_genes = cast(int, num_genes)

    def rows(self) -> range:
        """Returns a range of all row indices in the grid."""
        return range(self.x_min, self.x_max+1)

    def cols(self) -> range:
        """Returns a range of all column indices in the grid."""
        return range(self.y_min, self.y_max+1)

    def _flatten_coords(self, i: int, j: int) -> int:
        return self.width * (i - self.x_min) + (j - self.y_min)

    def _flatten_coords_vec(self, coords) -> npt.ArrayLike:
        return ((self.width, 1) * (coords - (self.x_min, self.y_min))).sum(axis=1)

    def expression(self, *coords: tuple[(int, int)]) -> sparse.spmatrix:
        """The total expression at these coordinates in the grid"""
        return self.matrix[list(map(lambda p: self._flatten_coords(*p),
                                    coords
                                    ))].sum(axis=0)

    def expression_vec(self, coords: npt.NDArray) -> sparse.spmatrix:
        flattened = self._flatten_coords_vec(coords)
        return self.matrix[flattened].sum(axis=0)

    def square_nbhd(self,
                    i: int,
                    j: int,
                    scale: int
                    ) -> Iterator[tuple[int, int]]:
        """All coordinates (x,y) in the grid such that d(x,i), d(y-j) <= scale"""
        return square_nbhd((i, j), scale, (self.x_min, self.x_max),
                           (self.y_min, self.y_max))

    def square_nbhd_vec(self, i: int, j: int, scale: int) -> npt.NDArray:
        return square_nbhd_vec((i, j), scale, (self.x_min, self.x_max),
                               (self.y_min, self.y_max))

    def _ensure_integral_X(self, max_bytes: int = 512 * 1024 * 1024) -> bool:
        """Ensure a cached summed-area table for all genes exists.

        Builds dense X (H,W,G) and its integral image P (H+1,W+1,G) once,
        guarded by a memory threshold.

        Returns:
            True if the integral image is available after the call.
        """
        if self._integral_ready and self._integral_X is not None:
            return True

        H = int(self.height)
        W = int(self.width)
        G = int(self.num_genes)

        needed = (H + 1) * (W + 1) * G * 4  # float32
        if needed > max_bytes:
            return False

        # Densify in float32 directly (avoid float64 materialization).
        X = self.matrix.astype(np.float32, copy=False).toarray().reshape(H, W, G)
        P = np.zeros((H + 1, W + 1, G), dtype=np.float32)
        P[1:, 1:, :] = X
        np.cumsum(P, axis=0, out=P)
        np.cumsum(P, axis=1, out=P)

        self._dense_X = X
        self._integral_X = P
        self._integral_ready = True
        return True

    def _get_box_bounds(self, scale: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get (x1,x2,y1,y2,x2p1,y2p1) bounds arrays for a given scale (cached)."""
        s = int(scale)
        cached = self._box_bounds_cache.get(s)
        if cached is not None:
            return cached

        H = int(self.height)
        W = int(self.width)
        xs = np.arange(H)
        ys = np.arange(W)
        x1 = np.maximum(0, xs - s)
        x2 = np.minimum(H - 1, xs + s)
        y1 = np.maximum(0, ys - s)
        y2 = np.minimum(W - 1, ys + s)

        x2p1 = x2 + 1
        y2p1 = y2 + 1

        self._box_bounds_cache[s] = (x1, x2, y1, y2, x2p1, y2p1)
        return x1, x2, y1, y2, x2p1, y2p1

    def _neighborhood_sums_for_centers(self,
                                       scale: int,
                                       centers_flat: npt.NDArray,
                                       _totals_integral: npt.NDArray | None = None
                                       ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        """Compute neighbourhood sums only for an explicit list of centers.

        Args:
            scale: Neighborhood radius.
            centers_flat: 1D array of flattened indices into the HxW grid.
            _totals_integral: Optional precomputed (H+1, W+1) integral image of
                total transcript counts per spot.

        Returns:
            coords: Absolute (x,y) coords, shape (K,2).
            exprs: Neighborhood-summed expression, shape (K,G).
            totals_supported: Neighborhood total transcript counts, shape (K,).
            supported_flat: Flattened indices for returned coords (subset of centers_flat).
        """
        H = int(self.height)
        W = int(self.width)
        G = int(self.num_genes)

        centers_flat = np.asarray(centers_flat)
        if centers_flat.size == 0:
            empty_coords = np.empty((0, 2), dtype=int)
            return (empty_coords,
                    np.empty((0, G), dtype=np.float32),
                    np.empty((0,), dtype=np.float32),
                    np.empty((0,), dtype=np.int64))

        coords, exprs, totals_supported, supported_flat = self._neighborhood_sums_for_centers_nocoords(
            scale,
            centers_flat,
            _totals_integral=_totals_integral
        )
        return coords, exprs, totals_supported, supported_flat

    def _neighborhood_sums_for_centers_nocoords(self,
                                                scale: int,
                                                centers_flat: npt.NDArray,
                                                _totals_integral: npt.NDArray | None = None
                                                ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        """Compute neighbourhood sums for given centers without unnecessary coords work.

        Returns:
            coords: Absolute (x,y) coords, shape (K,2).
            exprs: Neighborhood-summed expression, shape (K,G).
            totals_supported: Neighborhood total transcript counts, shape (K,).
            supported_flat: Flattened indices for returned coords (subset of centers_flat).
        """
        H = int(self.height)
        W = int(self.width)
        G = int(self.num_genes)

        centers_flat = np.asarray(centers_flat)
        if centers_flat.size == 0:
            empty_coords = np.empty((0, 2), dtype=int)
            return (empty_coords,
                    np.empty((0, G), dtype=np.float32),
                    np.empty((0,), dtype=np.float32),
                    np.empty((0,), dtype=np.int64))

        # Bounds vectors cached per scale
        x1, _, y1, _, x2p1, y2p1 = self._get_box_bounds(scale)

        # Totals integral image (exact, fidelity-safe)
        if _totals_integral is None:
            totals_flat_all = np.asarray(self.matrix.sum(axis=1)).reshape(-1)
            T = totals_flat_all.reshape(H, W)
            S = np.pad(np.cumsum(np.cumsum(T, axis=0), axis=1),
                       ((1, 0), (1, 0)),
                       mode='constant')
        else:
            S = _totals_integral

        centers_flat_i64 = centers_flat.astype(np.int64, copy=False)
        rx_all = (centers_flat_i64 // W).astype(np.int64, copy=False)
        cy_all = (centers_flat_i64 % W).astype(np.int64, copy=False)

        xa_all = x2p1[rx_all]
        xb_all = x1[rx_all]
        ya_all = y2p1[cy_all]
        yb_all = y1[cy_all]

        totals_all = (S[xa_all, ya_all] - S[xb_all, ya_all] - S[xa_all, yb_all] + S[xb_all, yb_all]).astype(np.float32, copy=False)

        supported = totals_all > 0
        if not np.any(supported):
            empty_coords = np.empty((0, 2), dtype=int)
            return (empty_coords,
                    np.empty((0, G), dtype=np.float32),
                    np.empty((0,), dtype=np.float32),
                    np.empty((0,), dtype=np.int64))

        rx = rx_all[supported]
        cy = cy_all[supported]
        xa = xa_all[supported]
        xb = xb_all[supported]
        ya = ya_all[supported]
        yb = yb_all[supported]
        totals_supported = totals_all[supported]
        supported_flat = centers_flat_i64[supported]

        K = int(rx.shape[0])
        coords = np.empty((K, 2), dtype=int)
        coords[:, 0] = rx + int(self.x_min)
        coords[:, 1] = cy + int(self.y_min)

        # Fast path: reuse cached integral image for all genes, if available
        if self._integral_X is not None:
            P = self._integral_X
            exprs = (P[xa, ya, :] - P[xb, ya, :] - P[xa, yb, :] + P[xb, yb, :])
            return coords, exprs.astype(np.float32, copy=False), totals_supported, supported_flat

        # --- Fallback: chunk genes; reuse buffer to reduce allocations ---
        target_bytes = 128 * 1024 * 1024  # ~128MB
        bytes_per_value = 4  # float32
        denom = max(1, H * W * bytes_per_value)
        chunk_genes = max(1, min(G, target_bytes // denom))

        exprs = np.empty((K, G), dtype=np.float32)

        # Pre-allocate padded integral buffer once at max chunk size.
        P_big = np.empty((H + 1, W + 1, int(chunk_genes)), dtype=np.float32)

        for g0 in range(0, G, chunk_genes):
            g1 = min(G, g0 + chunk_genes)
            cg = int(g1 - g0)

            # Densify chunk in float32 directly.
            X_chunk = self.matrix[:, g0:g1].astype(np.float32, copy=False).toarray().reshape(H, W, cg)

            P_view = P_big[:, :, :cg]
            P_view.fill(0.0)
            P_view[1:, 1:, :] = X_chunk
            np.cumsum(P_view, axis=0, out=P_view)
            np.cumsum(P_view, axis=1, out=P_view)

            chunk_sums = (P_view[xa, ya, :] - P_view[xb, ya, :] - P_view[xa, yb, :] + P_view[xb, yb, :])
            exprs[:, g0:g1] = chunk_sums

        return coords, exprs, totals_supported, supported_flat

    def neighborhood_sums_all_spots(self,
                                    scale: int,
                                    mask: npt.NDArray | None = None,
                                    _totals_integral: npt.NDArray | None = None
                                    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
        """Compute square-neighborhood gene expression sums for all spots.

        Uses summed-area tables (integral images) to compute exact box sums for
        every center at the given scale, with edge clipping.

        If mask is provided, only masked-in spots are considered. Additionally,
        spots whose neighborhood total transcript count is 0 are skipped (to
        avoid unnecessary classification), preserving output semantics (those
        remain unclassified/NaN in the caller).

        Args:
            scale: The neighborhood radius s (box size (2s+1)x(2s+1)).
            mask: Optional boolean array of shape (height, width).

        Returns:
            coords:
                Absolute coordinates array of shape (K, 2) with columns (x, y).
            exprs:
                Neighborhood-summed expression array of shape (K, G).
            totals_supported:
                Neighborhood total transcript counts for each returned coord,
                shape (K,).
        """
        H = int(self.height)
        W = int(self.width)

        if mask is None:
            centers_flat = np.arange(H * W, dtype=np.int64)
        else:
            if mask.shape != (H, W):
                raise ValueError(f"mask has shape {mask.shape} but expected {(H, W)}")
            centers_flat = np.flatnonzero(mask.astype(bool, copy=False).ravel())

        coords, exprs, totals_supported, _ = self._neighborhood_sums_for_centers(
            scale,
            centers_flat,
            _totals_integral=_totals_integral
        )
        return coords, exprs, totals_supported


class Worker(Process):
    """Deprecated worker implementation.

    Kept for backwards compatibility but no longer used by classify_parallel(),
    which now performs scale-major neighbourhood aggregation using integral
    images (summed-area tables).
    """

    def __init__(self,
                 grid: ExpressionGrid,
                 min_scale: int,
                 max_scale: int,
                 classifier: Classifier,
                 job_queue: Queue,
                 res_queue: Queue,
                 procid: int,
                 verbose: bool
                 ):
        super().__init__()
        self.grid = grid
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.classifier = classifier
        self.job_queue = job_queue
        self.res_queue = res_queue
        self.procid = procid
        self.verbose = verbose

    def run(self):
        simplefilter(action='ignore', category=FutureWarning)
        if self.verbose:
            print(f'Worker {self.procid} started')

        num_classes = len(self.classifier.classes)

        cols = list(self.grid.cols())
        num_scales = self.max_scale - self.min_scale + 1
        exprs = np.zeros((num_scales, self.grid.num_genes))
        for i, col_values in iter(self.job_queue.get, None):
            if self.verbose:
                print(f"Worker {self.procid} got job {i}")
            for col_index in col_values:
                j = cols[col_index]
                for scale in range(self.min_scale, self.max_scale + 1):
                    nbhd = self.grid.square_nbhd_vec(i, j, scale)
                    expr = self.grid.expression_vec(nbhd)
                    exprs[scale - self.min_scale] = expr

                first_nonzero = densetools.first_nonzero_1d(exprs.sum(axis=1))

                probs = np.empty((num_scales, num_classes))
                probs[:] = -1

                if 0 <= first_nonzero < num_scales:
                    to_classify = np.vstack(exprs[first_nonzero:])  # pyright: ignore # noqa: E501

                    all_confidences = self.classifier.classify(to_classify)

                    probs[first_nonzero:] = all_confidences

                self.res_queue.put((i, j, probs.tolist()))
        self.res_queue.put(None)
        if self.verbose:
            print(f'Worker {self.procid} finished')


class CountGrid(CountTable):
    """A spatial transcriptomics object with associated methods.

    Attributes:
        grid: An expression grid.
    """

    def __init__(self, *args, **kwargs):
        """Inits spatial data with values from a dataframe."""
        super().__init__(*args, **kwargs)
        self.generate_expression_grid()
        self.height, self.width = self.grid.height, self.grid.width

    @classmethod
    def from_coord_table(cls, table, **kwargs):
        x_coords = range(table.x.min(), table.x.max() + 1)
        y_coords = range(table.y.min(), table.y.max() + 1)

        coords = itertools.product(x_coords, y_coords)
        samples = map(combine_coords, coords)

        new_table = table.copy()
        new_table['sample'] = new_table.apply(lambda row: f'{row.x},{row.y}',
                                              axis=1)

        count_grid = cls(new_table, samples=list(samples), **kwargs)
        samples = count_grid.samples
        x_coords = {sample: first_coord(sample) for sample in samples}
        y_coords = {sample: second_coord(sample) for sample in samples}
        count_grid.add_metadata('x', x_coords)
        count_grid.add_metadata('y', y_coords)
        return count_grid

    def pseudobulk(self) -> npt.NDArray:
        return np.array(self.grid.matrix.sum(axis=0))[0]

    def count_matrix(self) -> npt.NDArray:
        # It's tempting to try and do something clever with numpy or pandas
        # here. There be dragons.
        x_min = self.table.x.min()
        y_min = self.table.y.min()
        count_matrix = np.zeros((self.width, self.height))
        counts = self.table.groupby(['x', 'y']).sum().reset_index()
        count_index = self.table.columns.get_loc(self.count_col)
        for row in counts.itertuples():
            count_matrix[row.y-y_min, row.x-x_min] += row[count_index]
        return count_matrix

    def density_mask(self, radius: int, threshold: int) -> npt.NDArray:
        return densetools.density_hull(self.count_matrix(), radius, threshold)

    def generate_expression_grid(self):
        self.grid = ExpressionGrid(self.table,
                                   genes=self.genes,
                                   gene_col=self.gene_col,
                                   count_col=self.count_col
                                   )

    def classify_parallel(self,
                          classifier: Classifier,
                          min_scale: int,
                          max_scale: int,
                          outfile: str,
                          mask: npt.NDArray | None = None,
                          num_proc: int = 1,
                          verbose: bool = False,
                          threshold: float | None = None
                          ):
        """Classify spots across multiple neighbourhood scales.

        This implementation performs scale-major neighbourhood aggregation using
        integral images (summed-area tables), avoiding explicit enumeration of
        neighbourhood coordinates per spot/scale.

        Additionally, if `threshold` is provided, performs *active-set* multiscale
        classification with early stopping: once a spot exceeds the confidence
        threshold at some scale, it is removed from subsequent scales.

        Note:
            num_proc is currently unused in this fast path (kept for API
            compatibility).
        """
        _ = num_proc  # API compat; multiprocessing not used in scale-major path

        outfile += '' if outfile[-4:] == '.npy' else '.npy'
        shape = (int(self.grid.height),
                 int(self.grid.width),
                 int(max_scale - min_scale + 1),
                 len(classifier.classes)
                 )
        result = np.lib.format.open_memmap(outfile, dtype=np.float32,
                                           mode='w+', shape=shape)
        result[:] = np.nan
        result.flush()

        # Historical code transposed mask; preserve that behaviour.
        tissue_mask: npt.NDArray | None = None
        if mask is not None:
            mask = mask.T
            if mask.shape != (self.height, self.width):
                raise ValueError(f'Mask has shape {mask.shape} but expected {(self.height, self.width)}')
            tissue_mask = mask.astype(bool, copy=False)

        num_scales = int(max_scale - min_scale + 1)

        # Precompute totals integral image once per run (expensive sparse reduction otherwise)
        H = int(self.grid.height)
        W = int(self.grid.width)
        totals_flat = np.asarray(self.grid.matrix.sum(axis=1)).reshape(-1)
        T = totals_flat.reshape(H, W)
        totals_integral = np.pad(np.cumsum(np.cumsum(T, axis=0), axis=1),
                                 ((1, 0), (1, 0)),
                                 mode='constant')

        # Precompute and cache box bounds for all requested scales
        for scale in range(min_scale, max_scale + 1):
            self.grid._get_box_bounds(scale)

        # Attempt to build a cached integral image for all genes once (guarded by memory limit)
        _ = self.grid._ensure_integral_X()

        C = len(classifier.classes)

        # Reuse one flattened view for all writes: (H*W, num_scales, C)
        flat_result = result.reshape(H * W, num_scales, C)

        # Active-set update optimization for threshold mode: use a boolean mask.
        if threshold is not None:
            if tissue_mask is None:
                active_mask = np.ones(H * W, dtype=bool)
            else:
                active_mask = tissue_mask.ravel().astype(bool, copy=False).copy()
            active_flat = np.flatnonzero(active_mask).astype(np.int64, copy=False)
        else:
            active_mask = None
            if tissue_mask is None:
                active_flat = np.arange(H * W, dtype=np.int64)
            else:
                active_flat = np.flatnonzero(tissue_mask.ravel()).astype(np.int64, copy=False)

        # Flushing a memmap can be expensive; default to flushing only at the end.
        flush_every = 0

        for scale_index, scale in enumerate(range(min_scale, max_scale + 1)):
            if threshold is not None and active_flat.size == 0:
                if verbose:
                    print(f"All spots resolved by scale {scale-1}; stopping early.")
                break

            if verbose:
                print(f"Aggregating scale {scale} ({scale_index+1}/{num_scales})")

            _, exprs, totals_supported, supported_flat = self.grid._neighborhood_sums_for_centers_nocoords(
                scale,
                active_flat,
                _totals_integral=totals_integral
            )

            if exprs.shape[0] == 0:
                continue

            # Fast path: reuse totals_supported for normalization and do in-place log1p.
            if isinstance(classifier, SVCClassifier):
                factors = (10 ** classifier.r_value) / totals_supported
                exprs = exprs.astype(np.float32, copy=False)
                exprs *= factors[:, None]
                np.log1p(exprs, out=exprs)
                confidences = classifier.clf.predict_proba(exprs)
            else:
                confidences = classifier.classify(exprs)

            confidences = confidences.astype(np.float32, copy=False)

            # Write directly into flat memmap view.
            flat_result[supported_flat, scale_index, :] = confidences

            # Early stopping: mark resolved spots inactive; rebuild active list.
            if threshold is not None and active_mask is not None:
                max_conf = np.max(confidences, axis=1)
                resolved = max_conf >= float(threshold)
                if np.any(resolved):
                    active_mask[supported_flat[resolved]] = False
                active_flat = np.flatnonzero(active_mask).astype(np.int64, copy=False)

            if flush_every and (scale_index + 1) % flush_every == 0:
                result.flush()

        result.flush()
        if verbose:
            print("Done!")

    def annotate(self,
                 confidence_matrix: npt.NDArray,
                 threshold: float,
                 labels: tuple[str, ...],
                 column_label: str = "cell type"):

        classifications = extract_classifications(confidence_matrix, threshold)
        x_min, y_min = self.grid.x_min, self.grid.y_min
        to_add = {combine_coords((x+x_min, y+y_min)): labels[c]
                  for (x, y), c in classifications.items()
                  }

        self.add_metadata(column_label, to_add)
