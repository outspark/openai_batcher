import os
import json
import pandas as pd
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key

def process_csv(file_obj, remove_list, mode='full_csv', selected_columns=None):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_obj)

    # Apply user-defined filters
    for word in remove_list:
        word = word.strip()
        if word:
            df.replace(word, '', inplace=True)

    if mode == 'full_csv':
        # Return the entire DataFrame as a string
        return df.to_string()
    elif mode == 'line_by_line':
        # If selected_columns is provided, select those columns
        if selected_columns:
            df = df[selected_columns]
        # Return a list of dictionaries (records)
        records = df.to_dict(orient='records')
        return records
    else:
        raise ValueError("Invalid mode. Must be 'full_csv' or 'line_by_line'.")

def create_jsonl_from_csvs(csv_files, remove_list, output_jsonl, prompt="default prompt", mode='full_csv', selected_columns=None):
    with open(output_jsonl, 'w') as outfile:
        idx = 0
        for file_obj in csv_files:
            file_obj.seek(0)  # Reset file pointer to the beginning

            if mode == 'full_csv':
                csv_content = process_csv(file_obj, remove_list, mode=mode)
                content = f"Artifact Name: {file_obj.name}:\n{csv_content}\n=====\n{prompt}"
                jsonl_entry = {
                    "custom_id": f"axiom_{idx:03d}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": content}
                        ],
                        "max_tokens": 1000
                    }
                }
                outfile.write(json.dumps(jsonl_entry) + '\n')
                idx += 1
            elif mode == 'line_by_line':
                records = process_csv(file_obj, remove_list, mode=mode, selected_columns=selected_columns)
                for record in records:
                    # Construct the content from selected columns
                    content_lines = [f"{key}: {value}" for key, value in record.items()]
                    content = "\n".join(content_lines)
                    content += f"\n=====\n{prompt}"
                    jsonl_entry = {
                        "custom_id": f"axiom_{idx:03d}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": "gpt-4",
                            "messages": [
                                {"role": "system", "content": content}
                            ],
                            "max_tokens": 1000
                        }
                    }
                    outfile.write(json.dumps(jsonl_entry) + '\n')
                    idx += 1
            else:
                raise ValueError("Invalid mode. Must be 'full_csv' or 'line_by_line'.")

def create_batch(jsonl_file):
    client = openai.OpenAI()
    batch_input_file = client.files.create(file=open(jsonl_file, "rb"), purpose="batch")
    batch_input_file_id = batch_input_file.id

    batch_job = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    return batch_job.id

def download_batch(batch_id):
    client = openai.OpenAI()
    batch = client.batches.retrieve(batch_id=batch_id)
    print(batch)

    if batch.status == "completed":
        print("Batch job is completed")
        # Retrieve the content of the output file
        file_response = client.files.content(file_id=batch.output_file_id)

        # Ensure the 'output' directory exists
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate the output file name
        batch_fname = f"{output_dir}/{datetime.now().strftime('%y%m%d%H%M')}_batch_job_results_{batch_id}.jsonl"

        # Save the batch result to a jsonl file
        with open(batch_fname, 'w') as file:
            file.write(file_response.text)

        # Handle any errors
        if batch.error_file_id is not None:
            error_response = client.files.content(file_id=batch.error_file_id)

            error_batch_name = f"{output_dir}/ERROR_{datetime.now().strftime('%y%m%d%H%M')}_batch_job_results_{batch_id}.jsonl"

            # Save the batch errors to a jsonl file
            with open(error_batch_name, 'w') as file:
                file.write(error_response.text)

        return batch_fname
    else:
        return None
