from src.model.ChatGPT import ChatGPT
from src.utils.logger import logger

def create_repair_tool(args):       
    if args.model_name == "gpt-4o":
        return ChatGPT(args.model_name, args.temperature, args.top_p, args.top_k, args.frequency_penalty, args.presence_penalty)
    if args.model_name == "gpt-3.5-turbo":
        return ChatGPT(args.model_name, args.temperature, args.top_p, args.top_k, args.frequency_penalty, args.presence_penalty)
    else:
        logger.error("Invalid tool name: {}".format(args.model_name))