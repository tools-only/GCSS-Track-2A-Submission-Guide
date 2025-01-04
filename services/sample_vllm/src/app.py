import yaml
import time
import json
import torch
import gc
from fastapi import FastAPI, HTTPException, Request
from transformers import AutoTokenizer
from utils.models import (
    torch,
    BasicChatRequest,
    ChatRequest,
    ChatRequestLogger,
    load_model,
    conversation_template,
)
from utils.env_setup import *
from utils.logger import *

# Setup logger
logger = logging.getLogger(__name__)

# Start App()
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Check for GPU availability and names
    logger.info(f"Number of GPUs available: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")

    global model_loaded
    model_loaded = {
        "model_idx": None,
        "model": None,
        "tokenizer": None,
        "loaded": False,
    }

    logger.info(
        f"Application started successfully with the following env settings: {env_settings} and initial model_loaded: {model_loaded}"
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} completed in {process_time:.4f}: {response.status_code}"
    )

    return response


@app.get("/")
async def read_root():
    logger.info("Root endpoint called")
    return {"message": "Hello! This is the VLLM server."}



@app.post("/chat/respondTo")
async def response_from_vllm_model(request: BasicChatRequest):
    # Record start time
    start_time = time.time()

    # Get requested model_idx from request
    model_idx = request.model

    # TODO: Check if request model_idx is part of the set to be loaded
    if str(model_idx) not in env_settings.MODEL_IDX.keys():
        return {
            "response": {
                "success": False,
                "message": {
                    "role": "assistant",
                    "content": "Wrong 'model' value requested!!",
                },
            }
        }

    # Global cache - check global model_loaded
    if (
        model_loaded["model_idx"] is None
        or model_idx != model_loaded["model_idx"]
    ):
        if model_idx != model_loaded["model_idx"]:
            # Clear cache, etc before reloading new model, tokenizer
            del model_loaded["model"]
            del model_loaded["tokenizer"]

            # Garbage collection & clearing cuda cache
            gc.collect()
            torch.cuda.empty_cache()

            # time sleep to account for emptying cache before loading new one
            time.sleep(5)

        # Load model, tokenizer on a per model id basis
        model, tokenizer = load_model(model_idx=request.model)
        tokenizer.pad_token = tokenizer.eos_token

        # Store in cache
        model_loaded["model_idx"] = model_idx
        model_loaded["model"] = model
        model_loaded["tokenizer"] = tokenizer

    # Get the conversation from the request to send to the model
    # Single Prompt Request from "user")
    single_prompt = ChatRequest(
        model=model_loaded["model_idx"],
        messages=[{"role": "user", "content": request.message}],
    )
    current_test_case = conversation_template(single_prompt)

    # Tokenize the prompt
    input_ids = model_loaded["tokenizer"](
        current_test_case, padding=True, return_tensors="pt"
    )
    input_ids["input_ids"] = input_ids["input_ids"].cuda()
    input_ids["attention_mask"] = input_ids["attention_mask"].cuda()
    num_input_tokens = input_ids["input_ids"].shape[1]

    response = None
    exception = None
    try:
        # generate output
        outputs = model_loaded["model"].generate(
            input_ids["input_ids"],
            attention_mask=input_ids["attention_mask"].half(),
            max_new_tokens=env_settings.VLLM_RESPONSE_MAX_TOKEN_LENGTH,
            pad_token_id=model_loaded["tokenizer"].pad_token_id,
        )

        # truncate output (limit 256 token length) & decode back to string representation
        response = model_loaded["tokenizer"].batch_decode(
            # outputs[:, num_input_tokens:max_response_tokens_to_judge],
            outputs[:, num_input_tokens:],
            skip_special_tokens=True,
        )

        logger.debug(
            f"VLLM:{request.model}\tATTACK PROMPT:{current_test_case}\tSTATUS CODE:200\tRESPONSE:{response[0]}"
        )

        return {
            "response": {
                "success": True,
                "message": {"role": "assistant", "content": response[0]},
            }
        }

    except Exception as e:
        exception = e
        status_code = 500
        logger.error(
            f"VLLM:{request.model}\tATTACK PROMPT:{current_test_case}\tSTATUS CODE:{status_code}\tRESPONSE: Error: {e}"
        )
        return {
            "response": {
                "success": False,
                "message": {"role": "assistant", "content": str(e)},
            }
        }
    finally:
        if response is not None and exception is None:
            vllm_response = response[0]

            # Log the response
            # Data Structure "Validation"
            request_body_struct = ChatRequestLogger(
                model=request.model,
                model_name=env_settings.MODEL_IDX[str(request.model)],
                message=request.message,
                start_time=start_time,
                end_time=time.time(),
                vllm_input=f"{current_test_case}",
                vllm_response=vllm_response,
            )

            # construct a json string
            request_body_json_str = json.dumps(request_body_struct.__dict__)

            # save it
            respond_to_tracker(message=f"{request_body_json_str}")
