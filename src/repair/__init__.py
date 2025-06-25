from src.repair.RegMiner4APR_ChatGPT_PromptAPR import RegMiner4APR_ChatGPT_PromptAPR
from src.repair.RegMiner4APR_ChatGPT_ConversationalAPR import RegMiner4APR_ChatGPT_ConversationalAPR
from src.repair.RegMiner4APR_ChatGPT_PromptAPR_BIC import RegMiner4APR_ChatGPT_PromptAPR_BIC
from src.repair.RegMiner4APR_ChatGPT_ConversationalAPR_BIC import RegMiner4APR_ChatGPT_ConversationalAPR_BIC
from src.utils.logger import logger

def create_repair_instance(args):
    """
    Factory function to create a repair instance based on the specified arguments.
    """
    if args.option == "prompt-apr" and args.dataset == "regminer4apr":
        logger.info("Creating PromptAPR instance...")
        return RegMiner4APR_ChatGPT_PromptAPR(args)
    elif args.option == "conversational-apr" and args.dataset == "regminer4apr":
        logger.info("Creating ConversationalAPR instance...")
        return RegMiner4APR_ChatGPT_ConversationalAPR(args)
    elif args.option == "prompt-apr-with-bic" and args.dataset == "regminer4apr":
        logger.info("Creating PromptAPR with BIC instance...")
        return RegMiner4APR_ChatGPT_PromptAPR_BIC(args)
    elif args.option == "conversational-apr-with-bic" and args.dataset == "regminer4apr":
        logger.info("Creating ConversationalAPR with BIC instance...")
        return RegMiner4APR_ChatGPT_ConversationalAPR_BIC(args)
    else:
        logger.error("Invalid option: {}".format(args.option))
        raise ValueError("Invalid option: {}".format(args.option))