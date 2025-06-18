from src.model.ChatGPT import ChatGPT
from src.utils.logger import logger

def create_repair_tool(model_name, temperature, top_p, top_k, frequency_penalty, presence_penalty):       
    if model_name == "gpt-4o":
        return ChatGPT(model_name, temperature, top_p, top_k, frequency_penalty, presence_penalty)
    if model_name == "gpt-3.5-turbo":
        return ChatGPT(model_name, temperature, top_p, top_k, frequency_penalty, presence_penalty)
    else:
        logger.error("Invalid tool name: {}".format(model_name))