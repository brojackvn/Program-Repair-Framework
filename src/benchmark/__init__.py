from src.benchmark.RegMiner4APR import RegMiner4APR
from src.utils.logger import logger

def create_dataset(dataset, input_dir, mapping_dir, env_dir, tmp_dir, output_dir):
    if dataset == "regminer4apr":
        return RegMiner4APR(input_dir, mapping_dir, env_dir, tmp_dir, output_dir)
    else:
        logger.error("Invalid dataset name: {}".format(dataset))