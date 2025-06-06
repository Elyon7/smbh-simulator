import streamlit as st
import yt
import openai
from pathlib import Path
import os

# ---- CONFIGURATION ----
# Replace with your own OpenAI key or load from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# Path to simulation folders with .phdf outputs (organized by scenario)
DATA_PATH = Path("./simulation_data")
PLOT_OUTPUT = "output_plot.png"

# ---- FUNCTION: Generate slice plot using yt ----
def plot_slice(filename, field="density", axis="z"):
    ds = yt.load(filename)
    slc = yt.SlicePlot(ds, axis, field)
    slc.set_cmap(field, 'inferno')
    slc.save(".")  # Save to current directory
    return PLOT_OUTPUT

# ---- FUNCTION: AI Tutor Dialogue ----
def ask_ai(prompt):
    messages = [
        {"role": "system", "content": "You are an astrophysics tutor guiding students through black hole simulations. Ask questions and give suggestions to help them think like a scientist."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ---- STREAMLIT INTERFACE ----
st.set_page_config(page_title="SMBH Simulation Explorer", layout="wide")
st.title("🕳️ SMBH Simulation Explorer with AI Tutor")

# Step 1: Choose Scenario
st.sidebar.header("1. Select Simulation Scenario")
scenario_dirs = [f for f in DATA_PATH.iterdir() if f.is_dir()]
scenario = st.sidebar.selectbox("Scenario", scenario_dirs, format_func=lambda x: x.name)

# Step 2: Choose Snapshot
phdf_files = sorted(scenario.glob("*.phdf"))
snapshot = st.sidebar.selectbox("Snapshot File", phdf_files, format_func=lambda x: x.name)

# Step 3: Choose Field
field = st.sidebar.selectbox("Field to Plot", ["density", "temperature", "velocity_magnitude"])

# Step 4: Choose Axis
axis = st.sidebar.radio("Slice Axis", ["x", "y", "z"])

# Step 5: Plot
if st.sidebar.button("Generate Plot"):
    with st.spinner("Generating plot with yt..."):
        plot_file = plot_slice(str(snapshot), field=field, axis=axis)
        st.image(plot_file, caption=f"{field} Slice on {axis}-axis")

# Step 6: AI Tutor Interaction
st.subheader("🤖 Ask the AI-Tutor about this simulation")
student_input = st.text_area("Ask a question or describe your interpretation:")

if st.button("Get AI Guidance"):
    context = f"Scenario: {scenario.name}, Snapshot: {snapshot.name}, Field: {field}, Axis: {axis}."
    full_prompt = f"{context}\nStudent says: {student_input}"
    response = ask_ai(full_prompt)
    st.markdown("**AI-Tutor Response:**")
    st.markdown(response)

# Step 7: Reflection Journal
st.subheader("📝 Reflection")
reflection = st.text_area("What did you learn from this simulation?")
if st.button("Save Reflection"):
    with open("student_reflections.txt", "a") as f:
        f.write(f"Scenario: {scenario.name}, Snapshot: {snapshot.name}, Field: {field}, Axis: {axis}\n")
        f.write(f"Reflection: {reflection}\n\n")
    st.success("Reflection saved!")
