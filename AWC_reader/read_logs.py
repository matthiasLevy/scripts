#!/usr/bin/env python3

import datetime
from io import StringIO
from typing import Union

import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objs._figure
from path import Path
from plotly import express as px


class AWC_log_reader:
    """
    Simple class to read files from a specific folder and prepare plots
    """

    # Using Plotly as default plot for pandas
    pd.set_option("plotting.backend", "plotly")

    FORMAT_DATE = '%Y%m%d'
    FORMAT_DATETIME = '%Y%m%d_%H%M%S'

    def __init__(self, folder_base):
        self.folder_base = folder_base

    def _read_file_dt(self, filename):
        return datetime.datetime.strptime(
            Path(filename).stem.split('-')[0], self.FORMAT_DATETIME
        )

    def search_last_file_content(
        self, start_dt: Union[str, datetime.datetime] = None, nb_hours=24
    ):
        # folder /= '20221017'
        self.files = pd.DataFrame(
            data=self.folder_base.walk('*AWC*.log'), columns=['path']
        )

        self.files['dt'] = [self._read_file_dt(f) for f in self.files]

        self.files.sort_values(by='dt')
        if not start_dt:
            self.files.sort(key=self._read_file_dt())[-1:]
        else:
            if not isinstance(start_dt, datetime.datetime):
                start_dt = datetime.datetime.strptime(start_dt, self.FORMAT_DATETIME)
            files

        files = [f for f in files if f.get]
        file = files[-1]

        # date_file = datetime.datetime.strptime(file.basename()[:8], format='%Y%m%d')
        date_file_str = file.basename()[:8]

        if date_file_str > '20221013':
            file_content = file
        else:
            file_content = file.open('r').read()
            file_content = StringIO(file_content.replace(';\n', '\n'))
        return file_content

    def read_file_data(file_content, skip_lines=0):
        lines_skipped = [0] + list(range(2, 2 + skip_lines))
        data = pd.read_csv(
            file_content,
            sep=';',
            header=0,
            skiprows=lines_skipped,
            decimal='.',
            parse_dates=True,
            index_col=0,
            dayfirst=True,
        )

        data.columns = data.columns.str.replace(' ', '')
        # Timestamp_UTC; P[W]; Q[VAr]; U_L1L2[V]; U_L2L3[V]; U_L3L1[V]; I_L1[A]; I_L2[A]; I_L3[A]; f[Hz]; PMin[W]; PMax[W]; P_setYuso[W];   Q_setYuso[W]; P_setToTSC[W]; Q_setToTSC[W]; P_setReadback[W]; Q_setReadback[W]; E[Wh]; E_PMax[Wh]

        data['E[MWh]'] = data['E[Wh]'] / 1000000
        # Calculate average Voltage
        data['U_avg'] = data[[c for c in data.columns if 'U_L' in c]].mean(axis=1)
        return data

    def select_last_data(data, minutes=5):
        # date_detail = '20221014_152300'
        # start = datetime.datetime.strptime(date_detail, '%Y%m%d_%H%M%S')
        # end = start + datetime.timedelta(minutes=15)

        end = data.index[-1]
        start = end - datetime.timedelta(minutes=minutes)

        return data[(data.index >= start) & (data.index <= end)]


folder = Path(
    r'/mnt/g/.shortcut-targets-by-id/1zJg6xXMQtwsL4z7K86PE8FS6FspMhFec/04_PROJETS/21_Deux-Acren/13_EXECUTION/Réception/Tests préalables/DEIF-exports: Invalid argument'
)
folder = Path(r'/mnt/c/Users/MLevy/Documents/2Acren')

# folder /= '20221017'
files = list(folder.walk('*AWC*.log'))
files.sort(key=Path.getmtime)

file = files[-1]

# date_file = datetime.datetime.strptime(file.basename()[:8], format='%Y%m%d')
date_file_str = file.basename()[:8]

if date_file_str > '20221013':
    file_content = file
else:
    file_content = file.open('r').read()
    file_content = StringIO(file_content.replace(';\n', '\n'))

data = pd.read_csv(
    file_content,
    sep=';',
    header=0,
    skiprows=1,
    decimal='.',
    parse_dates=True,
    index_col=0,
    dayfirst=True,
)


# Timestamp_UTC; P[W]; Q[VAr]; U_L1L2[V]; U_L2L3[V]; U_L3L1[V]; I_L1[A]; I_L2[A]; I_L3[A]; f[Hz]; PMin[W]; PMax[W]; P_setYuso[W]; Q_setYuso[W]; P_setToTSC[W]; Q_setToTSC[W]; P_setReadback[W]; Q_setReadback[W]; E[Wh]; E_PMax[Wh]

data_resample = data.resample('200ms').mean()
data_resample = data.resample('1S').mean()


def plot_df(data):
    # Simple time plot

    figure: plotly.graph_objs._figure.Figure = data[
        [
            ' P_setYuso[W]',
            ' P[W]',
            # ' Q_setYuso[W]',' Q[VAr]'
        ]
    ].plot()

    # Calculate average Voltage
    data['U_avg'] = data[[c for c in data.columns if 'U_L' in c]].mean(axis=1)

    # Plot all reactive power columns
    for c in [c for c in data.columns if 'Q' in c]:
        figure.add_trace(go.Scatter(x=data.index, y=data[c].values, name=c, yaxis="y1"))

    figure.add_trace(
        go.Scatter(x=data.index, y=data[' f[Hz]'].values, name="freq", yaxis="y2")
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data['U_avg'].values, name="U_avg", yaxis="y3")
    )

    figure.update_layout(
        xaxis=dict(domain=[0, 0.9]),
        yaxis=dict(
            title="Power",
            # titlefont=dict(
            # color="#1f77b4"
            # ),
            # tickfont=dict(
            # color="#1f77b4"
            # )
        ),
        yaxis2=dict(
            title="Freq",
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
            title="U (V)",
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
        hovermode="x",
    )
    figure.update_traces(hovertemplate=None)
    figure.update_layout(hovermode="x")
    return figure


figure = plot_df(data_resample)
figure.write_html(file.replace(file.ext, '.html'))
# figure.show()

detail_plot = True
# detail_plot = False

if detail_plot:
    date_detail = '20221014_152300'
    start = datetime.datetime.strptime(date_detail, '%Y%m%d_%H%M%S')

    if start < data.index[0] or start > data.index[-1]:
        # start = data.index[int(len(data)/2)]
        start = data.index[0]

    end = start + datetime.timedelta(minutes=15)

    end = data.index[-1]
    start = end - datetime.timedelta(minutes=5)

    data_detail = data[(data.index >= start) & (data.index <= end)]

    figure_detail = plot_df(data_detail)
    figure_detail.write_html(file.replace(file.ext, '_detail.html', fileopt='extend'))

if __name__ == '__main__':
    folder = Path(r'C:\Users\MLevy\Documents\2Acren')
