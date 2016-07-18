import datetime
from time import process_time
import matplotlib.pyplot as plt
import loadearthquake as eaq
import loadmagnetic as mag
import plot as pt
import pyculiarity.detect_ts as pyc
import stationsdata as station
import pandas as pd
import bandfilter as bf
import statsmodels.api as sm
import detectanomalies as anom
import seaborn as sb
import numpy as np


def compute_anomalies(mag):
    return get_anom(mag, 'X'), get_anom(mag, 'Y'), get_anom(mag, 'Z')


def get_anom(magnetic, column):
    print("Detecting anomalies for", column, "axis", end='')
    start = process_time()

    df = magnetic[['Date', column]]
    df.columns = ["timestamp", "value"]

    # df = df[df.value < 5]

    # TODO: mess around with maximum_anomalies and alpha to improve resulting plots
    eq_anom = pyc.detect_ts(df, maximum_anomalies=0.025, direction='pos', alpha=0.05)

    print(" --- took", round(process_time() - start, 2), " s")
    return eq_anom['anoms']


def compute_anomalies_for_earthquake(eq, anomalies, time=24):
    x, y, z = anomalies
    anoms = comp_anom_for_eq(eq, x, time), comp_anom_for_eq(eq, y, time), comp_anom_for_eq(eq, z, time)
    return pd.DataFrame({'X_anoms': anoms[0],
                         'Y_anoms': anoms[1],
                         'Z_anoms': anoms[2]},
                        index=eq.index)


def comp_anom_for_eq(earthquake, anomaly, interval):
    X_anoms = []

    for index, row in earthquake.iterrows():
        end = index
        start = end - datetime.timedelta(hours=interval)
        tempX = anomaly[start:end]

        X_anoms.append(len(tempX.index))

    return X_anoms


def anomaly_rate(magnetic, anomalies, num_h=4):
    mag_interval = magnetic.resample('10T').mean()

    anom_rate = []
    for index, row in mag_interval.iterrows():
        end = index
        start = end - datetime.timedelta(hours=num_h)
        temp = anomalies.anoms[start:end]
        anom_rate.append(len(temp.index)/num_h)

    anom_r = pd.DataFrame()
    anom_r['anom_r'] = pd.Series(anom_rate)
    anom_r['log_anom_r'] = np.log(anom_r['anom_r'])
    anom_r.index = mag_interval.index
    anom_r = anom_r[anom_r.log_anom_r >= 0]
    anom_r['log_z_score'] = ((anom_r['log_anom_r']-anom_r['log_anom_r'].mean())/anom_r['log_anom_r'].std())
    anom_r['log_z_score_zero_trans'] = anom_r.log_z_score + abs(anom_r['log_z_score'].min())
    anom_r['Date'] = anom_r.index
   
    return anom_r