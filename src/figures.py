from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import polars as pl

COLOR_SEQUENCE = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c"]
PIE_COLORS = [
    "#93c5fd",
    "#86efac",
    "#fca5a5",
    "#c4b5fd",
    "#fdba74",
    "#67e8f9",
    "#fde68a",
    "#f9a8d4",
    "#a7f3d0",
    "#cbd5e1",
]


def department_map(data: pl.DataFrame, geojson: dict[str, Any]) -> go.Figure:
    """Crea el mapa de muertes por departamento."""
    figure = go.Figure(
        go.Choropleth(
            geojson=geojson,
            locations=data["dpto"].to_list(),
            z=data["total"].to_list(),
            featureidkey="properties.DPTO",
            text=data["departamento"].to_list(),
            colorscale="Reds",
            colorbar={
                "title": "Muertes",
                "thickness": 16,
                "len": 0.78,
                "x": 0.94,
                "y": 0.48,
            },
            marker_line_color="#ffffff",
            marker_line_width=0.6,
            hovertemplate="<b>%{text}</b><br>Muertes: %{z:,}<extra></extra>",
        )
    )
    figure.update_geos(
        fitbounds="locations",
        visible=False,
        domain={"x": [0.0, 0.88], "y": [0.0, 1.0]},
    )
    figure.update_layout(
        height=620,
        margin={"r": 35, "t": 58, "l": 25, "b": 20},
        title="Distribucion total de muertes por departamento",
        title_x=0.02,
        dragmode="zoom",
    )
    return figure


def monthly_line(data: pl.DataFrame) -> go.Figure:
    """Crea la linea de muertes por mes."""
    figure = go.Figure(
        go.Scatter(
            x=data["mes_nombre"].to_list(),
            y=data["total"].to_list(),
            mode="lines+markers",
            line={"color": "#2563eb", "width": 3},
            marker={"size": 8},
            hovertemplate="Mes: %{x}<br>Muertes: %{y:,}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Total de muertes por mes en Colombia",
        xaxis_title=None,
        yaxis_title="Muertes",
        yaxis_tickformat=",",
    )
    return figure


def violent_cities_bar(data: pl.DataFrame) -> go.Figure:
    """Crea las barras de las ciudades con mas homicidios X95."""
    sorted_data = data.sort("total")
    figure = go.Figure(
        go.Bar(
            x=sorted_data["total"].to_list(),
            y=sorted_data["ciudad"].to_list(),
            orientation="h",
            marker={"color": "#b91c1c"},
            hovertemplate="%{y}<br>Homicidios: %{x:,}<extra></extra>",
        )
    )
    figure.update_layout(
        title="5 ciudades mas violentas por homicidios con armas de fuego",
        yaxis_title=None,
        xaxis_title="Homicidios",
        xaxis_tickformat=",",
        showlegend=False,
    )
    return figure


def lowest_mortality_pie(data: pl.DataFrame) -> go.Figure:
    """Crea el grafico circular de ciudades con menor mortalidad."""
    figure = go.Figure(
        go.Pie(
            labels=data["ciudad"].to_list(),
            values=data["total"].to_list(),
            marker={"colors": PIE_COLORS},
            textinfo="percent+label",
            hovertemplate="%{label}<br>Muertes: %{value:,}<extra></extra>",
        )
    )
    figure.update_layout(
        title="10 ciudades con menor total de muertes registradas",
        showlegend=False,
    )
    return figure


def department_sex_stacked_bar(data: pl.DataFrame) -> go.Figure:
    """Crea las barras apiladas por sexo y departamento."""
    departments = data["departamento"].unique(maintain_order=True).to_list()
    colors = {
        "Hombres": "#2563eb",
        "Mujeres": "#db2777",
        "Indeterminado": "#64748b",
        "Sin informacion": "#94a3b8",
    }
    figure = go.Figure()

    for sex_name, color in colors.items():
        totals = _totals_by_department(data, departments, sex_name)
        figure.add_bar(
            x=totals,
            y=departments,
            name=sex_name,
            orientation="h",
            marker={"color": color},
            hovertemplate="%{y}<br>Muertes: %{x:,}<extra></extra>",
        )

    figure.update_layout(
        title="Muertes por sexo en cada departamento",
        barmode="stack",
        yaxis_title=None,
        xaxis_title="Muertes",
        xaxis_tickformat=",",
        legend_title_text="Sexo",
        height=850,
    )
    return figure


def age_group_histogram(data: pl.DataFrame) -> go.Figure:
    """Crea el histograma por categorias de edad DANE."""
    figure = go.Figure(
        go.Bar(
            x=data["categoria_edad"].to_list(),
            y=data["total"].to_list(),
            marker={"color": COLOR_SEQUENCE * 3},
            hovertemplate="%{x}<br>Muertes: %{y:,}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Distribucion de muertes por grupos de edad",
        xaxis_title=None,
        yaxis_title="Muertes",
        yaxis_tickformat=",",
        showlegend=False,
    )
    figure.update_xaxes(tickangle=-35)
    return figure


def _totals_by_department(
    data: pl.DataFrame, departments: list[str], sex_name: str
) -> list[int]:
    """Obtiene totales alineados por departamento para un sexo."""
    filtered = data.filter(pl.col("sexo_nombre") == sex_name)
    values = dict(
        zip(filtered["departamento"].to_list(), filtered["total"].to_list(), strict=True)
    )
    return [int(values.get(department, 0)) for department in departments]
