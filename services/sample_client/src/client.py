# Standard Python Library
import requests
import json
import sys
import traceback
import time
import os

# Environment Variables
GCSS_DEFENSE_MODEL_SERVER = os.getenv("GCSS_DEFENSE_MODEL_SERVER")


########## Interact with the defense model server ##########
def post_defense_model(model, message):
    """Post to start process"""
    request = {"model": model, "message": message}
    try:

        response = requests.post(
            GCSS_DEFENSE_MODEL_SERVER + "/chat/respondTo", json=request
        )

        return response.json()
    except Exception as e:
        return {
            "response": {
                "success": False,
                "message": {"role": "assistant", "content": str(e)},
            }
        }

if __name__ == "__main__":
    try:
        # Read all input from stdin
        raw_input_data = sys.stdin.read()

        # Parse the json-string input data as dictionary
        input_entries = json.loads(raw_input_data)

        # Iterate through the "input"
        # For each input_prompts, get results
        stdout_result = []
        for input_entry in input_entries:
            model = input_entry[
                "model"
            ]  # corresponding to the three Victim Models.
            input_prompt = input_entry["input_prompt"]
            behaviour = input_entry["behaviour"]

            # Rest call success to False for next
            api_call_success = False
            while not api_call_success:
                # Post input to model and time it
                start_time = time.time()
                output = post_defense_model(model, input_prompt)
                end_time = time.time()

                # Check if api call is successful
                api_call_success = output["response"]["success"]


            # Successful
            vllm_response = output["response"]["message"]["content"]

            # Output it one-by-one
            output_struct = {
                "start_time": start_time,
                "end_time": end_time,
                "model": model,
                "behaviour": behaviour,
                "input_prompt": input_prompt,
                "vllm_response": vllm_response,
            }

            stdout_result.append(output_struct)

        # construct a json string
        output_struct_json_str = json.dumps(stdout_result, indent=4)
        sys.stdout.write(output_struct_json_str)

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error decoding JSON: {e}\n")

    except Exception as e:
        sys.stderr.write(f"An error occured: {e} - {traceback.format_exc()}\n")
