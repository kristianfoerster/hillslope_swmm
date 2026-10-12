#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 10:17:47 2026

@author: kristianfoerster
"""

from pathlib import Path


def build_swmm_model(
    output_file="hillslope_model.inp",
    hourly_intensity = 5.,
    slope_percent=5.0,
    curve_number=75.0,
    dx = 50,
    dy = 150,
    n = 6
):
    """
    Erzeugt eine einfache SWMM-INP-Datei für ein idealisiertes Hangmodell.

    Modellannahmen:
    - Einzugsgebiet: 300 x 150 m
    - Sechs Teilflächen mit je 7.500 m²
    - Vereinfachte serielle Abflussverbindung
    - Ein gemeinsamer Gebietsauslass
    - Konstanter Niederschlag während der ersten Stunde

    Die hydrologischen Parameter sind Demonstrationswerte,
    keine kalibrierten Werte für ein reales Einzugsgebiet.
    """

    output_file = Path(output_file)

    # Sechs Teilflächen mit jeweils 7.500 m²
    #subcatchment_area_ha = 0.75
    
    #n = 6
    #dx = 50
    #dy = 150
    
    subcatchment_area_ha = dx * dy * 1.-4
    
    # positions of junctions
    #node_x = {
    #    "N1": 250,
    #    "N2": 200,
    #    "N3": 150,
    #    "N4": 100,
    #    "N5": 50,
    #    "N6": 10,
    #    "OUT1": 0,
    #}
    node_x = dict()
    for i in range(0,n):
        i1 = i+1
        x = n * dx - i * dx
        node_x[f"N{i1}"] = x
    node_x["OUT1"]=0
    
    lines = [
        "[TITLE]",
        "Idealized hillslope model - six serial subcatchments",
        "",
        "[OPTIONS]",
        "FLOW_UNITS           CMS",
#        "INFILTRATION         HORTON",
        "INFILTRATION         CURVE_NUMBER",
        "FLOW_ROUTING         DYNWAVE",
        "START_DATE           06/01/2025",
        "START_TIME           00:00:00",
        "REPORT_START_DATE    06/01/2025",
        "REPORT_START_TIME    00:00:00",
        "END_DATE             06/29/2025",
        "END_TIME             00:00:00",
        "SWEEP_START          01/01",
        "SWEEP_END            12/31",
        "DRY_DAYS             0",
        "REPORT_STEP          00:15:00",
        "WET_STEP             00:01:00",
        "DRY_STEP             01:00:00",
        "ROUTING_STEP         00:00:30",
        "ALLOW_PONDING        NO",
        "INERTIAL_DAMPING     PARTIAL",
        "VARIABLE_STEP        0.75",
        "LENGTHENING_STEP     0",
        "MIN_SURFAREA         1.0",
        "SKIP_STEADY_STATE    NO",
        "",
        "[EVAPORATION]",
        "CONSTANT 5.0",
        "",
        "[RAINGAGES]",
        "RG1 VOLUME 1:00 1.0 TIMESERIES RainSeries",
        "",
        "[TIMESERIES]",
        "RainSeries 06/01/2025 00:00 0.0",
        f"RainSeries 06/01/2025 01:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 02:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 03:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 04:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 05:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 06:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 07:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 08:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 09:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 10:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 11:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 12:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 13:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 14:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 15:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 16:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 17:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 18:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 19:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 20:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 21:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 22:00 {hourly_intensity}",
        f"RainSeries 06/01/2025 23:00 {hourly_intensity}",
        f"RainSeries 06/02/2025 00:00 {hourly_intensity}",
        "RainSeries 06/02/2025 01:00 0.0",
        "",        "",
        "[SUBCATCHMENTS]",
        "; Name RainGage Outlet Area(ha) %Imperv Width(m) Slope(%) CurbLen(m)",
    ]

    for i in range(1, n+1):
        outlet = f"N{i}"
        lines.append(
            f"S{i} RG1 {outlet} {subcatchment_area_ha:.3f} "
            f"0.0 {dy} {slope_percent:.2f} 0.0"
        )

    lines += [
        "",
        "[SUBAREAS]",
        "; Subcatchment N-Imperv N-Perv S-Imperv S-Perv PctZero RouteTo PctRouted",
    ]

    for i in range(1, n+1):
        lines.append(f"S{i} 0.01 0.15 1.5 5.0 25.0 OUTLET 100")

    lines += [
        "",
        "[INFILTRATION]",
        "; Subcatchment MaxRate MinRate Decay DryTime MaxInfil",
    ]

    for i in range(1, n+1):
        # lines.append(f"S{i} {max_infiltration_rate:.2f} 4.0 3.0 7.0 0.0") # horton
        lines.append(f"S{i} {curve_number:.2f} 0.0 7")

    lines += [
        "",
        "[JUNCTIONS]",
        "; Name Elevation(m) MaxDepth(m) InitDepth(m) SurDepth(m) Aponded(m2)",
    ]
    
    last_id = f"N{n}"
    outlet_x = node_x[last_id]
    for i in range(1, n+1):
        elevation = (node_x[f"N{i}"] - outlet_x) * slope_percent / 100.0
        lines.append(f"N{i} {elevation:.2f} 2.0 0.0 0.0 0.0")

    lines += [
        "",
        "[OUTFALLS]",
        "; Name Elevation(m) Type StageData Gated RouteTo",
        f"OUT1 {-slope_percent / 100.0 * (node_x['N6'] - node_x['OUT1']):.2f} FREE NO",
        "",
        "[CONDUITS]",
        "; Name FromNode ToNode Length(m) Roughness InOffset OutOffset InitFlow MaxFlow",
    ]

    for i in range(1, n):
        length = abs(node_x[f"N{i}"] - node_x[f"N{i + 1}"])
        lines.append(
            f"C{i} N{i} N{i + 1} {length:.1f} 0.035 0.0 0.0 0.0 0.0"
        )

    length = abs(node_x[last_id] - node_x["OUT1"])
    lines.append(
        f"C{n} N{n} OUT1 {length:.1f} 0.035 0.0 0.0 0.0 0.0"
    )
    
    lines += [
        "",
        "[XSECTIONS]",
        "; Conduit Shape Geom1 Geom2 Geom3 Geom4 Barrels",
    ]

    for i in range(1, n+1):
        lines.append(f"C{i} CIRCULAR 0.30 0.0 0.0 0.0 1")

    lines += [
        "",
        "[REPORT]",
        "INPUT YES",
        "CONTROLS NO",
        "SUBCATCHMENTS ALL",
        "NODES ALL",
        "LINKS ALL",
        "",
        "[MAP]",
        "DIMENSIONS 0 0 300 150",
        "Units METERS",
        "",
        "[COORDINATES]",
        *[f"N{i} {node_x[f'N{i}']} 25" for i in range(1, 7)],
        f"OUT1 {node_x['OUT1']} 25",
        "",
        "",
        "[POLYGONS]",
        #"S1 250 0",
        #"S1 300 0",
        #"S1 300 150",
        #"S1 250 150",
        #"S2 200 0",
        #"S2 250 0",
        #"S2 250 150",
        #"S2 200 150",
        #"S3 150 0",
        #"S3 200 0",
        #"S3 200 150",
        #"S3 150 150",
        #"S4 100 0",
        #"S4 150 0",
        #"S4 150 150",
        #"S4 100 150",
        #"S5 50 0",
        #"S5 100 0",
        #"S5 100 150",
        #"S5 50 150",
        #"S6 0 0",
        #"S6 50 0",
        #"S6 50 150",
        #"S6 0 150",
        #"",
    ]
    
    for i in range(0,n):
        i1 = i+1
        sid = f"N{i1}"
        lines+=[f"S{i1} {node_x[sid]} 0",
            f"S{i1} {node_x[sid]+dx} 0",
            f"S{i1} {node_x[sid]+dx} 150",
            f"S{i1} {node_x[sid]} 150"]    
    
    output_file.write_text("\n".join(lines), encoding="utf-8")

    return output_file