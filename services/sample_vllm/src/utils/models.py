"""
Helper Functions for APIs and data structure for APIs
"""

import os
import torch
import time
from pydantic import BaseModel
from typing import List
from transformers import AutoTokenizer, AutoModelForCausalLM
from utils.env_setup import *
from utils.conversation import get_conv_template


# Pydantic Models for FastAPI APIs
class BasicChatRequest(BaseModel):
    model: int
    message: str


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: int
    messages: List[Message]


class ChatRequestLogger(BaseModel):
    model: int
    model_name: str
    start_time: float
    end_time: float
    message: str
    vllm_input: str
    vllm_response: str


# Helper Function for Loading 1x VLLM Models
def load_model(model_idx):
    """
    Return
    - tuple (Model, Tokenizer)
    """
    # type cast model_idx to string
    model_idx = str(model_idx)

    # preload model
    model_name_or_path = os.path.join(
        env_settings.MODEL_FILES_LOCATION, env_settings.MODEL_IDX[model_idx]
    )

    # get the model from model_name_or_path
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.float16,
        device_map="balanced",  # "auto"
    ).eval()

    # Setup tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        padding_side="left",
        use_fast=False,
    )

    return model, tokenizer


# Helper Function for Constructing Converstation to Send to Model
def conversation_template(request: ChatRequest):
    # type cast model_idx to string
    model_idx = str(request.model)

    # get model_name
    model_name = env_settings.MODEL_IDX[model_idx]

    conv = get_conv_template(model_name)

    while request.messages:
        msg = request.messages.pop()
        role = msg.role
        content = msg.content
        if role.strip().lower() == "user":
            conv.append_message(conv.roles[0], content)
        elif role.strip().lower() == "assistant":
            conv.append_message(conv.roles[1], content)
        else:
            raise ValueError(f"{role} is not a valid role.")
    conv.append_message(conv.roles[1], None)
    full_convo = conv.get_prompt()
    return full_convo
