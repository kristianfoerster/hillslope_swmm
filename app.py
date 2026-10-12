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

from pyswmm import Simulation, Nodes
import swmmio

from model_builder import build_swmm_model

from matplotlib.patches import Rectangle

def build_model(file):
    workdir = Path("swmm_run")
    workdir.mkdir(exist_ok=True)

    inp_file = workdir / file

    # Build model
    build_swmm_model(
        output_file=inp_file,
        hourly_intensity=hourly_intensity,
        slope_percent=slope_percent,
        curve_number=curve_number,
    )

    st.write("### Parameters:")
    st.write(f"Curve Number: {curve_number}")
    st.write(f"Slope: {slope_percent:.1f} %")
    st.write(f"Rainfall intensity: {hourly_intensity:.1f} mm/h")


def model_vis(file):
    # --------------------------------------------------
    # Model visualization
    # --------------------------------------------------
    
    st.subheader("SWMM model")
    
    model = swmmio.Model(str(inp_file))
    
    fig_model, ax_model = plt.subplots(figsize=(12, 6))

    # areas
    # Einzugsgebiete als idealisierte Rechtecke darstellen
    for i in range(6):
        x = i * 50
    
        area = Rectangle(
            (x, 0),
            50,
            150,
            facecolor="lightblue",
            edgecolor="steelblue",
            alpha=0.4,
            linewidth=1.5,
            zorder=1,
        )
        ax_model.add_patch(area)
    
        ax_model.text(
            x + 25,
            75,
            f"S{i + 1}\n7.500 m²",
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
    
    
    ax_model.set_xlim(-10, 270)
    ax_model.set_ylim(-10, 165)
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

st.sidebar.header("Model parameters")

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

filename = "hillslope_model.inp"

build_model(filename)
model_vis(filename)

# --------------------------------------------------
# Simulation
# --------------------------------------------------

if run_simulation: # st.button("Run SWMM simulation", type="primary"):

    build_model()

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
        
        with Simulation(str(inp_file)) as sim:
            outlet = Nodes(sim)["OUT1"]
        
            for _ in sim:
                times.append(sim.current_time)
                flows.append(outlet.total_inflow)
        
        hydrograph = pd.DataFrame(
            {
                "Time": pd.to_datetime(times),
                "Discharge (m³/s)": flows,
            }
        )

        st.subheader("Outlet hydrograph")

        fig, ax = plt.subplots(figsize=(11, 4))

        ax.plot(
            hydrograph["Time"],
            hydrograph["Discharge (m³/s)"],
        )

        ax.set_xlabel("Time")
        ax.set_ylabel("Discharge (m³/s)")
        ax.grid(True)

        fig.autofmt_xdate()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "The hydrograph shows the total inflow reported "
            "by PySWMM for node OUT1."
        )

        model_vis()

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