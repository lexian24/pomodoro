import streamlit as st
import time
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# CSV file for logging sessions
LOG_FILE = 'study_sessions.csv'

# Streamlit app configuration
st.set_page_config(page_title="Capybara Pomodoro Timer", page_icon="🐾", layout="centered")

# Custom CSS for Capybara theme
st.markdown(
    """
    <style>
    /* General Page Styling */
    body {
        background-color: #f7f3e9;  /* Soft beige background */
        color: #4e342e;  /* Brownish text color */
    }

    /* Title Styling */
    .stTitle {
        color: #795548;  /* Capybara brown color for title */
        font-family: 'Comic Sans MS', cursive, sans-serif;
        text-align: center;
    }

    /* Subheader Styling (Timer) */
    .stSubheader {
        color: #3e2723;  /* Dark brown */
    }

    /* Button Styling */
    div.stButton > button {
        background-color: #a1887f;  /* Light brown button background */
        color: #fff;  /* White button text */
        border-radius: 10px;
        padding: 10px;
        border: none;
        font-size: 16px;
    }

    div.stButton > button:hover {
        background-color: #8d6e63;  /* Darker brown on hover */
        color: #ffffff;
    }

    /* Input box text color */
    .stNumberInput > div > input {
        color: #4e342e;  /* Brown text in number inputs */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to log the study session into the CSV file
def log_session(module, actual_time, sessions, session_type):
    session_data = {
        "Module": module,
        "Session Type": session_type,  # Work or Rest
        "Actual Time Spent (minutes)": actual_time,
        "Number of Sessions": sessions,
        "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Create or append to the CSV file
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame([session_data])
        df.to_csv(LOG_FILE, index=False)
    else:
        df = pd.read_csv(LOG_FILE)
        df = pd.concat([df, pd.DataFrame([session_data])], ignore_index=True)
        df.to_csv(LOG_FILE, index=False)

# Function to clear the study_sessions.csv file
def clear_history():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)  # Delete the file
        st.success("Study history cleared!")
    else:
        st.warning("No history found to clear!")

# Function to retrieve unique modules from the CSV file
def get_module_list():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        return sorted(df['Module'].unique().tolist())
    return []

# Function to load CSV and ensure 'Session Type' column exists
def load_csv_with_session_type():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)

        # If 'Session Type' column doesn't exist, add it with a default value
        if 'Session Type' not in df.columns:
            df['Session Type'] = 'Work'  # Assuming old sessions were work sessions
        return df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if CSV doesn't exist

# Function to reset all session states
def reset_session():
    st.session_state['running'] = False
    st.session_state['paused'] = False
    st.session_state['stop'] = False
    st.session_state['timer'] = 0
    st.session_state['is_work_session'] = True  # Reset to work session
    st.session_state['completed_sessions'] = 0  # Reset completed work sessions
    st.session_state['start_time'] = None

# Initialize session state variables
if 'timer' not in st.session_state:
    st.session_state['timer'] = 0
if 'running' not in st.session_state:
    st.session_state['running'] = False
if 'paused' not in st.session_state:
    st.session_state['paused'] = False
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = None  # To track when the session starts
if 'module' not in st.session_state:
    st.session_state['module'] = ""
if 'work_time' not in st.session_state:
    st.session_state['work_time'] = 25  # Default work time of 25 minutes
if 'rest_time' not in st.session_state:
    st.session_state['rest_time'] = 5  # Default rest time of 5 minutes
if 'sessions' not in st.session_state:
    st.session_state['sessions'] = 1
if 'completed_sessions' not in st.session_state:
    st.session_state['completed_sessions'] = 0  # Track how many work sessions have been completed
if 'stop' not in st.session_state:
    st.session_state['stop'] = False
if 'is_work_session' not in st.session_state:
    st.session_state['is_work_session'] = True  # To track whether it's a work or rest session

# Retrieve modules from the CSV
modules = get_module_list()
modules.append("Add new module")

# UI Layout
# Title with Capybara Image
col1, col2 = st.columns([1, 4])  # Create two columns for layout
with col1:
    st.image("capybara.png", width=100)  # Display the Capybara image

with col2:
    st.title("Capybara Pomodoro Timer")  # Display title next to the image

# Module Selection
selected_module = st.selectbox("Select Module", modules)

# New Module Input if "Add new module" selected
if selected_module == "Add new module":
    st.session_state['module'] = st.text_input("New Module Name")
else:
    st.session_state['module'] = selected_module

# Work Time and Rest Time Inputs
st.session_state['work_time'] = st.number_input("Work Time (minutes)", min_value=1, max_value=90, value=st.session_state['work_time'])
st.session_state['rest_time'] = st.number_input("Rest Time (minutes)", min_value=1, max_value=30, value=st.session_state['rest_time'])
st.session_state['sessions'] = st.number_input("Number of Sessions", min_value=1, max_value=10, value=st.session_state['sessions'])

# Timer Display (Work or Rest)
if st.session_state['is_work_session']:
    session_type = "Work"
    st.subheader(f"Work Timer: {st.session_state['work_time']:02d} minutes")
else:
    session_type = "Rest"
    st.subheader(f"Rest Timer: {st.session_state['rest_time']:02d} minutes")

# Function to play sound when timer ends (using HTML and JavaScript)
def play_sound():
    st.markdown(
        """
        <audio autoplay>
        <source src="https://www.soundjay.com/button/beep-07.wav" type="audio/wav">
        </audio>
        """, 
        unsafe_allow_html=True
    )

# Start Button
if st.button("Start") and not st.session_state['running']:
    if not st.session_state['module']:
        st.error("Please enter or select a module.")
    else:
        if st.session_state['is_work_session']:
            st.session_state['timer'] = st.session_state['work_time'] * 60  # Convert to seconds
        else:
            st.session_state['timer'] = st.session_state['rest_time'] * 60  # Convert to seconds for rest
        st.session_state['running'] = True
        st.session_state['paused'] = False
        st.session_state['stop'] = False
        st.session_state['start_time'] = datetime.now()  # Capture the start time

# Pause Button
if st.session_state['running'] and not st.session_state['paused'] and st.button("Pause"):
    st.session_state['paused'] = True  # Pause the timer
    st.session_state['running'] = False  # Temporarily stop the timer

# Resume Button
if st.session_state['paused'] and st.button("Resume"):
    st.session_state['paused'] = False  # Resume the timer
    st.session_state['running'] = True

# Stop Button
if st.session_state['running'] or st.session_state['paused']:
    if st.button("Stop"):
        st.session_state['stop'] = True
        elapsed_time = (datetime.now() - st.session_state['start_time']).total_seconds() / 60  # Actual time in minutes
        st.success(f"Session stopped early. Actual time: {int(elapsed_time)} minutes.")
        log_session(st.session_state['module'], int(elapsed_time), st.session_state['sessions'], session_type)
        reset_session()  # Reset everything after stop

# Timer Countdown Logic
if st.session_state['running'] and not st.session_state['stop']:
    if st.session_state['timer'] > 0:
        time.sleep(1)
        st.session_state['timer'] -= 1
        st.experimental_rerun()  # Rerun the app to update the timer
    else:
        play_sound()  # Play sound when the timer ends
        if st.session_state['is_work_session']:
            st.success("Work session completed!")
            elapsed_time = (datetime.now() - st.session_state['start_time']).total_seconds() / 60  # Actual time in minutes
            st.session_state['completed_sessions'] += 1
            log_session(st.session_state['module'], int(elapsed_time), st.session_state['completed_sessions'], "Work")
            if st.session_state['completed_sessions'] < st.session_state['sessions']:
                st.session_state['is_work_session'] = False  # Switch to rest session
                st.session_state['timer'] = st.session_state['rest_time'] * 60  # Set timer for rest
                st.experimental_rerun()  # Restart the app to immediately show the rest timer
            else:
                st.success("All work sessions completed!")
                reset_session()  # Reset after completing all sessions
        else:
            st.success("Rest session completed!")
            log_session(st.session_state['module'], st.session_state['rest_time'], st.session_state['completed_sessions'], "Rest")
            st.session_state['is_work_session'] = True  # Switch back to work session
            st.session_state['timer'] = st.session_state['work_time'] * 60  # Set timer for next work session
            st.experimental_rerun()  # Restart the app to immediately show the work timer

# Clear Study History Button
if st.button("Clear Study History"):
    clear_history()

# View Study Schedule
if st.button("View Study Schedule"):
    df = load_csv_with_session_type()
    if not df.empty:
        st.write("Study Schedule Log:")
        st.dataframe(df)
    else:
        st.write("No study sessions have been logged yet.")

# Display Cumulative Study Hours Dashboard
df = load_csv_with_session_type()
if not df.empty:
    df['Total Time Spent (hours)'] = df['Actual Time Spent (minutes)'] / 60
    # Filter by work sessions only
    module_hours = df[df['Session Type'] == 'Work'].groupby('Module')['Total Time Spent (hours)'].sum().sort_values()

    st.write("### Cumulative Study Hours per Module")
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Horizontal bar plot with earthy color palette and larger text
    sns.barplot(x=module_hours, y=module_hours.index, palette="YlGnBu", ax=ax)
    ax.set_xlabel("Total Study Time (hours)", fontsize=14)  # Larger font for axis labels
    ax.set_ylabel("Module", fontsize=14)
    ax.set_title("Study Time by Module", fontsize=18)  # Larger font for title
    ax.tick_params(labelsize=12)  # Make module labels larger
    st.pyplot(fig)
