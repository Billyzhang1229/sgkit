from typing import Any, Dict, Optional

import numpy as np
import xarray as xr
from xarray import Dataset
from zarr.storage import StoreLike

# The dtype Xarray uses for object arrays of variable-length strings
VLEN_STR_DTYPE = np.dtype("O", metadata={"element_type": str})


def save_dataset(
    ds: Dataset,
    store: StoreLike,
    storage_options: Optional[Dict[str, str]] = None,
    auto_rechunk: Optional[bool] = None,
    zarr_format: int = 2,
    **kwargs: Any,
) -> None:
    """Save a dataset to Zarr storage.

    This function is a thin wrapper around :meth:`xarray.Dataset.to_zarr`
    that uses sensible defaults and makes it easier to use in a pipeline.

    Parameters
    ----------
    ds
        Dataset to save.
    store
        Zarr store or path to directory in file system to save to.
    storage_options:
        Any additional parameters for the storage backend (see ``fsspec.open``).
    auto_rechunk:
        If True, automatically rechunk the dataset to uniform chunks before saving,
        if necessary. This is required for Zarr, but can be expensive. Defaults to False.
    zarr_format:
        On-disk Zarr format, either 2 or 3. Defaults to 2 for compatibility with
        existing datasets, even though sgkit requires Zarr Python 3.
    kwargs
        Additional arguments to pass to :meth:`xarray.Dataset.to_zarr`.
    """
    if auto_rechunk is None:
        auto_rechunk = False
    # Change the encoding on a shallow copy, so the caller's dataset is unchanged
    ds = ds.copy()
    for v in ds.variables:
        # Workaround for https://github.com/pydata/xarray/issues/4380
        ds[v].encoding.pop("chunks", None)

        # Workaround for https://github.com/pydata/xarray/issues/11848: Xarray
        # writes NumPy StringDType arrays to Zarr format 2 as fixed-width Unicode,
        # so ask for variable-length strings instead. Strings with a fill value
        # load as objects, but keep StringDType as their encoding dtype.
        dtype = ds[v].encoding.get("dtype", ds[v].dtype)
        if zarr_format == 2 and np.dtype(dtype).kind == "T":
            ds[v].encoding["dtype"] = VLEN_STR_DTYPE

    if auto_rechunk:
        # This logic for checking if rechunking is necessary is
        # taken from xarray/backends/zarr.py#L109.
        # We can't try to save and catch the error as by that
        # point the zarr store is non-empty.
        if any(len(set(chunks[:-1])) > 1 for chunks in ds.chunks.values()) or any(
            (chunks[0] < chunks[-1]) for chunks in ds.chunks.values()
        ):
            # Here we use the max chunk size as the target chunk size as for the commonest
            # case of subsetting an existing dataset, this will be closest to the original
            # intended chunk size.
            ds = ds.chunk(
                chunks={dim: max(chunks) for dim, chunks in ds.chunks.items()}
            )

    # Catch unequal chunking errors to provide a more helpful error message
    try:
        ds.to_zarr(
            store, storage_options=storage_options, zarr_format=zarr_format, **kwargs
        )
    except ValueError as e:
        if "Zarr requires uniform chunk sizes" in str(
            e
        ) or "Final chunk of Zarr array must be the same size" in str(e):
            raise ValueError(
                "Zarr requires uniform chunk sizes. Use the `auto_rechunk` argument to"
                "`save_dataset` to automatically rechunk the dataset."
            ) from e
        else:
            raise e


def load_dataset(
    store: StoreLike,
    storage_options: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> Dataset:
    """Load a dataset from Zarr storage.

    This function is a thin wrapper around :func:`xarray.open_zarr`
    that uses sensible defaults and makes it easier to use in a pipeline.

    Parameters
    ----------
    store
        Zarr store or path to directory in file system to load from.
    storage_options:
        Any additional parameters for the storage backend (see ``fsspec.open``).
    kwargs
        Additional arguments to pass to :func:`xarray.open_zarr`.

    Returns
    -------

    Dataset
        The dataset loaded from the Zarr store or file system.
    """
    ds: Dataset = xr.open_zarr(store, storage_options=storage_options, concat_characters=False, **kwargs)  # type: ignore[no-untyped-call]
    for v in ds:
        # Workaround for https://github.com/pydata/xarray/issues/4386
        if v.endswith("_mask"):  # type: ignore
            ds[v] = ds[v].astype(bool)
    return ds
