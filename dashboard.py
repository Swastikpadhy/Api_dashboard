import streamlit as st
import pandas as pd
import os
import re
from log_parser import parse_logs_from_folder

st.title('Tomcat API Log Dashboard')

st.sidebar.header('Log Folder Selection')
log_files = st.sidebar.file_uploader('Upload log files', type='log', accept_multiple_files=True)

folder = None
if log_files:
    import tempfile
    temp_dir = tempfile.mkdtemp()
    for uploaded_file in log_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
    folder = temp_dir
else:
    st.info('Please upload one or more .log files using the sidebar.')

def extract_timestamp(line):
    # Extracts the timestamp from the log line
    match = re.search(r'\[(.*?)\]', line)
    if match:
        # Example: 10/Oct/2023:13:55:36 +0000
        from datetime import datetime
        try:
            return datetime.strptime(match.group(1).split()[0], '%d/%b/%Y:%H:%M:%S')
        except Exception:
            return None
    return None

if folder and st.button('Load Logs'):
    df = parse_logs_from_folder(folder)
    # Add timestamp column
    timestamps = []
    for file_path in [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.log')]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                ts = extract_timestamp(line)
                if ts:
                    timestamps.append(ts)
    if len(timestamps) < len(df):
        # If for some reason not all lines parsed, pad with None
        timestamps += [None] * (len(df) - len(timestamps))
    df['timestamp'] = timestamps[:len(df)]

    if df.empty:
        st.warning('No log data found!')
    else:
        # --- OVERALL METRICS ---
        min_time = df['timestamp'].min()
        max_time = df['timestamp'].max()
        total_calls = len(df)
        total_seconds = (max_time - min_time).total_seconds() if min_time and max_time and min_time != max_time else 1
        calls_per_sec = total_calls / total_seconds if total_seconds > 0 else total_calls
        avg_response_per_sec = df['response_time'].sum() / total_seconds if total_seconds > 0 else df['response_time'].mean()
        col1, col2 = st.columns(2)
        col1.metric('Overall API Calls/sec', f"{calls_per_sec:.4f}")
        col2.metric('Average Response Time/sec (ms)', f"{avg_response_per_sec:.2f}")
        # --- END METRICS ---

        avg_time = df.groupby('api')['response_time'].mean().sort_values(ascending=False)
        max_time = df.groupby('api')['response_time'].max().sort_values(ascending=False)
        max_size = df.groupby('api')['response_size'].max().sort_values(ascending=False)

        st.subheader('Average API Response Time (ms)')
        st.bar_chart(avg_time)

        st.subheader('Top 10 APIs by Average Response Time')
        st.dataframe(avg_time.head(10).reset_index().rename(columns={'response_time': 'avg_response_time_ms'}))

        st.subheader('Top 10 APIs by Max Response Time')
        st.dataframe(max_time.head(10).reset_index().rename(columns={'response_time': 'max_response_time_ms'}))

        st.subheader('Top 10 APIs by Max Response Size')
        st.dataframe(max_size.head(10).reset_index().rename(columns={'response_size': 'max_response_size_bytes'}))

        st.subheader('Top 10 APIs by Most Calls')
        api_counts = df['api'].value_counts().head(10)
        st.bar_chart(api_counts)
        st.dataframe(api_counts.reset_index().rename(columns={'index': 'api', 'api': 'call_count'})) 