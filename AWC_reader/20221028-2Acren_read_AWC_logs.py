#!/usr/bin/env python3

import datetime
import sys
from argparse import ArgumentParser
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objs._figure
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from path import Path
from plotly import express as px

# Using Plotly as default plot for pandas
pd.set_option("plotting.backend", "plotly")

FORMAT_DATETIME = '%Y%m%d_%H%M%S'
COLORS = dict(P='blue', Q='red', U='green', P_TSC='cyan', Q_TSC='orange')

# dict of traces by name
TRACES = [
    dict(
        column='E[kWh]',
        ratio=1000,
        name='E[MWh]',
        yaxis='y4',
        color='firebrick',
        dash='dash',
        width=2,
    ),
    dict(
        column='P[kW]', ratio=1000, name='P[W]', yaxis='y1', color='blue', dash='solid'
    ),
    dict(
        column='Q[kvar]',
        ratio=1000,
        name='Q[VAr]',
        yaxis='y1',
        color='red',
        dash='solid',
    ),
    dict(
        column='P[kW]', ratio=1000, name='P[W]', yaxis='y1', color='blue', dash='solid'
    ),
    dict(
        column='Q_set[VAr]',
        ratio=1000,
        name='Q_set[VAr]',
        yaxis='y1',
        color='blue',
        dash='solid',
    ),
    dict(colums='P_TSC[kW]', name='P_TSC'),
    dict(colums='Q_TSC[kW]', name='Q_TSC'),
]

freq_resample = '5S'  # resampling frequency or None
freq_update = 2  # seconds

detail_duration_minutes = 30


def _read_file_dt(filename):
    return datetime.datetime.strptime(
        Path(filename).stem.split('-')[0], FORMAT_DATETIME
    )


def search_last_file_content(folder, replace_semicolon=False):
    # folder /= '20221017'
    files = list(folder.walk('*AWC*.log'))
    files.sort(key=_read_file_dt)

    file = files[-1]

    if not replace_semicolon:
        return file

    date_file_str = file.basename()[:8]

    if date_file_str > '20221013':
        file_content = file
    else:
        file_content = file.open('r').read()
        file_content = StringIO(file_content.replace(';\n', '\n'))
    return file_content


def read_file_data(file_content, skip_lines=0):
    line_headers = 0
    with file.open() as f:
        line1 = f.readline()
    if 'putty' in line1.lower():
        line_headers = 1

    lines_skipped = list(range(0, line_headers)) + list(
        range(line_headers + 1, line_headers + 1 + skip_lines)
    )
    # lines_skipped = list(range(1, 1 + skip_lines))
    data = pd.read_csv(
        file_content,
        sep=';',
        header=0,
        skiprows=lines_skipped,
        decimal='.',
        parse_dates=True,
        index_col=0,
        dayfirst=True,
        # usecols=[0, 23]
    )

    data.columns = data.columns.str.replace(' ', '')
    # Timestamp_UTC; P[kW]; Q[kVAr]; U_L1L2[V]; U_L2L3[V]; U_L3L1[V]; I_L1[A]; I_L2[A]; I_L3[A]; f[Hz]; PMin[kW]; PMax[kW]; P_setYuso[kW];   Q_setYuso[kW]; P_setToTSC[kW]; Q_setToTSC[kW]; P_setReadback[kW]; Q_setReadback[kW]; E[Wh]; E_PMax[Wh]
    # Timestamp_UTC; P[kW]; Q[kvar]; U_L1L2[V]; U_L2L3[V]; U_L3L1[V]; I_L1[A]; I_L2[A]; I_L3[A]; f[mHz]; PMin[kW]; PMax[kW]; P_set[kW]; Q_set[kW]; P_setToTSC[kW]; Q_setToTSC[kW]; P_setReadback[kW]; Q_setReadback[kW]; E[kWh]; E_PMax[kWh]; P_TSC[kW]; Q_TSC[kW]; Q(U) Inputs/Outputs:; 1;2;3;4;5;6
    try:
        data['E[MWh]'] = data['E[Wh]'] / 1000000
    except Exception:
        data['E[MWh]'] = data['E[kWh]'] / 1000

    data['PMin[W]'] = data['PMin[kW]'] * 1000
    data['PMax[W]'] = data['PMax[kW]'] * 1000
    data['P_set[W]'] = data['P_setToTSC[kW]'] * 1000

    data['P[W]'] = data['P[kW]'] * 1000
    data['P[W]'] = data['P[kW]'] * 1000

    data['Q[VAr]'] = data['Q[kvar]'] * 1000
    data['Q_set[VAr]'] = data['Q_setToTSC[kW]'] * 1000

    data['P_TSC[W]'] = data['P_TSC[kW]'] * 1000
    data['Q_TSC[W]'] = data['Q_TSC[kW]'] * 1000

    data['f[Hz]'] = data['f[mHz]'] / 1000
    # Calculate average Voltage
    data['U_avg'] = data[[c for c in data.columns if 'U_L' in c]].mean(axis=1)
    data = data.tz_localize('UTC').tz_convert('Europe/Paris')

    data.index.name = 'Time (CET)'
    return data


def update_figure(fig, data, cols_dict=[]):

    if isinstance(fig, plotly.graph_objs._figure.Figure):
        with fig.batch_update():
            for data_i in fig['data']:
                data_i.x = data.index
                if data_i.name in cols_dict:
                    name = cols_dict[data_i.name]
                else:
                    name = data_i.name

                if name in data.columns:
                    data_i.y = data[name].values
                else:
                    print(f"{name} not found in data.columns : {data.columns}")
    else:
        for data_i in fig['data']:
            data_i['x'] = data.index
            if data_i['name'] in cols_dict:
                name = cols_dict[data_i['name']]
            else:
                name = data_i['name']

            if name in data.columns:
                data_i['y'] = data[name].values
            else:
                print(f"{name} not found in data.columns : {data.columns}")

    # return fig


def plot_df(data, slider=False):

    # Simple time plot
    cols_dict = {}

    figure: plotly.graph_objs._figure.Figure = plotly.tools.make_subplots()

    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data['f[Hz]'].values,
            name="freq",
            yaxis="y2",
            line=dict(color='lightgrey'),
            visible='legendonly',
        )
    )
    cols_dict['freq'] = 'f[Hz]'

    figure.add_trace(
        go.Scatter(x=data.index, y=data['U_avg'].values, name="U_avg", yaxis="y3")
    )

    figure.add_trace(
        go.Scatter(x=data.index, y=data['P_set[W]'].values, name='P_set[W]', yaxis="y1")
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data['P[W]'].values,
            name='P[W]',
            yaxis="y1",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data.index, y=data['Q_set[VAr]'].values, name='Q_set[VAr]', yaxis="y1"
        )
    )

    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data['Q[VAr]'].values,
            name='Q[VAr]',
            yaxis="y1",
            line=dict(color=COLORS['Q']),
        )
    )

    for c in ['PMin[kW]', 'PMax[kW]']:
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=data[c].values,
                name=c,
                yaxis="y1",
                legendgroup='G-Flex',
            )
        )
    for trace in figure.data:
        if 'P' in trace.name:
            trace.line.color = COLORS['P']
        elif 'Q' in trace.name:
            trace.line.color = COLORS['Q']
        if 'set[' in trace.name:
            trace.line.dash = 'dash'
        if trace.legendgroup == 'G-Flex':
            trace.line.update(width=1, dash='dot')
        if trace.name in COLORS:
            trace.line.color = COLORS[trace.name]
        elif 'Q_TSC' in trace.name:
            trace.line.color = 'orance'

    # Plot all reactive power columns
    # for c in [ c for c in data.columns if 'Q' in c]:
    #     figure.add_trace(go.Scatter(x=data.index, y=data[c].values, name=c , yaxis="y1"))

    if 'E[MWh]' not in data.columns:
        print(f"'E[MWh]' not found in data.columns : {data.columns}")
    else:
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=data['E[MWh]'].values,
                name="E[MWh]",
                yaxis="y4",
                line=dict(color='firebrick', width=2, dash='dash'),
            )
        )

    figure.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        xaxis=dict(domain=[0.05, 0.95]),
        yaxis=dict(
            title="Power(W)",
            # titlefont=dict(
            # color="#1f77b4"
            # ),
            # tickfont=dict(
            # color="#1f77b4"
            # )
            position=0.0,
            range=[-55e6, 55e6],
        ),
        yaxis2=dict(
            title="Freq(Hz)",
            # titlefont=dict(
            # color="#ff7f0e"
            # ),
            # tickfont=dict(
            # color="#ff7f0e"
            # ),
            # anchor="free",
            overlaying="y",
            side="right",
            position=0.9,
        ),
        yaxis3=dict(
            title="U(V)",
            # titlefont=dict(
            # color="#ff7f0e"
            # ),
            # tickfont=dict(
            # color="#ff7f0e"
            # ),
            # anchor="free",
            overlaying="y",
            side="right",
            position=1,
        ),
        yaxis4=dict(
            title="E(MWh)",
            # titlefont=dict(
            # color="#ff7f0e"
            # ),
            # tickfont=dict(
            # color="#ff7f0e"
            # ),
            # anchor="free",
            overlaying="y",
            # side="left",
            position=0.05,
            range=[-5, 110],
            ticklabelposition="inside",
            tick0=0,
            dtick=20,
        ),
        hovermode="x",
        legend=dict(
            orientation="h",
            # yanchor='bottom',  # ['auto', 'top', 'middle', 'bottom']
            # y=0,
            # xanchor='center',  # ['auto', 'left', 'center', 'right']
            # x=0.5
        ),
    )
    figure.update_traces(hovertemplate=None)
    figure.update_layout(hovermode="x")
    # if slider:
    #     figure.update_xaxes(rangeslider_visible=True)

    return figure, cols_dict


def select_last_data(data, minutes=5):
    # date_detail = '20221014_152300'
    # start = datetime.datetime.strptime(date_detail, '%Y%m%d_%H%M%S')
    # end = start + datetime.timedelta(minutes=15)

    end = data.index[-1]
    start = end - datetime.timedelta(minutes=minutes)

    return data[(data.index >= start) & (data.index <= end)]


def make_app_store(name, figure, fig_detail):
    app = Dash(name)
    app.layout = html.Div(
        children=[
            # html.H1(children=name),
            # html.Div(children='''
            # Dash: A web application framework for your data.
            # '''),
            dcc.Graph(id='graph_detail', figure=fig_detail),
            dcc.Graph(id='graph_all', figure=figure),
            dcc.Interval(
                id='interval-component',
                interval=freq_update * 1000,  # in milliseconds
                n_intervals=0,
            ),
        ]
    )
    return app


def parse_args(args=[]):
    parser = ArgumentParser(description="Plot AWC logs.")
    parser.add_argument(
        "file",
        action="store",
        nargs='?',
        default=0,
        help="Specify a file to plot. If not specified, plots the last one.",
    )
    parser.add_argument(
        "--write",
        "-w",
        dest='write',
        action="store_true",
        default=None,
        help="Writes the html files of the plots.",
    )
    parser.add_argument(
        "--plot",
        "-p",
        dest='plot',
        action="store_true",
        default=None,
        help="Show the independant plots.",
    )
    parser.add_argument(
        "--update",
        "-u",
        dest='update',
        action="store_true",
        default=None,
        help="Launch the app for updating plots",
    )
    parser.add_argument(
        "--detail",
        "-d",
        dest='detail',
        action="store_true",
        default=None,
        help="Plots a detailed graph separatly",
    )
    parser.add_argument(
        "--skip_lines",
        "-s",
        dest='skip',
        action="store",
        default=0,
        help="Lines to skip at start of data",
    )
    if Path(args).basename() == 'pydevconsole.py':
        args = args[3:]
    else:
        args = args[1:]
    # if not len(args) or '-u' in args or '--update' in args:
    #     args.append(0)

    return parser.parse_args(args)


if __name__ == '__main__':
    folder = Path(r'C:\Users\MLevy\Documents\2Acren')
    args = parse_args(sys.argv)

    if args.file:
        if Path(args.file).exists():
            file = args.file
        else:
            file = folder / args.file
    else:
        file = search_last_file_content(folder)

    print(f"Reading file {file}")
    data = read_file_data(file, int(args.skip))
    nb_lines_read = len(data)

    try:
        assert isinstance(data.index, pd.DatetimeIndex)
    except AssertionError as err:
        print(f"### Error reading file {file}:\n{err}")
        print(data)
    if freq_resample:
        data_resample = data.resample(freq_resample).mean()
    else:
        data_resample = data.copy()
    figure, _ = plot_df(data_resample)
    plot_all_resample = False

    detail_plot = True
    # detail_plot = False

    if args.detail or args.update:
        name = file.stem + '_detail'
        data_detail = select_last_data(data, detail_duration_minutes)
        figure_detail, cols_dict = plot_df(data_detail, slider=bool(args.file))

    if args.plot:
        figure.update_layout(title=file.stem)
        figure.show()
        if args.detail:
            figure_detail.update_layout(title=file.stem + '_detail')
            figure_detail.show()

    if args.write:
        figure.write_html(file.replace(file.ext, '.html'))
        if args.detail:
            figure_detail.write_html(
                file.replace(file.ext, '_detail.html')
            )  # , fileopt='extend'

    if args.update and not args.file:
        update_running = False
        app = make_app_store(name, figure, figure_detail)

        @app.callback(
            Output('graph_detail', 'figure'),
            Output('graph_all', 'figure'),
            # Output('data_store', 'data'),
            Input('interval-component', 'n_intervals'),
            Input('graph_detail', 'figure'),
            Input('graph_all', 'figure'),
        )
        def update_graph_detail(
            n,
            figure_detail,
            figure,
        ):
            global update_running
            global file
            global nb_lines_read
            global data_detail
            global data_resample
            global cols_dict
            # global figure, figure_detail

            # if n <= 30 / freq_update:
            #     print(f"#### No update at startup.")
            #     return figure_detail, figure
            if not update_running:
                update_running = True
                try:
                    # data = pd.read_json(data, dtype=float)
                    # print(f"data length:\n{len(data)}")
                    start = datetime.datetime.now()
                    data_new = read_file_data(file, skip_lines=nb_lines_read)
                    stop = datetime.datetime.now()
                    print(
                        f"{len(data_new)} lines read, {nb_lines_read} skipped in {(stop - start).total_seconds()} seconds."
                    )
                    nb_lines_read += len(data_new)
                    # print(f"start :{start}")
                    # print(f"stop :{stop}")

                    if len(data_new) > 0:
                        data_detail = select_last_data(
                            data_detail, detail_duration_minutes
                        )
                        data_detail = pd.concat(
                            [data_detail, data_new]
                        )  # .drop_duplicates()
                        # print(f"data_detail columns:\n{data_detail.columns}")

                        update_figure(figure_detail, data_detail, cols_dict)
                        # figure_detail, cols_dict = plot_df(data_detail)

                        data_resample_new = data_new.resample(freq_resample).mean()
                        data_resample = pd.concat([data_resample, data_resample_new])
                        data_resample = data_resample.groupby(
                            data_resample.index
                        ).last()
                        # print(f"data_resample columns:\n{data_resample.columns}")

                        update_figure(figure, data_resample, cols_dict)
                        # figure, _ = plot_df(data_resample)

                        # print(figure)
                        stop = datetime.datetime.now()
                        print(
                            f"Fig updated in {(stop - start).total_seconds()} seconds."
                        )
                except Exception as err:
                    print(f"Error updating: {err}")
                    raise err
                finally:
                    update_running = False
            else:
                print(f"#### Update already running! {nb_lines_read} lines read.")

            return figure_detail, figure  # , data

        print(f"Data loaded, {len(data)} lines read. Launching app")
        app.run_server()
