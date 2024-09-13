# import streamlit as st
# import time
# import pandas as pd
# from gpt_batch_processor import create_jsonl_from_csvs, create_batch, download_batch
# from dotenv import load_dotenv
# import os

# # Ensure .env file is in the correct directory
# load_dotenv("/home/hmc/work/axiom_ctf_milvus/gpt_batcher/.env")

# # Title
# st.title("GPT Batch Data Generator")

# # File upload
# uploaded_files = st.file_uploader("Upload your CSV files", type=["csv"], accept_multiple_files=True)

# remove_list = st.text_area("Enter any words to remove (comma-separated)")
# prompt = st.text_area("Enter prompt text")

# # Initialize session state variables
# if 'batch_id' not in st.session_state:
#     st.session_state.batch_id = None
# if 'batch_ready' not in st.session_state:
#     st.session_state.batch_ready = False
# if 'batch_created_time' not in st.session_state:
#     st.session_state.batch_created_time = None
# if 'last_checked_time' not in st.session_state:
#     st.session_state.last_checked_time = 0
# if 'check_interval' not in st.session_state:
#     st.session_state.check_interval = 5  # Default check interval
# if 'num_entries' not in st.session_state:
#     st.session_state.num_entries = 0
# if 'result_file' not in st.session_state:
#     st.session_state.result_file = None

# def get_num_entries(jsonl_file):
#     """Get the number of lines in the jsonl file."""
#     with open(jsonl_file, 'r') as f:
#         return sum(1 for _ in f)

# def update_check_interval():
#     """Update the check interval based on the number of entries."""
#     base_interval = 5  # Base interval in seconds
#     increment_per_10_entries = 5  # Additional seconds per 10 entries
#     num_entries = st.session_state.num_entries

#     if num_entries > 10:
#         st.session_state.check_interval = base_interval + ((num_entries // 10) * increment_per_10_entries)
#     else:
#         st.session_state.check_interval = base_interval

# def check_batch_status():
#     """Check batch status at intervals without blocking the app."""
#     current_time = time.time()
#     if current_time - st.session_state.last_checked_time >= st.session_state.check_interval:
#         st.session_state.last_checked_time = current_time
#         result_file = download_batch(st.session_state.batch_id)
#         if result_file:
#             st.session_state.batch_ready = True
#             st.session_state.result_file = result_file

# # Handle batch creation
# if uploaded_files and st.button("Create GPT Batch"):
#     # Temporary JSONL file creation path
#     jsonl_file = "temp_batch.jsonl"

#     # Create JSONL from the uploaded CSV files
#     create_jsonl_from_csvs(
#         csv_files=uploaded_files,
#         remove_list=remove_list.split(","),
#         output_jsonl=jsonl_file,
#         prompt=prompt
#     )

#     # Get the number of entries (lines) in the jsonl file
#     st.session_state.num_entries = get_num_entries(jsonl_file)

#     # Update the check interval based on the number of entries
#     update_check_interval()

#     # Send the batch for processing
#     st.session_state.batch_id = create_batch(jsonl_file)
#     st.session_state.batch_created_time = time.time()
#     st.session_state.last_checked_time = 0
#     st.session_state.batch_ready = False
#     st.session_state.result_file = None

#     st.success(f"Batch created with ID: {st.session_state.batch_id}")
#     st.info(f"Checking batch status every {st.session_state.check_interval} seconds.")

# # Check batch status if batch is not ready
# if st.session_state.batch_id and not st.session_state.batch_ready:
#     check_batch_status()

# # Display download button and status message if batch_id exists
# if st.session_state.batch_id:
#     if st.session_state.batch_ready:
#         st.success("Batch is ready for download!")
#         with open(st.session_state.result_file, 'rb') as file:
#             st.download_button(
#                 label="Download Results",
#                 data=file.read(),
#                 file_name=os.path.basename(st.session_state.result_file),
#                 mime="application/json"
#             )
#     else:
#         st.warning("Batch is not ready yet. Please wait.")
#         # Disabled download button
#         st.download_button(
#             label="Download Results",
#             data="",
#             disabled=True,
#             help="Batch is not ready yet.",
#         )
#         # Show next check time
#         next_check_in = int(st.session_state.check_interval - (time.time() - st.session_state.last_checked_time))
#         if next_check_in < 0:
#             next_check_in = 0
#         st.info(f"Next automatic status check in {next_check_in} seconds.")
#         # Auto-refresh the app after the interval
#         st.rerun()
import streamlit as st
import time
import pandas as pd
from gpt_batch_processor import create_jsonl_from_csvs, create_batch, download_batch
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv("/home/hmc/work/axiom_ctf_milvus/gpt_batcher/.env")

# Title
st.title("GPT Batch Data Generator")

# File upload
uploaded_files = st.file_uploader("Upload your CSV files", type=["csv"], accept_multiple_files=True)

# Initialize session state variables
if 'batch_id' not in st.session_state:
    st.session_state.batch_id = None
if 'batch_ready' not in st.session_state:
    st.session_state.batch_ready = False
if 'batch_created_time' not in st.session_state:
    st.session_state.batch_created_time = None
if 'last_checked_time' not in st.session_state:
    st.session_state.last_checked_time = 0
if 'check_interval' not in st.session_state:
    st.session_state.check_interval = 5  # Default check interval
if 'num_entries' not in st.session_state:
    st.session_state.num_entries = 0
if 'result_file' not in st.session_state:
    st.session_state.result_file = None

# Select processing mode
mode_option = st.radio("Select processing mode", ('Use entire CSV as text', 'Process CSV line by line'))

remove_list = st.text_area("Enter any words to remove (comma-separated)")
prompt = st.text_area("Enter prompt text")

selected_columns = None

if mode_option == 'Process CSV line by line' and uploaded_files:
    # For simplicity, use the columns from the first uploaded file
    uploaded_files[0].seek(0)
    df = pd.read_csv(uploaded_files[0])
    columns = df.columns.tolist()
    selected_columns = st.multiselect('Select columns to include in the prompt', options=columns, default=columns)

def update_check_interval():
    """Update the check interval based on the number of entries."""
    base_interval = 10  # Base interval in seconds
    increment_per_100_entries = 10  # Additional seconds per 100 entries
    num_entries = st.session_state.num_entries

    if num_entries > 100:
        st.session_state.check_interval = base_interval + ((num_entries // 100) * increment_per_100_entries)
    else:
        st.session_state.check_interval = base_interval

def check_batch_status():
    """Check batch status at intervals without blocking the app."""
    current_time = time.time()
    if current_time - st.session_state.last_checked_time >= st.session_state.check_interval:
        st.session_state.last_checked_time = current_time
        result_file = download_batch(st.session_state.batch_id)
        if result_file:
            st.session_state.batch_ready = True
            st.session_state.result_file = result_file

# Handle batch creation
if uploaded_files and st.button("Create GPT Batch"):
    # Temporary JSONL file creation path
    jsonl_file = "temp/temp_batch.jsonl"

    # Determine the mode
    mode = 'full_csv' if mode_option == 'Use entire CSV as text' else 'line_by_line'

    # Create JSONL from the uploaded CSV files
    create_jsonl_from_csvs(
        csv_files=uploaded_files,
        remove_list=[word.strip() for word in remove_list.split(",")],
        output_jsonl=jsonl_file,
        prompt=prompt,
        mode=mode,
        selected_columns=selected_columns
    )

    # Get the number of entries (lines) in the jsonl file
    with open(jsonl_file, 'r') as f:
        st.session_state.num_entries = sum(1 for _ in f)

    # Update the check interval based on the number of entries
    update_check_interval()

    # Send the batch for processing
    st.session_state.batch_id = create_batch(jsonl_file)
    st.session_state.batch_created_time = time.time()
    st.session_state.last_checked_time = 0
    st.session_state.batch_ready = False
    st.session_state.result_file = None

    st.success(f"Batch created with ID: {st.session_state.batch_id}")
    st.info(f"Checking batch status every {st.session_state.check_interval} seconds.")

# Check batch status if batch is not ready
if st.session_state.batch_id and not st.session_state.batch_ready:
    check_batch_status()

# Display download button and status message if batch_id exists
if st.session_state.batch_id:
    if st.session_state.batch_ready:
        st.success("Batch is ready for download!")
        with open(st.session_state.result_file, 'rb') as file:
            st.download_button(
                label="Download Results",
                data=file.read(),
                file_name=os.path.basename(st.session_state.result_file),
                mime="application/json"
            )
    else:
        st.warning("Batch is not ready yet. Please wait.")
        # Disabled download button
        st.download_button(
            label="Download Results",
            data="",
            disabled=True,
            help="Batch is not ready yet.",
        )
        # Show next check time
        next_check_in = int(st.session_state.check_interval - (time.time() - st.session_state.last_checked_time))
        if next_check_in < 0:
            next_check_in = 0
        st.info(f"Next automatic status check in {next_check_in} seconds.")
        # Auto-refresh the app after the interval
        time.sleep(st.session_state.check_interval)
        st.rerun()
