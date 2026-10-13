#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 12:58:10 2026

@author: kristianfoerster
"""

from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pyswmm import Simulation, Nodes, RainGages, Subcatchments
import swmmio

from model_builder import build_swmm_model

from matplotlib.patches import Rectangle, Polygon

def build_model(inp_file):

    # Build model
    build_swmm_model(
        output_file=inp_file,
        hourly_intensity=hourly_intensity,
        slope_percent=slope_percent,
        curve_number=curve_number,
        dx = val_dx,
        dy = val_dy,
        n = val_n
    )

    #st.write("### Parameters:")
    #st.write(f"Curve Number: {curve_number}")
    #st.write(f"Slope: {slope_percent:.1f} %")
    #st.write(f"Rainfall intensity: {hourly_intensity:.1f} mm/h")


def model_vis(inp_file):
    # --------------------------------------------------
    # Model visualization
    # --------------------------------------------------
    
    #st.subheader("SWMM model")
    
    model = swmmio.Model(str(inp_file))
    
    fig_model, ax_model = plt.subplots(figsize=(12, 6))

    # areas: read polygons from INP file
    inp_path = Path(inp_file)

    with open(inp_path, "r") as f:
        lines = f.readlines()

    in_polygons = False
    polygons = {}

    for line in lines:
        line = line.strip()

        if line.startswith("["):
            in_polygons = line.upper() == "[POLYGONS]"
            continue

        if not in_polygons or not line or line.startswith(";"):
            continue

        parts = line.split()

        if len(parts) >= 3:
            name = parts[0]
            x = float(parts[1])
            y = float(parts[2])

            polygons.setdefault(name, []).append((x, y))

    for name, points in polygons.items():
        area = Polygon(
            points,
            closed=True,
            facecolor="lightblue",
            edgecolor="steelblue",
            alpha=0.4,
            linewidth=1.5,
            zorder=1,
        )
        ax_model.add_patch(area)

        # Label in the center of the polygon
        x_center = sum(p[0] for p in points) / len(points)
        y_center = sum(p[1] for p in points) / len(points)

        ax_model.text(
            x_center,
            y_center,
            f"{name}\n{val_dx*val_dy} m²",
            ha="center",
            va="center",
            fontsize=10,
            zorder=4,
        )

    
    # links
    links = model.links.geodataframe
    if not links.empty:
        links.plot(
            ax=ax_model,
            color="steelblue",
            linewidth=2,
            zorder=2,
        )
    
    # nodes
    nodes = model.nodes.geodataframe
    if not nodes.empty:
        nodes.plot(
            ax=ax_model,
            color="darkred",
            markersize=35,
            zorder=3,
        )
    
        # names
    for node_name, node in nodes.iterrows():
        point = node.geometry
        ax_model.annotate(
            str(node_name),
            (point.x, point.y),
            xytext=(4, 7),
            textcoords="offset points",
            fontsize=9,
        )
    
    ax_model.set_title("Idealized Hillslope SWMM model")
    ax_model.set_xlabel("X coordinate (m)")
    ax_model.set_ylabel("Y coordinate (m)")
    ax_model.set_aspect("equal", adjustable="datalim")
    ax_model.grid(True, alpha=0.3)
    
    
    #ax_model.set_xlim(-10, 270)
    #ax_model.set_ylim(-10, 165)
    st.pyplot(fig_model)
    plt.close(fig_model)

# --------------------------------------------------
# Seitenaufbau
# --------------------------------------------------

st.set_page_config(
    page_title="Idealized Hillslope SWMM",
    layout="wide",
)

st.title("Idealized Hillslope Model")
st.write(
    "Explore how the curve number and hillslope gradient "
    "affect runoff at the outlet."
)


# --------------------------------------------------
# Modellparameter
# --------------------------------------------------

st.sidebar.header("Model dimension & parameters")

val_dx = st.sidebar.slider(
    "Length dx",
    min_value=10.0,
    max_value=100.0,
    value=50.0,
    step=10.0,
)

val_dy = st.sidebar.slider(
    "Length dy",
    min_value=50.0,
    max_value=200.0,
    value=150.0,
    step=10.0,
)

val_n = st.sidebar.slider(
    "# of hillslope elements",
    min_value=1,
    max_value=10,
    value=6,
    step=1,
)

curve_number = st.sidebar.slider(
    "Curve Number",
    min_value=30.0,
    max_value=98.0,
    value=75.0,
    step=1.0,
)

slope_percent = st.sidebar.slider(
    "Slope (%)",
    min_value=0.5,
    max_value=15.0,
    value=5.0,
    step=0.5,
)

hourly_intensity = st.sidebar.number_input(
    "Rainfall intensity (mm/h)",
    min_value=0.0,
    max_value=100.0,
    value=5.0,
    step=1.0,
)

st.sidebar.caption(
    "The simulation starts when you click the button below."
)


run_simulation = st.sidebar.button(
    "Run SWMM simulation",
    type="primary",
    use_container_width=True,
)

workdir = Path("swmm_run")
workdir.mkdir(exist_ok=True)

filename = "hillslope_model.inp"
inp_file = workdir / filename

build_model(inp_file)
model_vis(inp_file)

# --------------------------------------------------
# Simulation
# --------------------------------------------------

if run_simulation: # st.button("Run SWMM simulation", type="primary"):

    #build_model(inp_file)

    try:
        # Run SWMM
        with Simulation(str(inp_file)) as sim:
            for _ in sim:
                pass

        st.success("SWMM simulation completed successfully.")

        # --------------------------------------------------
        # Outlet hydrograph
        # --------------------------------------------------

        out_file = inp_file.with_suffix(".out")

        if not out_file.exists():
            st.error(
                "The simulation did not produce an SWMM output file."
            )
            st.stop()
        
        times = []
        flows = []
        rainfall = []
        evaporation = []
        s1_runoff = []
        infiltration = []
        
        with Simulation(str(inp_file)) as sim:
            outlet = Nodes(sim)["OUT1"]
            rain_gage = RainGages(sim)["RG1"]
            subcatchment = Subcatchments(sim)["S1"]
        
            for _ in sim:
                times.append(sim.current_time)
                flows.append(outlet.total_inflow)
                
                rainfall.append(rain_gage.rainfall)
                evaporation.append(subcatchment.evaporation_loss)
                s1_runoff.append(subcatchment.runoff)
                infiltration.append(subcatchment.infiltration_loss)
        
        hydrograph = pd.DataFrame(
            {
                "Time": pd.to_datetime(times),
                "Discharge (m³/s)": flows,
            }
        )

        #st.subheader("Outlet hydrograph")

        df = pd.DataFrame(index=pd.to_datetime(times), data={
            #"flow": flows,
            "rainfall": rainfall,
            "evaporation": evaporation,
            "infiltration": infiltration,
            "runoff": s1_runoff
        }).resample('D').mean()

        # for display reasons:
        df.index = df.index + pd.Timedelta(hours=12)

        fig, axes = plt.subplots(5,1,figsize=(11, 8), sharex=True)

        #ax.plot(
        #    hydrograph["Time"],
        #    hydrograph["Discharge (m³/s)"],
        #)

        #ax.set_xlabel("Time")
        #ax.set_ylabel("Discharge (m³/s)")
        #ax.grid(True)


        axes[0].bar(
            df.index,
            df["rainfall"] * 24,
            width=1,
            color="#a6cee3"
        )
        axes[0].set_ylabel("P [mm/$\Delta t$]")
        axes[0].set_title("S1 Precipitation P")
        axes[0].grid(axis="y", alpha=0.3)

        axes[1].bar(
            df.index,
            df["evaporation"],
            width=1,
            color="#b2df8a"
        )
        axes[1].set_ylabel("ET [mm/$\Delta t$]")
        axes[1].set_title("S1 Evapotranspiration ET")
        axes[1].grid(axis="y", alpha=0.3)

        axes[2].bar(
            df.index,
            df["infiltration"] * 24,
            width=1,
            color="#fdbf6f"
        )
        axes[2].set_ylabel("Inf [mm/$\Delta t$]")
        axes[2].set_title("S1 Infiltration Inf")
        axes[2].grid(alpha=0.3)

        axes[3].bar(
            df.index,
            df["runoff"] * 86400 / (val_dx * val_dy) * 1000,
            width=1,
            color="#1f78b4"
        )
        axes[3].set_ylabel("R [mm/$\Delta t$]")
        axes[3].set_title("S1 Runoff R")
        axes[3].grid(axis="y", alpha=0.3)


        axes[4].plot(
            times,
            flows,
            color="#1f78b4"
        )
        axes[4].set_ylabel("Discharge [m³/s]")
        axes[4].set_xlabel("Time")
        axes[4].set_title("Total hillslope discharge")
        axes[4].grid(alpha=0.3)

        fig.tight_layout()

        fig.autofmt_xdate()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "The hydrograph shows the total inflow reported "
            "by PySWMM for node OUT1."
        )
        
        Sum_P = sum(df["rainfall"] * 24)
        Sum_E = sum(df["evaporation"])
        Sum_I = sum(df["infiltration"] * 24)
        Sum_R = sum(df["runoff"] * 86400 / (val_dx * val_dy) * 1000)
        dS    = Sum_P - Sum_R - Sum_E - Sum_I
        
        st.code(f"S1 Precipitation:      {Sum_P:>8.1f}\n"
                f"S1 Evapotranspiration: {Sum_E:>8.1f}\n"
                f"S1 Infiltration:       {Sum_I:>8.1f}\n"
                f"S1 Runoff:             {Sum_R:>8.1f}\n"
                f"S1 Delta S:            {dS:.1f}"
                 )

        # --------------------------------------------------
        # Download input file
        # --------------------------------------------------

        st.download_button(
            label="Download SWMM input file",
            data=inp_file.read_bytes(),
            file_name="hillslope_model.inp",
            mime="text/plain",
        )

    except Exception as error:
        st.error("The simulation or plotting failed.")
        st.exception(error)