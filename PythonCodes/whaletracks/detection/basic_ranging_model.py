"""Analytic multipath travel-time model for whale-to-station ranging.

Given water depth, water and sediment sound speeds, and sediment thickness,
``basic_ranging`` returns theoretical differential arrival times (relative to
the direct water path ``t0``) as a function of source-receiver distance.

This straight-ray model is a first-order helper, **not** the source of the final
ranges: ``run_detection`` uses it only to size the multipath search window
(``dt_down = max(mp_interp - t0) + 0.2``). Final ranges come from the BELLHOP
ray-arrival tables in ``data/bellhop_arrival_models/`` via
``detection/range_estimation.py``.
"""

import math

import matplotlib.pyplot as plt
import numpy as np


def basic_ranging(depth, ss, sed_speed, t, plotflag=False):
    """Compute theoretical multipath arrival times versus distance.

    :param float depth: water depth (m)
    :param float ss: water-column sound speed (m/s)
    :param float sed_speed: sediment sound speed (m/s)
    :param float t: sediment thickness (m); if 0, basement arrivals are skipped
    :param bool plotflag: if True, scatter-plot the differential arrivals
    :return tuple: (distance, t0, t1, t2, t3, d_interp, mp_interp, mp_interp2)
        where t0..t3 are surface-reflected water-path arrival times and the
        ``*_interp`` arrays are basement (sub-seafloor) multipath arrivals
        interpolated onto the ``distance`` grid.
    """
    # Surface-bounce orders for the waterborne arrivals.
    n0, n1, n2, n3 = 0, 1, 2, 3

    distance = np.linspace(0, 20000, 2001, endpoint=True)  # waterborne arrivals
    theta1s = np.linspace(0, 3.14 / 4, 150, endpoint=True)  # subsurface arrivals

    # Waterborne arrival calculations
    t0 = [((2 * n0 + 1) * math.sqrt((d / (2 * n0 + 1)) ** 2 + depth**2)) / ss for d in distance]
    t1 = [((2 * n1 + 1) * math.sqrt((d / (2 * n1 + 1)) ** 2 + depth**2)) / ss for d in distance]
    t2 = [((2 * n2 + 1) * math.sqrt((d / (2 * n2 + 1)) ** 2 + depth**2)) / ss for d in distance]
    t3 = [((2 * n3 + 1) * math.sqrt((d / (2 * n3 + 1)) ** 2 + depth**2)) / ss for d in distance]

    # Basement (sub-seafloor) arrival calculations
    if t > 0:
        theta2s = [math.asin(sed_speed * math.sin(theta1) / ss) for theta1 in theta1s]
        d_dbs = [
            math.sqrt((depth / math.cos(theta1)) ** 2 - depth**2)
            + 2
            * math.sqrt((t / (math.cos(math.asin(sed_speed * math.sin(theta1) / ss)))) ** 2 - t**2)
            for theta1 in theta1s
        ]
        d_mpbs = [
            3 * math.sqrt((depth / math.cos(theta1)) ** 2 - depth**2)
            + 2
            * math.sqrt((t / (math.cos(math.asin(sed_speed * math.sin(theta1) / ss)))) ** 2 - t**2)
            for theta1 in theta1s
        ]
        d_mpb2s = [
            3 * math.sqrt((depth / math.cos(theta1)) ** 2 - depth**2)
            + 4
            * math.sqrt((t / (math.cos(math.asin(sed_speed * math.sin(theta1) / ss)))) ** 2 - t**2)
            for theta1 in theta1s
        ]
        H1 = [depth / math.cos(theta1) for theta1 in theta1s]
        H2 = [t / math.cos(theta2) for theta2 in theta2s]
        inds = np.arange(len(H1))
        TT_db = [H1[j] / ss + (2 * H2[j]) / sed_speed for j in inds]
        TT_mpb = [(3 * H1[j] / ss) + (2 * H2[j]) / sed_speed for j in inds]
        TT_mpb2 = [(3 * H1[j] / ss) + (4 * H2[j]) / sed_speed for j in inds]

        # Interpolate basement arrivals onto the water-column distance grid.
        d_interp = np.interp(distance, d_dbs, TT_db)
        mp_interp = np.interp(distance, d_mpbs, TT_mpb)
        mp_interp2 = np.interp(distance, d_mpb2s, TT_mpb2)
    else:
        d_interp = []
        mp_interp = []
        mp_interp2 = []

    if plotflag:
        plt.scatter(distance, np.subtract(t0, t0))
        plt.scatter(distance, np.subtract(d_interp, t0))
        plt.scatter(distance, np.subtract(t1, t0))
        plt.scatter(distance, np.subtract(mp_interp, t0))
        plt.scatter(distance, np.subtract(mp_interp2, t0))
        plt.scatter(distance, np.subtract(t2, t0))
        plt.scatter(distance, np.subtract(t3, t0))
        plt.show()

    return (distance, t0, t1, t2, t3, d_interp, mp_interp, mp_interp2)
