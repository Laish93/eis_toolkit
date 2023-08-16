from enum import Enum
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import rasterio
import typer
from rasterio import warp
from typing_extensions import Annotated

from eis_toolkit.raster_processing.clipping import clip_raster
from eis_toolkit.raster_processing.reprojecting import reproject_raster
from eis_toolkit.raster_processing.snapping import snap_with_raster
from eis_toolkit.raster_processing.windowing import extract_window
from eis_toolkit.vector_processing.reproject_vector import reproject_vector

app = typer.Typer()


class VariogramModel(str, Enum):
    """Variogram models for kriging interpolation."""

    linear = "linear"
    power = "power"
    gaussian = "gaussian"
    spherical = "spherical"
    exponential = "exponential"
    hole_effect = "hole-effect"


class KrigingMethod(str, Enum):
    """Kriging methods."""

    ordinary = "ordinary"
    universal = "universal"


class MergeStrategy(str, Enum):
    """Merge strategies for rasterizing."""

    replace = "replace"
    add = "add"


class ResamplingMethods(str, Enum):
    """Resampling methods available."""

    nearest = "nearest"
    bilinear = "bilinear"
    cubic = "cubic"
    average = "average"
    gauss = "gauss"
    max = "max"
    min = "min"


RESAMPLING_MAPPING = {
    "nearest": warp.Resampling.nearest,
    "bilinear": warp.Resampling.bilinear,
    "cubic": warp.Resampling.cubic,
    "average": warp.Resampling.average,
    "gauss": warp.Resampling.gauss,
    "max": warp.Resampling.max,
    "min": warp.Resampling.min,
}


# def file_option(help: str = None, default: Any = None, read: bool = True, write: bool = False):
#     return typer.Option(
#         default=default,
#         help=help,
#         exists=True,
#         file_okay=True,
#         dir_okay=False,
#         writable=write,
#         readable=read,
#         resolve_path=True,
#     )


# TODO: Check this and output file option
INPUT_FILE_OPTION = typer.Option(
    exists=True,
    file_okay=True,
    dir_okay=False,
    writable=False,
    readable=True,
    resolve_path=True,
)

OUTPUT_FILE_OPTION = typer.Option(
    file_okay=True,
    dir_okay=False,
    writable=True,
    readable=True,
    resolve_path=True,
)


# CLIP RASTER
@app.command()
def clip_raster_cli(
    input_raster: Annotated[Path, INPUT_FILE_OPTION],
    geometries: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
):
    """Clip the input raster with geometries in a geodataframe."""

    typer.echo("Progress: 10%")

    geodataframe = gpd.read_file(geometries)
    typer.echo("Progress: 40%")

    with rasterio.open(input_raster) as raster:
        out_image, out_meta = clip_raster(
            raster=raster,
            geodataframe=geodataframe,
        )

    typer.echo("Progress: 70%")

    with rasterio.open(output_raster, "w", **out_meta) as dest:
        dest.write(out_image)

    typer.echo("Progress: 100%")
    typer.echo(f"Clipping completed, output raster written to {output_raster}.")


# REPROJECT RASTER
@app.command()
def reproject_raster_cli(
    input_raster: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
    target_crs: int = typer.Option(help="crs help"),
    resampling_method: ResamplingMethods = typer.Option(help="resample help", default=ResamplingMethods.nearest),
):
    """Reproject the input raster to given CRS."""
    method = RESAMPLING_MAPPING[resampling_method]
    with rasterio.open(input_raster) as raster:
        out_image, out_meta = reproject_raster(raster=raster, target_crs=target_crs, resampling_method=method)

    with rasterio.open(output_raster, "w", **out_meta) as dest:
        dest.write(out_image)

    typer.echo("Reprojecting completed")
    typer.echo(f"Writing raster to {output_raster}.")


# SNAP RASTER
@app.command()
def snap_raster_cli(
    input_raster: Annotated[Path, INPUT_FILE_OPTION],
    snap_raster: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
):
    """Snaps/aligns input raster to the given snap raster."""
    with rasterio.open(input_raster) as src, rasterio.open(snap_raster) as snap_src:
        out_image, out_meta = snap_with_raster(src, snap_src)

    with rasterio.open(output_raster, "w", **out_meta) as dst:
        dst.write(out_image)

    typer.echo("Snapping completed")
    typer.echo(f"Writing raster to {output_raster}")


# EXTRACT WINDOW
@app.command()
def extract_window_cli(
    input_raster: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
    center_coords: Tuple[float, float] = typer.Option(),
    height: int = typer.Option(),
    width: int = typer.Option(),
):
    """Extract window from raster."""
    with rasterio.open(input_raster) as raster:
        out_image, out_meta = extract_window(raster, center_coords, height, width)

    with rasterio.open(output_raster, "w", **out_meta) as dst:
        dst.write(out_image)

    typer.echo("Windowing completed")
    typer.echo(f"Writing raster to {output_raster}")


# UNIFY RASTERS
@app.command()
def unify_rasters_cli(
    base_raster: Annotated[Path, INPUT_FILE_OPTION],
    rasters_to_unify: Annotated[List[Path], INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
    resampling_method: ResamplingMethods = typer.Option(help="resample help", default=ResamplingMethods.nearest),
    same_extent: bool = False,
):
    """Extract window from raster. NOT IMPLEMENTED YET."""
    pass


# RASTERIZE
@app.command()
def rasterize_cli(
    input_vector: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
    resolution: float = None,
    value_column: str = None,
    default_value: float = 1.0,
    fill_value: float = 0.0,
    base_raster_profile_raster: Annotated[Path, INPUT_FILE_OPTION] = None,
    buffer_value: float = None,
    merge_strategy: MergeStrategy = MergeStrategy.replace,
):
    """Rasterize input vector."""
    from eis_toolkit.vector_processing.rasterize_vector import rasterize_vector

    geodataframe = gpd.read_file(input_vector)

    if base_raster_profile_raster is not None:
        with rasterio.open(base_raster_profile_raster) as raster:
            base_raster_profile = raster.profile

    out_image, out_meta = rasterize_vector(
        geodataframe,
        resolution,
        value_column,
        default_value,
        fill_value,
        base_raster_profile,
        buffer_value,
        merge_strategy,
    )

    out_meta.update(
        {
            "count": 1,
            "dtype": base_raster_profile["dtype"] if base_raster_profile_raster else float,  # TODO change this
        }
    )

    with rasterio.open(output_raster, "w", **out_meta) as dst:
        dst.write(out_image)

    typer.echo("Rasterizing completed")
    typer.echo(f"Writing raster to {output_raster}")


# REPROJECT VECTOR
@app.command()
def reproject_vector_cli(
    input_vector: Annotated[Path, INPUT_FILE_OPTION],
    output_vector: Annotated[Path, OUTPUT_FILE_OPTION],
    target_crs: int = typer.Option(help="crs help"),
):
    """Reproject the input vector to given CRS."""
    geodataframe = gpd.read_file(input_vector)

    reprojected_geodataframe = reproject_vector(geodataframe=geodataframe, target_crs=target_crs)

    reprojected_geodataframe.to_file(output_vector, driver="GeoJSON")

    typer.echo("Reprojecting completed")
    typer.echo(f"Writing vector to {output_vector}")


# KRIGING INTERPOLATION
@app.command()
def kriging_interpolation_cli(
    input_vector: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
    target_column: str = typer.Option(),
    pixel_size_x: float = typer.Option(),
    pixel_size_y: float = typer.Option(),
    extent: Tuple[float, float, float, float] = None,
    variogram_model: VariogramModel = VariogramModel.linear,
    method: KrigingMethod = KrigingMethod.ordinary,
    drift_terms: Annotated[List[str], typer.Option()] = ["regional_linear"],
):
    """Apply kriging interpolation to input vector file."""
    from eis_toolkit.vector_processing.kriging_interpolation import kriging

    geodataframe = gpd.read_file(input_vector)

    out_image, out_meta = kriging(
        data=geodataframe,
        target_column=target_column,
        resolution=(pixel_size_x, pixel_size_y),
        extent=extent,
        variogram_model=variogram_model,
        method=method,
        drift_terms=drift_terms,
    )

    out_meta.update(
        {
            "count": 1,
            "driver": "GTiff",
            "dtype": "float32",
        }
    )

    with rasterio.open(out_image, "w", **out_meta) as dst:
        dst.write(out_image)

    typer.echo("Kriging interpolation completed")
    typer.echo(f"Writing raster to {output_raster}")


# DISTANCE COMPUTATION
@app.command()
def distance_computation_cli(
    input_raster: Annotated[Path, INPUT_FILE_OPTION],
    geometries: Annotated[Path, INPUT_FILE_OPTION],
    output_raster: Annotated[Path, OUTPUT_FILE_OPTION],
):
    """Reproject the input vector to given CRS."""
    from eis_toolkit.spatial_analyses.distance_computation import distance_computation

    with rasterio.open(input_raster) as raster:
        profile = raster.profile

    geodataframe = gpd.read_file(geometries)

    out_image = distance_computation(profile, geodataframe)

    with rasterio.open(output_raster, "w", **profile) as dst:
        dst.write(out_image, profile["count"])

    typer.echo("Distance computation completed")
    typer.echo(f"Writing raster to {output_raster}")


# DESCRIPTIVE STATISTICS
def descriptive_statistics_cli(input_file: Annotated[Path, INPUT_FILE_OPTION], column: str):
    """Not implemented yet."""
    pass


# if __name__ == "__main__":
def cli():
    """CLI app."""
    app()


if __name__ == "__main__":
    app()
