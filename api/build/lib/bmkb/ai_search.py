import os
from flask import Request, current_app
#from . import db as db_utils
#from . import utils as utils
from .llm import LLM
from .llm.openai_api import OpenAILLM
from .llm.rate_limiter import ai_search_rate_limiter

def transform_ai_query(req_obj):

    if not ai_search_rate_limiter.can_make_request():
        rate_status = ai_search_rate_limiter.get_status()
        error_obj = {"error_list":[{"error":"rate-limit-exceeded"}]}
        return error_obj, 429

    custom_app = current_app
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    try:
        llm_client: LLM
        llm_client = OpenAILLM()
        search_params = llm_client.advanced_search(req_obj["query"])
        if search_params is None:
            error_obj = {"error_list":[{"error":"Unable to parse query using LLM provider"}]}
            return error_obj, 500
        if "error" in search_params:
            if search_params["error"] == llm_client.key_error_str:
                error_obj = {"error_list":[{"error":"Unable to find LLM API key"}]}
                return error_obj, 500
            elif search_params["error"] == llm_client.relevancy_error_str:
                error_obj = {"error_list":[{"error":"User made non-biomarker query"}]}
                return error_obj, 400
        return search_params, 200
    except Exception as e:
        error_obj = {"error_list":[{"error":str(e)}]}
        return error_obj, 500
