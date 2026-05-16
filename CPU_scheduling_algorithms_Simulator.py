import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from copy import deepcopy

# =========================
# Page Config
# =========================
st.set_page_config(page_title="CPU Scheduling Simulator", layout="wide")

# =========================
# Styling
# =========================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
h1 { font-size: 62px !important; text-align: center; color: #4281a4 !important; font-family: 'Inter', 'Poppins', sans-serif !important;}
h2 { font-size: 35px !important; }
h3 { font-size: 24px !important; }
label { font-size: 18px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

st.title("CPU Scheduling Simulator")

# =========================
# Session State
# =========================
if "processes" not in st.session_state:
    st.session_state.processes = []

if "pid_counter" not in st.session_state:
    st.session_state.pid_counter = 1

# =========================
# Process Class
# =========================
class Process:
    def __init__(self, pid, at, bt, priority=1):
        self.pid = pid
        self.at = at
        self.bt = bt
        self.priority = priority
        self.remaining = bt
        self.st = None
        self.ct = 0
        self.tat = 0
        self.wt = 0
        self.rt = None

# =========================
# Utility
# =========================
def calculate_metrics(processes, gantt):
    n = len(processes)
    total_idle = sum(end - start for pid, start, end in gantt if pid == "Idle")
    total_time = gantt[-1][2] if gantt else 0

    for p in processes:
        p.tat = p.ct - p.at
        p.wt = p.tat - p.bt
        p.rt = p.st - p.at

    avg_wt = sum(p.wt for p in processes) / n
    avg_tat = sum(p.tat for p in processes) / n
    avg_rt = sum(p.rt for p in processes) / n
    cpu_util = ((total_time - total_idle) / total_time) * 100 if total_time > 0 else 0
    throughput = n / total_time if total_time > 0 else 0

    return avg_wt, avg_tat, avg_rt, cpu_util, throughput

# =========================
# Gantt Chart
# =========================
def generate_gantt_chart(gantt):
    fig = go.Figure()
    palette = ["#588157", "#e07a5f", "#3d405b", "#335c67",
               "#f2cc8f", "#6a994e", "#bc4749", "#4361ee"]
    color_map = {}
    color_index = 0

    for pid, start, end in gantt:
        if pid not in color_map:
            if pid == "Idle":
                color_map[pid] = "#cccccc"
            else:
                color_map[pid] = palette[color_index % len(palette)]
                color_index += 1

        fig.add_trace(go.Bar(
            x=[end - start],
            y=["CPU"],
            base=start,
            orientation='h',
            marker_color=color_map[pid],
            text=pid,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=14),
            showlegend=False
        ))

    fig.update_layout(
        barmode='stack',
        title="Gantt Chart",
        xaxis_title="Time",
        yaxis=dict(showticklabels=False),
        height=300
    )
    return fig

# =========================
# Algorithms
# =========================
def fcfs(processes):
    processes.sort(key=lambda x: x.at)
    time = 0
    gantt = []

    for p in processes:
        if time < p.at:
            gantt.append(("Idle", time, p.at))
            time = p.at
        p.st = time
        time += p.bt
        p.ct = time
        gantt.append((p.pid, p.st, p.ct))

    return processes, gantt


def sjf(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.ct == 0]
        if not ready:
            next_arrival = min(p.at for p in processes if p.ct == 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        p = min(ready, key=lambda x: x.bt)
        p.st = time
        time += p.bt
        p.ct = time
        gantt.append((p.pid, p.st, p.ct))
        completed += 1

    return processes, gantt


def ljf(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.ct == 0]
        if not ready:
            next_arrival = min(p.at for p in processes if p.ct == 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        p = max(ready, key=lambda x: x.bt)
        p.st = time
        time += p.bt
        p.ct = time
        gantt.append((p.pid, p.st, p.ct))
        completed += 1

    return processes, gantt


def srjf(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.remaining > 0]
        if not ready:
            next_arrival = min(p.at for p in processes if p.remaining > 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        p = min(ready, key=lambda x: x.remaining)

        if p.st is None:
            p.st = time

        start = time
        time += 1
        p.remaining -= 1

        if p.remaining == 0:
            p.ct = time
            completed += 1

        gantt.append((p.pid, start, time))

    return processes, gantt


def lrjf(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.remaining > 0]
        if not ready:
            next_arrival = min(p.at for p in processes if p.remaining > 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        p = max(ready, key=lambda x: x.remaining)

        if p.st is None:
            p.st = time

        start = time
        time += 1
        p.remaining -= 1

        if p.remaining == 0:
            p.ct = time
            completed += 1

        gantt.append((p.pid, start, time))

    return processes, gantt


def hrrn(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.ct == 0]

        if not ready:
            next_arrival = min(p.at for p in processes if p.ct == 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        for p in ready:
            waiting = time - p.at
            p.rr = (waiting + p.bt) / p.bt

        p = max(ready, key=lambda x: x.rr)
        p.st = time
        time += p.bt
        p.ct = time
        gantt.append((p.pid, p.st, p.ct))
        completed += 1

    return processes, gantt


def priority_preemptive(processes):
    time, completed = 0, 0
    n = len(processes)
    gantt = []

    while completed < n:
        ready = [p for p in processes if p.at <= time and p.remaining > 0]

        if not ready:
            next_arrival = min(p.at for p in processes if p.remaining > 0)
            gantt.append(("Idle", time, next_arrival))
            time = next_arrival
            continue

        p = min(ready, key=lambda x: x.priority)

        if p.st is None:
            p.st = time

        start = time
        time += 1
        p.remaining -= 1

        if p.remaining == 0:
            p.ct = time
            completed += 1

        gantt.append((p.pid, start, time))

    return processes, gantt


def round_robin(processes, quantum):
    time = 0
    queue = []
    gantt = []
    processes.sort(key=lambda x: x.at)
    n = len(processes)
    completed = 0
    i = 0

    while completed < n:
        while i < n and processes[i].at <= time:
            queue.append(processes[i])
            i += 1

        if not queue:
            if i < n:
                gantt.append(("Idle", time, processes[i].at))
                time = processes[i].at
            continue

        p = queue.pop(0)

        if p.st is None:
            p.st = time

        exec_time = min(quantum, p.remaining)
        start = time
        time += exec_time
        p.remaining -= exec_time
        gantt.append((p.pid, start, time))

        while i < n and processes[i].at <= time:
            queue.append(processes[i])
            i += 1

        if p.remaining > 0:
            queue.append(p)
        else:
            p.ct = time
            completed += 1

    return processes, gantt


# =========================
# UI
# =========================
if "processes" not in st.session_state:
    st.session_state.processes = []
# =========================
# Add Process Section
# =========================
st.header("Add Process")
c1, c2, c3, c4 = st.columns(4)

with c1:
    pid = st.text_input("Process ID", value=f"P{st.session_state.pid_counter}")
with c2:
    at = st.number_input("Arrival Time", min_value=0)
with c3:
    bt = st.number_input("Burst Time", min_value=1)
with c4:
    priority = st.number_input("Priority", min_value=1, value=1)

if st.button("Add Process"):
    st.session_state.processes.append((pid, at, bt, priority))
    st.session_state.pid_counter += 1
    st.rerun()

if st.button("Reset"):
    st.session_state.processes = []
    st.session_state.pid_counter = 1
    st.rerun()

st.dataframe(pd.DataFrame(
    st.session_state.processes,
    columns=["PID", "Arrival Time", "Burst Time", "Priority"]
), use_container_width=True)

# =========================
# Algorithm Selection
# =========================
st.header("Select Algorithm")

algo = st.selectbox(
    "Algorithm",
    ["FCFS", "SJF", "LJF", "SRJF", "LRJF",
     "HRRN", "Priority (Preemptive)", "Round Robin"]
)

quantum = None
if algo == "Round Robin":
    quantum = st.slider("Time Quantum", min_value=1, max_value=10, value=2, step=1)

run_simulation = st.button("Run Simulation", use_container_width=True)

# =========================
# Simulation
# =========================
if run_simulation and st.session_state.processes:

    base_processes = [
        Process(pid, at, bt, priority)
        for pid, at, bt, priority in st.session_state.processes
    ]

    # ---- Run Selected Algo ----
    processes = deepcopy(base_processes)

    if algo == "FCFS":
        processes, gantt = fcfs(processes)
    elif algo == "SJF":
        processes, gantt = sjf(processes)
    elif algo == "LJF":
        processes, gantt = ljf(processes)
    elif algo == "SRJF":
        processes, gantt = srjf(processes)
    elif algo == "LRJF":
        processes, gantt = lrjf(processes)
    elif algo == "HRRN":
        processes, gantt = hrrn(processes)
    elif algo == "Priority (Preemptive)":
        processes, gantt = priority_preemptive(processes)
    else:
        processes, gantt = round_robin(processes, quantum)

    avg_wt, avg_tat, avg_rt, cpu_util, throughput = calculate_metrics(processes, gantt)

    # =========================
    # Results
    # =========================
    st.divider()
    st.header("Results Table")

    df = pd.DataFrame([{
        "PID": p.pid,
        "AT": p.at,
        "BT": p.bt,
        "Priority": p.priority,
        "ST": p.st,
        "CT": p.ct,
        "TAT": p.tat,
        "WT": p.wt,
        "RT": p.rt
    } for p in processes])

    st.dataframe(df, use_container_width=True)

    st.divider()
    st.header("Gantt Chart")
    st.plotly_chart(generate_gantt_chart(gantt), use_container_width=True)

    st.divider()
    st.header("Performance Metrics")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Avg WT", f"{avg_wt:.3f}")
    c2.metric("Avg TAT", f"{avg_tat:.3f}")
    c3.metric("Avg RT", f"{avg_rt:.3f}")
    c4.metric("CPU Util (%)", f"{cpu_util:.2f}")
    c5.metric("Throughput", f"{throughput:.4f}")

    # =========================
    # FULL Comparison Section
    # =========================
    st.divider()
    st.header("Algorithm Comparison")

    algorithm_colors = {
        "FCFS": "#588157",
        "SJF": "#f4f1de",
        "LJF": "#e07a5f",
        "SRJF": "#3d405b",
        "LRJF": "#335c67",
        "HRRN": "#6a994e",
        "Priority (Preemptive)": "#bc4749",
        "Round Robin": "#f2cc8f"
    }

    results = {}

    for name in algorithm_colors.keys():
        procs = deepcopy(base_processes)

        if name == "FCFS":
            procs, g = fcfs(procs)
        elif name == "SJF":
            procs, g = sjf(procs)
        elif name == "LJF":
            procs, g = ljf(procs)
        elif name == "SRJF":
            procs, g = srjf(procs)
        elif name == "LRJF":
            procs, g = lrjf(procs)
        elif name == "HRRN":
            procs, g = hrrn(procs)
        elif name == "Priority (Preemptive)":
            procs, g = priority_preemptive(procs)
        else:
            # For Round Robin, use the current quantum if set, otherwise default to 2
            q = quantum if quantum is not None else 2
            procs, g = round_robin(procs, q)

        results[name] = calculate_metrics(procs, g)

    # ---- Comparison Table ----
    comparison_df = pd.DataFrame([
        {
            "Algorithm": name,
            "Avg WT": round(metrics[0], 2),
            "Avg TAT": round(metrics[1], 2),
            "Avg RT": round(metrics[2], 2),
            "CPU Util (%)": round(metrics[3], 2),
            "Throughput": round(metrics[4], 3)
        }
        for name, metrics in results.items()
    ])

    st.subheader("Comparison Summary Table")
    st.dataframe(comparison_df, use_container_width=True)

    # ---- Tabs with Charts ----
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Avg WT", "Avg TAT", "Avg RT", "CPU Util (%)", "Throughput"]
    )

    def create_chart(metric_name, index):
        algorithms = list(results.keys())
        values = [round(results[a][index], 3) for a in algorithms]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=algorithms,
            y=values,
            text=values,
            textposition='outside',
            marker_color=[algorithm_colors[a] for a in algorithms]
        ))

        fig.update_layout(
            title=f"{metric_name} Comparison",
            template="plotly_dark",
            height=600
        )

        return fig

    with tab1:
        st.plotly_chart(create_chart("Avg WT", 0), use_container_width=True)

    with tab2:
        st.plotly_chart(create_chart("Avg TAT", 1), use_container_width=True)

    with tab3:
        st.plotly_chart(create_chart("Avg RT", 2), use_container_width=True)

    with tab4:
        st.plotly_chart(create_chart("CPU Util (%)", 3), use_container_width=True)

    with tab5:
        st.plotly_chart(create_chart("Throughput", 4), use_container_width=True)

    # =========================
    # NEW SECTION: Round Robin with multiple quantums (only if current algo is not RR)
    # =========================
    if algo != "Round Robin":
        st.divider()
        st.header("Round Robin Performance with Different Time Quantums")

        quantums = list(range(1, 11))  # 1 to 10
        rr_results = {}

        for q in quantums:
            procs = deepcopy(base_processes)
            _, g = round_robin(procs, q)
            rr_results[q] = calculate_metrics(procs, g)

        rr_df = pd.DataFrame([
            {
                "Quantum": q,
                "Avg WT": round(metrics[0], 2),
                "Avg TAT": round(metrics[1], 2),
                "Avg RT": round(metrics[2], 2),
                "CPU Util (%)": round(metrics[3], 2),
                "Throughput": round(metrics[4], 3)
            }
            for q, metrics in rr_results.items()
        ])

        st.subheader("Metrics for Time Quantum 1–10")
        st.dataframe(rr_df, use_container_width=True)

        # Line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rr_df["Quantum"], y=rr_df["Avg WT"], mode='lines+markers', name='Avg WT'))
        fig.add_trace(go.Scatter(x=rr_df["Quantum"], y=rr_df["Avg TAT"], mode='lines+markers', name='Avg TAT'))
        fig.add_trace(go.Scatter(x=rr_df["Quantum"], y=rr_df["Avg RT"], mode='lines+markers', name='Avg RT'))
        fig.add_trace(go.Scatter(x=rr_df["Quantum"], y=rr_df["CPU Util (%)"], mode='lines+markers', name='CPU Util (%)'))
        fig.add_trace(go.Scatter(x=rr_df["Quantum"], y=rr_df["Throughput"], mode='lines+markers', name='Throughput'))
        fig.update_layout(
            title="Round Robin Metrics vs Time Quantum",
            xaxis_title="Time Quantum",
            yaxis_title="Value",
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)