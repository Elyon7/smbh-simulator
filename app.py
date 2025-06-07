import streamlit as st
import yt
from openai import OpenAI
from pathlib import Path
import os

# ---- CONFIGURATION ----
client = OpenAI()  # Usa OPENAI_API_KEY dall'ambiente
DATA_PATH = Path("/workspaces/smbh-simulator/simulation_data")
IMAGE_PATH = Path("/workspaces/smbh-simulator/pre_rendered_plots")
PLOT_OUTPUT = "output_plot.png"

# ---- FUNCTION: Generate slice plot using yt ----
def plot_slice(filename, field="density", axis="z"):
    ds = yt.load(filename)
    slc = yt.SlicePlot(ds, axis, field)
    slc.set_cmap(field, 'inferno')
    slc.save(".")  # Save to current directory
    return PLOT_OUTPUT

# ---- FUNCTION: AI Tutor Dialogue (updated for openai>=1.0.0) ----
def ask_ai(prompt):
    messages = [
        {"role": "system", "content": "You are an astrophysics tutor guiding students through black hole simulations. Ask questions and give suggestions to help them think like a scientist."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ---- STREAMLIT INTERFACE ----
st.set_page_config(page_title="SMBH Simulation Explorer", layout="wide")
st.title("🕳️ SMBH Simulation Explorer with AI Tutor")

# Step 1: Choose whether to use pre-rendered media or .phdf
use_image = st.sidebar.checkbox("Use pre-rendered media instead of .phdf")

# ---------- PRE-RENDERED MEDIA ----------
selected_media = None
if use_image:
    st.sidebar.header("1. Select Pre-rendered Media")
    media_files = sorted(IMAGE_PATH.glob("*"))  # .png, .gif, .mp4

    if not media_files:
        st.warning("⚠️ Nessun file multimediale trovato nella cartella pre_rendered_plots.")
    else:
        selected_media = st.sidebar.selectbox("Select File", media_files, format_func=lambda x: x.name)

        # Display selected media
        if selected_media.suffix in [".png", ".gif"]:
            st.image(str(selected_media), caption=f"Media: {selected_media.name}")
        elif selected_media.suffix == ".mp4":
            with open(selected_media, "rb") as f:
                st.video(f.read())
        else:
            st.warning("Unsupported file format.")

# ---------- SIMULATION MODE ----------
else:
    st.sidebar.header("1. Select Simulation Scenario")
    scenario_dirs = [f for f in DATA_PATH.iterdir() if f.is_dir()]
    scenario = st.sidebar.selectbox("Scenario", scenario_dirs, format_func=lambda x: x.name) if scenario_dirs else None

    if scenario is None:
        st.warning("⚠️ Nessuno scenario disponibile nella cartella simulation_data.")
    else:
        phdf_files = sorted(scenario.glob("*.phdf"))
        if not phdf_files:
            st.warning("⚠️ Nessun file .phdf trovato nello scenario selezionato.")
        else:
            snapshot = st.sidebar.selectbox("Snapshot File", phdf_files, format_func=lambda x: x.name)
            field = st.sidebar.selectbox("Field to Plot", ["density", "temperature", "velocity_magnitude"])
            axis = st.sidebar.radio("Slice Axis", ["x", "y", "z"])

            if st.sidebar.button("Generate Plot"):
                with st.spinner("Generating plot with yt..."):
                    plot_file = plot_slice(str(snapshot), field=field, axis=axis)
                    st.image(plot_file, caption=f"{field} Slice on {axis}-axis")

# ---------- AI TUTOR ----------
st.subheader("🤖 Ask the AI-Tutor about this simulation")
student_input = st.text_area("Ask a question or describe your interpretation:")

if st.button("Get AI Guidance"):
    if use_image and selected_media:
        context = f"Media: {selected_media.name}"
    elif not use_image and 'scenario' in locals() and 'snapshot' in locals():
        context = f"Scenario: {scenario.name}, Snapshot: {snapshot.name}, Field: {field}, Axis: {axis}"
    else:
        context = "No valid context available."
    
    full_prompt = f"{context}\nStudent says: {student_input}"
    response = ask_ai(full_prompt)
    st.markdown("**AI-Tutor Response:**")
    st.markdown(response)

# ---------- REFLECTION ----------
st.subheader("📝 Reflection")
reflection = st.text_area("What did you learn from this simulation?")
if st.button("Save Reflection"):
    with open("student_reflections.txt", "a") as f:
        if use_image and selected_media:
            f.write(f"Media: {selected_media.name}\n")
        elif not use_image and 'scenario' in locals() and 'snapshot' in locals():
            f.write(f"Scenario: {scenario.name}, Snapshot: {snapshot.name}, Field: {field}, Axis: {axis}\n")
        else:
            f.write("No valid simulation context\n")
        f.write(f"Reflection: {reflection}\n\n")
    st.success("Reflection saved!")
