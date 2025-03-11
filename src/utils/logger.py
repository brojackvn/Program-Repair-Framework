import logging
from datetime import datetime
import os
import sys
from src.args import parser

class Logger():
    def __init__(self, args):
        now = datetime.now()

        # Set up logging file and format
        model_name = args.model_name # Name of the repair tool
        dataset_name = args.dataset # Name of the dataset
        data_id = args.data_id # ID of the buggy program
        log_name = str()
        if args.option == "prompt-apr":
            samples = args.sample_size # Number of samples to generate
            log_name = f'prompt-apr_{model_name}_{dataset_name}_{data_id}_{samples}_{now.strftime("%d-%m-%H:%M")}'
        elif args.option == "conversational-apr":
            samples = args.attempts
            log_name = f'conversational-apr_{model_name}_{dataset_name}_{data_id}_{samples}_{now.strftime("%d-%m-%H:%M")}'

        current_dir = os.getcwd()
        if not os.path.exists(os.path.join(current_dir, "logs")):
            os.makedirs(os.path.join(current_dir, "logs"))
        log_file = os.getenv("LOG", os.path.join(current_dir, f"logs/{log_name}.log"))
        logging.basicConfig(filename=log_file, encoding="utf-8", level=logging.INFO)
        logging.info(str(sys.argv))
        
    def info(self, msg):
        logging.info(msg)
        print(msg)
    
    def error(self, msg):
        logging.error("[ERROR]" + msg)
        print(msg)
    
    def warning(self, msg):
        logging.warning("[WARNING]" + msg)
        print(msg)
    
    def debug(self, msg):
        logging.info("[DEBUG]" + msg)
        print(msg)


args = parser.parse_args()

### Logger
logger = Logger(args)