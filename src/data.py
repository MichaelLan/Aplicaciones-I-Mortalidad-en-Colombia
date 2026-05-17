from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import polars as pl

BASE_PATH = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_PATH / "data"


@dataclass(frozen=True)
class DashboardData:
    """Datos agregados necesarios para construir el tablero."""

    department_totals: pl.DataFrame
    monthly_totals: pl.DataFrame
    violent_cities: pl.DataFrame
    lowest_mortality_cities: pl.DataFrame
    top_causes: pl.DataFrame
    department_sex_totals: pl.DataFrame
    age_group_totals: pl.DataFrame
    geojson: dict[str, Any]
    total_deaths: int
    total_departments: int
    total_municipalities: int


@lru_cache(maxsize=1)
def load_dashboard_data() -> DashboardData:
    """Carga los archivos base y calcula los agregados del tablero."""
    deaths = _load_deaths()
    municipalities = _load_municipalities()
    death_codes = _load_death_codes()
    geojson = _load_geojson()

    enriched_deaths = deaths.join(municipalities, on="cod_name", how="left")
    department_totals = _department_totals(enriched_deaths)
    monthly_totals = _monthly_totals(deaths)
    violent_cities = _violent_cities(enriched_deaths)
    lowest_mortality_cities = _lowest_mortality_cities(enriched_deaths)
    top_causes = _top_causes(deaths, death_codes)
    department_sex_totals = _department_sex_totals(enriched_deaths)
    age_group_totals = _age_group_totals(deaths)

    return DashboardData(
        department_totals=department_totals,
        monthly_totals=monthly_totals,
        violent_cities=violent_cities,
        lowest_mortality_cities=lowest_mortality_cities,
        top_causes=top_causes,
        department_sex_totals=department_sex_totals,
        age_group_totals=age_group_totals,
        geojson=geojson,
        total_deaths=deaths.height,
        total_departments=department_totals.height,
        total_municipalities=enriched_deaths.select(pl.col("cod_name").n_unique()).item(),
    )


def _load_deaths() -> pl.DataFrame:
    """Lee las defunciones no fetales de Colombia para 2019."""
    return pl.read_excel(
        DATA_PATH / "no_fetal_2019.xlsx",
        sheet_name="No_Fetales_2019",
        engine="xlsx2csv",
    ).with_columns(
        pl.col("cod_name").cast(pl.Int64),
        pl.col("cod_departamento").cast(pl.Int64),
        pl.col("cod_municipio").cast(pl.Int64),
        pl.col("cod_muerte").cast(pl.String),
    )


def _load_municipalities() -> pl.DataFrame:
    """Lee la tabla DIVIPOLA usada para nombres de departamentos y municipios."""
    return (
        pl.read_excel(
            DATA_PATH / "divipola.xlsx",
            sheet_name="Hoja1",
            engine="xlsx2csv",
        )
        .select(
            pl.col("cod_dane").cast(pl.Int64).alias("cod_name"),
            pl.col("departamento").cast(pl.String),
            pl.col("municipio").cast(pl.String),
        )
        .unique(subset=["cod_name"])
    )


def _load_death_codes() -> pl.DataFrame:
    """Lee los codigos CIE y su descripcion de mortalidad."""
    return (
        pl.read_excel(
            DATA_PATH / "codigos_muerte.xlsx",
            sheet_name="Final",
            engine="xlsx2csv",
        )
        .select(
            pl.col("cod_4").cast(pl.String).alias("codigo"),
            pl.col("descrip_mortal").cast(pl.String).alias("causa"),
        )
        .unique(subset=["codigo"])
    )


def _load_geojson() -> dict[str, Any]:
    """Lee la geometria de departamentos de Colombia."""
    with (DATA_PATH / "Colombia.geo.json").open(encoding="utf-8") as file:
        value = json.load(file)

    if not isinstance(value, dict):
        msg = "El archivo GeoJSON debe tener un objeto principal."
        raise TypeError(msg)

    return value


def _department_totals(deaths: pl.DataFrame) -> pl.DataFrame:
    """Agrupa el total de muertes por departamento."""
    return (
        deaths.group_by("cod_departamento")
        .agg(
            pl.len().alias("total"),
            pl.col("departamento").drop_nulls().first().alias("departamento"),
        )
        .with_columns(
            pl.col("cod_departamento").cast(pl.Utf8).str.zfill(2).alias("dpto"),
            pl.col("departamento").fill_null("SIN INFORMACION"),
        )
        .sort("total", descending=True)
    )


def _monthly_totals(deaths: pl.DataFrame) -> pl.DataFrame:
    """Agrupa el total de muertes por mes."""
    month_names = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }

    return (
        deaths.group_by("mes")
        .agg(pl.len().alias("total"))
        .sort("mes")
        .with_columns(
            pl.col("mes")
            .replace_strict(month_names, return_dtype=pl.String)
            .alias("mes_nombre")
        )
    )


def _violent_cities(deaths: pl.DataFrame) -> pl.DataFrame:
    """Calcula las cinco ciudades con mas homicidios por armas de fuego."""
    return (
        deaths.filter(pl.col("cod_muerte").str.starts_with("X95"))
        .group_by("cod_name")
        .agg(
            pl.len().alias("total"),
            pl.col("municipio").drop_nulls().first().alias("municipio"),
            pl.col("departamento").drop_nulls().first().alias("departamento"),
        )
        .with_columns(
            pl.concat_str(
                [
                    pl.col("municipio").fill_null("SIN INFORMACION"),
                    pl.lit(", "),
                    pl.col("departamento").fill_null("SIN INFORMACION"),
                ]
            ).alias("ciudad")
        )
        .sort("total", descending=True)
        .head(5)
    )


def _lowest_mortality_cities(deaths: pl.DataFrame) -> pl.DataFrame:
    """Calcula las diez ciudades con menor total de muertes registradas."""
    return (
        deaths.group_by("cod_name")
        .agg(
            pl.len().alias("total"),
            pl.col("municipio").drop_nulls().first().alias("municipio"),
            pl.col("departamento").drop_nulls().first().alias("departamento"),
        )
        .with_columns(
            pl.concat_str(
                [
                    pl.col("municipio").fill_null("SIN INFORMACION"),
                    pl.lit(", "),
                    pl.col("departamento").fill_null("SIN INFORMACION"),
                ]
            ).alias("ciudad")
        )
        .sort(["total", "ciudad"])
        .head(10)
    )


def _top_causes(deaths: pl.DataFrame, death_codes: pl.DataFrame) -> pl.DataFrame:
    """Calcula las diez causas de muerte mas frecuentes."""
    return (
        deaths.group_by("cod_muerte")
        .agg(pl.len().alias("total"))
        .rename({"cod_muerte": "codigo"})
        .join(death_codes, on="codigo", how="left")
        .with_columns(pl.col("causa").fill_null("Sin descripcion"))
        .sort("total", descending=True)
        .head(10)
        .select("codigo", "causa", "total")
    )


def _department_sex_totals(deaths: pl.DataFrame) -> pl.DataFrame:
    """Agrupa las muertes por sexo y departamento."""
    sex_names = {1: "Hombres", 2: "Mujeres", 3: "Indeterminado"}
    deaths_with_department = deaths.with_columns(
        pl.col("departamento").fill_null("SIN INFORMACION")
    )

    department_order = (
        deaths_with_department.group_by("departamento")
        .agg(pl.len().alias("departamento_total"))
        .sort("departamento_total", descending=True)
    )

    return (
        deaths_with_department.group_by(["departamento", "sexo"])
        .agg(pl.len().alias("total"))
        .with_columns(
            pl.col("sexo")
            .replace_strict(sex_names, default="Sin informacion", return_dtype=pl.String)
            .alias("sexo_nombre"),
        )
        .join(department_order, on="departamento", how="left")
        .sort(
            ["departamento_total", "departamento", "sexo"],
            descending=[True, False, False],
        )
    )


def _age_group_totals(deaths: pl.DataFrame) -> pl.DataFrame:
    """Agrupa las muertes por rangos definidos de GRUPO_EDAD1."""
    age_category = (
        pl.when(pl.col("grupo_edad1").is_between(0, 4))
        .then(pl.lit("Mortalidad neonatal"))
        .when(pl.col("grupo_edad1").is_between(5, 6))
        .then(pl.lit("Mortalidad infantil"))
        .when(pl.col("grupo_edad1").is_between(7, 8))
        .then(pl.lit("Primera infancia"))
        .when(pl.col("grupo_edad1").is_between(9, 10))
        .then(pl.lit("Ninez"))
        .when(pl.col("grupo_edad1") == 11)
        .then(pl.lit("Adolescencia"))
        .when(pl.col("grupo_edad1").is_between(12, 13))
        .then(pl.lit("Juventud"))
        .when(pl.col("grupo_edad1").is_between(14, 16))
        .then(pl.lit("Adultez temprana"))
        .when(pl.col("grupo_edad1").is_between(17, 19))
        .then(pl.lit("Adultez intermedia"))
        .when(pl.col("grupo_edad1").is_between(20, 24))
        .then(pl.lit("Vejez"))
        .when(pl.col("grupo_edad1").is_between(25, 28))
        .then(pl.lit("Longevidad / Centenarios"))
        .when(pl.col("grupo_edad1") == 29)
        .then(pl.lit("Edad desconocida"))
        .otherwise(pl.lit("Sin clasificar"))
    )

    order = {
        "Mortalidad neonatal": 1,
        "Mortalidad infantil": 2,
        "Primera infancia": 3,
        "Ninez": 4,
        "Adolescencia": 5,
        "Juventud": 6,
        "Adultez temprana": 7,
        "Adultez intermedia": 8,
        "Vejez": 9,
        "Longevidad / Centenarios": 10,
        "Edad desconocida": 11,
        "Sin clasificar": 12,
    }

    return (
        deaths.with_columns(age_category.alias("categoria_edad"))
        .group_by("categoria_edad")
        .agg(pl.len().alias("total"))
        .with_columns(
            pl.col("categoria_edad")
            .replace_strict(order, return_dtype=pl.Int64)
            .alias("orden")
        )
        .sort("orden")
    )
