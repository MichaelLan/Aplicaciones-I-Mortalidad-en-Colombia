from __future__ import annotations

from dash import Dash, dcc, html

from data import DashboardData, load_dashboard_data
from figures import (
    age_group_histogram,
    department_map,
    department_sex_stacked_bar,
    lowest_mortality_pie,
    monthly_line,
    violent_cities_bar,
)

CARD_STYLE = {
    "background": "#ffffff",
    "border": "1px solid #e2e8f0",
    "borderRadius": "14px",
    "boxShadow": "0 8px 24px rgba(15, 23, 42, 0.08)",
    "padding": "18px",
}

TABLE_CELL_STYLE = {
    "borderBottom": "1px solid #e2e8f0",
    "padding": "10px",
    "textAlign": "left",
}

TABLE_HEADER_STYLE = {
    **TABLE_CELL_STYLE,
    "background": "#0f172a",
    "color": "#ffffff",
}


def create_app() -> Dash:
    """Construye la aplicacion Dash de mortalidad en Colombia."""
    data = load_dashboard_data()
    app = Dash(__name__, title="Mortalidad Colombia 2019")
    app.layout = _layout(data)
    return app


def _layout(data: DashboardData) -> html.Div:
    """Define el layout principal del tablero."""
    return html.Div(
        children=[
            _header(data),
            _map_card(data),
            _graph_grid(
                [
                    dcc.Graph(figure=monthly_line(data.monthly_totals)),
                    dcc.Graph(figure=violent_cities_bar(data.violent_cities)),
                    dcc.Graph(figure=lowest_mortality_pie(data.lowest_mortality_cities)),
                ]
            ),
            _section_title("Principales causas de muerte"),
            _causes_table(data),
            _graph_grid(
                [
                    dcc.Graph(
                        figure=department_sex_stacked_bar(data.department_sex_totals)
                    ),
                    dcc.Graph(figure=age_group_histogram(data.age_group_totals)),
                ]
            ),
        ],
        style={
            "background": "#f8fafc",
            "color": "#0f172a",
            "fontFamily": "Arial, sans-serif",
            "minHeight": "100vh",
            "padding": "28px",
        },
    )


def _map_card(data: DashboardData) -> html.Div:
    """Crea una tarjeta amplia para apreciar mejor el mapa."""
    return html.Div(
        children=dcc.Graph(
            figure=department_map(data.department_totals, data.geojson),
            style={"height": "620px"},
            config={"displayModeBar": True, "responsive": True},
        ),
        style={**CARD_STYLE, "marginBottom": "22px"},
    )


def _header(data: DashboardData) -> html.Div:
    """Crea el encabezado con resumen general."""
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.H1(
                        "Mortalidad en Colombia, 2019",
                        style={"margin": "0 0 8px", "fontSize": "34px"},
                    ),
                    html.P(
                        "Tablero interactivo construido con Dash, Plotly y Polars.",
                        style={"margin": 0, "color": "#475569", "fontSize": "17px"},
                    ),
                ]
            ),
            html.Div(
                children=[
                    _metric_card("Muertes", f"{data.total_deaths:,}"),
                    _metric_card("Departamentos", f"{data.total_departments:,}"),
                    _metric_card("Municipios", f"{data.total_municipalities:,}"),
                ],
                style={
                    "display": "grid",
                    "gap": "12px",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(150px, 1fr))",
                    "marginTop": "22px",
                },
            ),
        ],
        style={**CARD_STYLE, "marginBottom": "22px"},
    )


def _metric_card(label: str, value: str) -> html.Div:
    """Crea una tarjeta sencilla para indicadores."""
    return html.Div(
        children=[
            html.Div(label, style={"color": "#64748b", "fontSize": "13px"}),
            html.Div(value, style={"fontSize": "25px", "fontWeight": 700}),
        ],
        style={
            "background": "#f1f5f9",
            "borderRadius": "12px",
            "padding": "14px",
        },
    )


def _graph_grid(graphs: list[dcc.Graph]) -> html.Div:
    """Organiza las graficas en una grilla adaptable."""
    return html.Div(
        children=[html.Div(graph, style=CARD_STYLE) for graph in graphs],
        style={
            "display": "grid",
            "gap": "18px",
            "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
            "marginBottom": "22px",
        },
    )


def _section_title(title: str) -> html.H2:
    """Crea un titulo de seccion."""
    return html.H2(title, style={"fontSize": "24px", "margin": "8px 0 14px"})


def _causes_table(data: DashboardData) -> html.Div:
    """Crea la tabla de las principales causas de muerte."""
    rows = [
        html.Tr(
            children=[
                html.Td(
                    str(row["codigo"]),
                    style={**TABLE_CELL_STYLE, "fontWeight": 700},
                ),
                html.Td(str(row["causa"]), style=TABLE_CELL_STYLE),
                html.Td(
                    f"{int(row['total']):,}",
                    style={**TABLE_CELL_STYLE, "textAlign": "right"},
                ),
            ]
        )
        for row in data.top_causes.iter_rows(named=True)
    ]

    return html.Div(
        children=html.Table(
            children=[
                html.Thead(
                    html.Tr(
                        children=[
                            html.Th("Codigo", style=TABLE_HEADER_STYLE),
                            html.Th("Causa", style=TABLE_HEADER_STYLE),
                            html.Th(
                                "Total",
                                style={**TABLE_HEADER_STYLE, "textAlign": "right"},
                            ),
                        ]
                    )
                ),
                html.Tbody(rows),
            ],
            style={
                "borderCollapse": "collapse",
                "fontSize": "14px",
                "width": "100%",
            },
        ),
        style={**CARD_STYLE, "marginBottom": "22px"},
    )


app = create_app()
server = app.server
