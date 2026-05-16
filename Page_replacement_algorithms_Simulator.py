import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Page Replacement Simulator", layout="wide")

# -------------------------------
# Custom CSS
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
            
    .conclusion-box {
    # background-color: rgb(238, 238, 238,0.1);
    background-color: rgb(30, 136, 229, 0.09);
    padding: 15px;
    border-radius: 10px;
    border-left: 6px solid #1E88E5;
    margin-top: 10px;
    }
            
    div.stButton > button[kind="primary"] {
    background-color: rgb(30, 136, 229, 0.15);
    color: white;
    border-radius: 8px;
    border: none;
    height: 3em;
    font-weight: bold;
    }

    /* Hover effect */
    div.stButton > button[kind="primary"]:hover {
        background-color: rgb(30, 136, 229, 0.25);
        color: white;
    }
    
    .bold-heading {
        font-size: 1.8rem;
        font-weight: bold;
        color: white;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
     h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 3rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
            
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>Page Replacement Algorithm Simulator</h1>", unsafe_allow_html=True)

# -------------------------------
# Session State Initialization
# -------------------------------
if "steps_full" not in st.session_state:
    st.session_state.steps_full = []

# ✅ NEW (only required addition)
if "ref_input" not in st.session_state:
    st.session_state.ref_input = "7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1"

# -------------------------------
# Helper Functions
# -------------------------------
def generate_random_string(length=10, max_page=9):
    return [random.randint(0, max_page) for _ in range(length)]

def simulate_fifo(ref_str, num_frames):
    frames = []
    steps = []
    page_faults = 0
    page_hits = 0
    queue = []

    for idx, page in enumerate(ref_str):
        step_num = idx + 1
        if page in frames:
            page_hits += 1
            hit_miss = "Hit"
            replaced = None
            frames_copy = frames.copy()
        else:
            page_faults += 1
            hit_miss = "Miss"
            if len(frames) < num_frames:
                frames.append(page)
                queue.append(page)
                replaced = None
            else:
                oldest = queue.pop(0)
                replace_index = frames.index(oldest)
                replaced = frames[replace_index]
                frames[replace_index] = page
                queue.append(page)
            frames_copy = frames.copy()
        steps.append({
            "Step": step_num,
            "Page": page,
            "Frames": frames_copy,
            "Hit/Miss": hit_miss,
            "Replaced": replaced
        })
    return steps, page_faults, page_hits

def simulate_lru(ref_str, num_frames):
    frames = []
    steps = []
    page_faults = 0
    page_hits = 0
    last_used = {}

    for idx, page in enumerate(ref_str):
        step_num = idx + 1
        if page in frames:
            page_hits += 1
            hit_miss = "Hit"
            replaced = None
            last_used[page] = idx
            frames_copy = frames.copy()
        else:
            page_faults += 1
            hit_miss = "Miss"
            if len(frames) < num_frames:
                frames.append(page)
                replaced = None
            else:
                lru_page = min(frames, key=lambda p: last_used.get(p, -1))
                replace_index = frames.index(lru_page)
                replaced = frames[replace_index]
                frames[replace_index] = page
            last_used[page] = idx
            frames_copy = frames.copy()
        steps.append({
            "Step": step_num,
            "Page": page,
            "Frames": frames_copy,
            "Hit/Miss": hit_miss,
            "Replaced": replaced
        })
    return steps, page_faults, page_hits

def simulate_optimal(ref_str, num_frames):
    frames = []
    steps = []
    page_faults = 0
    page_hits = 0

    for idx, page in enumerate(ref_str):
        step_num = idx + 1
        if page in frames:
            page_hits += 1
            hit_miss = "Hit"
            replaced = None
            frames_copy = frames.copy()
        else:
            page_faults += 1
            hit_miss = "Miss"
            if len(frames) < num_frames:
                frames.append(page)
                replaced = None
            else:
                future_use = {}
                for p in frames:
                    try:
                        next_use = ref_str.index(p, idx+1)
                    except ValueError:
                        next_use = float('inf')
                    future_use[p] = next_use
                to_replace = max(future_use, key=future_use.get)
                replace_index = frames.index(to_replace)
                replaced = frames[replace_index]
                frames[replace_index] = page
            frames_copy = frames.copy()
        steps.append({
            "Step": step_num,
            "Page": page,
            "Frames": frames_copy,
            "Hit/Miss": hit_miss,
            "Replaced": replaced
        })
    return steps, page_faults, page_hits

def display_step_table(steps):
    data = []
    for s in steps:
        frames_str = " | ".join([str(f) for f in s["Frames"]])
        data.append({
            "Step": s["Step"],
            "Page": s["Page"],
            "Frames": frames_str,
            "Hit/Miss": s["Hit/Miss"],
            "Replaced": s["Replaced"] if s["Replaced"] else "-"
        })
    df = pd.DataFrame(data)
    def color_hit_miss(val):
        if val == "Hit":
            return "background-color: #3a5a40"
        elif val == "Miss":
            return "background-color: #bf4342"
        return ""
    styled_df = df.style.applymap(color_hit_miss, subset=["Hit/Miss"])
    st.dataframe(styled_df, use_container_width=True)

def plot_comparison(results_df):
    fig = px.bar(results_df, x="Algorithm", y="Page Faults", 
                 color="Algorithm", title="Page Faults Comparison",
                 text="Page Faults")
    fig.update_traces(textposition='outside')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

def plot_hit_ratio_comparison(results_df):
    fig = px.bar(results_df, x="Algorithm", y="Hit Ratio", 
                 color="Algorithm", title="Hit Ratio Comparison",
                 text=results_df["Hit Ratio"].apply(lambda x: f"{x:.2%}"))
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis_tickformat=".0%")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

def belady_analysis(ref_str, max_frames=7):
    frame_counts = list(range(1, max_frames+1))
    fifo_faults = []
    lru_faults = []
    opt_faults = []
    for fc in frame_counts:
        _, fifo_f, _ = simulate_fifo(ref_str, fc)
        _, lru_f, _ = simulate_lru(ref_str, fc)
        _, opt_f, _ = simulate_optimal(ref_str, fc)
        fifo_faults.append(fifo_f)
        lru_faults.append(lru_f)
        opt_faults.append(opt_f)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frame_counts, y=fifo_faults, mode='lines+markers', name='FIFO'))
    fig.add_trace(go.Scatter(x=frame_counts, y=lru_faults, mode='lines+markers', name='LRU'))
    fig.add_trace(go.Scatter(x=frame_counts, y=opt_faults, mode='lines+markers', name='Optimal'))
    fig.update_layout(title="Effect of Frame Count on Page Faults (Belady's Anomaly Check)",
                      xaxis_title="Number of Frames", yaxis_title="Page Faults")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
<div class="conclusion-box">
<b>Conclusion:</b><br>
Belady's anomaly is a phenomenon where increasing the number of frames can lead to an increase in page faults.\n
This anomaly is most commonly observed with the <b>FIFO</b> algorithm.  
<b>LRU</b> and <b>Optimal</b> algorithms are generally anomaly-free.
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Main Layout
# -------------------------------
st.markdown('<div class="bold-heading">Simulation Parameters</div>', unsafe_allow_html=True)

row1_col1, row1_col2 = st.columns([6,4])

with row1_col1:
    ref_input = st.text_input(
        "Reference String (space-separated)", 
        value=st.session_state.ref_input
    )
    st.session_state.ref_input = ref_input

with row1_col2:
    st.write("")
    st.write("")
    
    if st.button("Generate Random String", use_container_width=True):
        rand_len = 20
        rand_max = 9
        random_str = generate_random_string(rand_len, rand_max)
        st.session_state.ref_input = " ".join(map(str, random_str))

row2_col1, row2_col2 = st.columns([6,4])

with row2_col1:
    num_frames = st.slider("Number of Frames", 1, 10, 3)

with row2_col2:
    algorithm = st.selectbox("Algorithm", ["FIFO", "LRU", "Optimal"])

try:
    ref_str = [int(x) for x in ref_input.strip().split()]
except:
    st.error("Invalid input. Please enter integers only.")
    ref_str = []

if st.button("Run Simulation", type="primary", use_container_width=True,) and ref_str:

    if algorithm == "FIFO":
        steps, faults, hits = simulate_fifo(ref_str, num_frames)
    elif algorithm == "LRU":
        steps, faults, hits = simulate_lru(ref_str, num_frames)
    else:
        steps, faults, hits = simulate_optimal(ref_str, num_frames)

    total = len(ref_str)
    hit_ratio = hits / total if total else 0
    miss_ratio = faults / total if total else 0

    st.session_state.steps_full = steps

    st.divider()

    st.markdown('<div class="bold-heading">Step-by-Step Simulation</div>', unsafe_allow_html=True)
    display_step_table(steps)

    st.divider()

    st.markdown('<div class="bold-heading">Performance Metrics</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Page Faults", faults)
    with m2:
        st.metric("Total Hits", hits)
    with m3:
        st.metric("Hit Ratio", f"{hit_ratio:.2%}")
    with m4:
        st.metric("Miss Ratio", f"{miss_ratio:.2%}")

    st.divider()

    st.markdown('<div class="bold-heading">Frame Occupancy Over Time</div>', unsafe_allow_html=True)
    frame_data = []
    for step in steps:
        frames = step["Frames"]
        padded = frames + [None] * (num_frames - len(frames))
        frame_data.append(padded)

    df_frames = pd.DataFrame(frame_data, columns=[f"Frame {i+1}" for i in range(num_frames)])
    df_frames.index = df_frames.index + 1
    st.dataframe(df_frames, use_container_width=True)

    st.divider()

    st.markdown('<div class="bold-heading">Algorithm Comparison</div>', unsafe_allow_html=True)
    results = []
    for algo in ["FIFO", "LRU", "Optimal"]:
        if algo == "FIFO":
            _, f, h = simulate_fifo(ref_str, num_frames)
        elif algo == "LRU":
            _, f, h = simulate_lru(ref_str, num_frames)
        else:
            _, f, h = simulate_optimal(ref_str, num_frames)
        hr = h / len(ref_str)
        results.append({
            "Algorithm": algo,
            "Page Faults": f,
            "Hits": h,
            "Hit Ratio": hr
        })

    
    comp_df = pd.DataFrame(results)
    st.dataframe(comp_df, use_container_width=True)
    st.divider()   
    col_left, col_right = st.columns(2)
    with col_left:
        plot_comparison(comp_df)
    with col_right:
        plot_hit_ratio_comparison(comp_df)

    st.divider()

    st.markdown('<div class="bold-heading">Frame Size Variation Analysis (Belady\'s Anomaly)</div>', unsafe_allow_html=True)
    belady_analysis(ref_str, max_frames=7)

    st.divider()

    st.markdown('<div class="bold-heading">Export Results</div>', unsafe_allow_html=True)
    if st.button("Export Steps as CSV"):
        df_export = pd.DataFrame([{
            "Step": s["Step"],
            "Page": s["Page"],
            "Frames": " | ".join(map(str, s["Frames"])),
            "Hit/Miss": s["Hit/Miss"],
            "Replaced": s["Replaced"] if s["Replaced"] else ""
        } for s in steps])
        csv = df_export.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="simulation_steps.csv", mime="text/csv")

elif not ref_str:
    st.info("Please enter a valid reference string and click Run Simulation.")