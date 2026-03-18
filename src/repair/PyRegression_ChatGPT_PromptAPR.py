from src.repair.AbstractRepair import AbstractRepair
import os
from datetime import datetime
from src.utils.logger import logger
from src.benchmark import create_dataset
from src.model import create_repair_tool
from src.utils.json_utils import write_json_file

class PyRegression_ChatGPT_PromptAPR(AbstractRepair):
    def __init__(self, args):
        super().__init__()
        self._load_arguments(args)

    def _load_arguments(self, args):
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Loading arguments..." + " " * 33 + "│")
        logger.info("=" * 80)
        # Model-related arguments
        self.model_name = args.model_name
        self.temperature = args.temperature
        self.top_p = args.top_p
        self.top_k = args.top_k
        self.frequency_penalty = args.frequency_penalty
        self.presence_penalty = args.presence_penalty

        # Running arguments
        self.samples = args.sample_size

        # Environment & dataset arguments
        self.input_dir = args.input_dir
        self.mapping_dir = args.mapping_dir
        self.dataset_name = args.dataset
        self.data_id = args.data_id
        self.time_limit = args.time_limit
        self.env_dir = args.env_dir
        self.early_stop = args.early_stop

        # Output and experiment name
        timestamp = datetime.now().strftime('%d-%m-%H-%M')
        self.experiment_name = f"promptAPR_{self.model_name}_{self.dataset_name}_{self.data_id}_{self.samples}_{timestamp}"
        self.output_dir = os.path.join(args.output_dir, "prompt-apr", self.dataset_name, self.model_name, self.data_id)

        # Ensure necessary directories exist
        for dir_path in [self.env_dir, self.output_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        print()
        logger.info(">>>> Arguments are successfully loaded!")
        print()

    def _load_dataset(self):
        # ==================  LOAD DATASET  ==================
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
        logger.info("=" * 80)

        dataset = create_dataset(self.dataset_name, self.input_dir, self.mapping_dir, self.env_dir, None)

        # Load single data index
        bug_info = dataset.load_single_info(self.data_id)
        print()
        logger.info(">>>> Loading dataset is successfully!")
        logger.info("- bug id             : {}".format(bug_info["bug_id"]))
        logger.info("- src dir            : {}".format(bug_info["src_dir"]))
        logger.info("- buggy relative path: {}".format(bug_info["buggy_relative_path"]))
        logger.info("- buggy file         : {}".format(bug_info["buggy_file"]))
        logger.info("- buggy loc          : {}".format(bug_info["buggy_loc"]))
        logger.info("- method loc         : {}".format(bug_info["method_loc"]))
        print()

        return dataset, bug_info

    def _load_model(self):
        # ==================   LOAD MODEL   ==================
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Loading model..." + " " * 37 + "│")
        logger.info("=" * 80)

        repair_tool = create_repair_tool(self.model_name, self.temperature, self.top_p, self.top_k, self.frequency_penalty, self.presence_penalty)
        
        print()
        logger.info(">>>> Model is successfully loaded!")
        print()

        return repair_tool

    def repair(self):
        """Repair the program."""
        # ================== RUNNING BUGGY PROGRAM ==================
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Running buggy program..." + " " * 29 + "│")
        logger.info("=" * 80)
        print("")

        dataset, bug_info = self._load_dataset()
        repair_tool = self._load_model()

        # Compile and Run test cases on Buggy Program
        validation_dir = dataset.setup_validation_dir(self.data_id)
        execution_result = dataset.execute(validation_dir)

        if execution_result["status"] == "[CE]" or execution_result["status"] == "[Plausible]" or execution_result["status"] == "[Timeout]":
            logger.error("Please check the environment and the buggy program.")
            return
        
        failed_message_list = execution_result["error_message"]
        formatted_failed_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(failed_message_list))

        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Generating & Validating Patches..." + " " * 19 + "│")
        logger.info("=" * 80)
        print("")

        # ================== GENERATE & VALIDATE PATCHES ==================
        total_non_compilable = 0
        total_compilable = 0
        total_plausible = 0
        total_timeout = 0
        total_generation_error = 0

        for index in range(self.samples):
            # ================== GENERATE PATCH ==================
            logger.info(f".......... Validating patch {index + 1}/{self.samples} ..........")
            logger.info("=" * 80)
            logger.info("│" + " " * 25 + "Generating patches..." + " " * 32 + "│")
            logger.info("=" * 80)
            print("")

            messages = self._format_prompt(bug_info["buggy_function"], formatted_failed_message)
            patch_info = repair_tool.generate_patch(1, messages)[0]

            # ================== VALIDATE PATCH ==================
            print("")
            logger.info("=" * 80)
            logger.info("│" + " " * 25 + "Validating patches..." + " " * 32 + "│")
            logger.info("=" * 80)
            print("")

            validated_patch_file = os.path.join(self.output_dir, f'{self.experiment_name}.json')

            # If the response is None, meaning API response is error
            if patch_info['patch'] is None:
                logger.warning("Cannot generate the patch!")
                total_generation_error += 1
                write_json_file(
                    {
                        "patch": None,
                        "patched_method_loc": None,
                        "status": "[ResponseError]",
                        "error_message": None,
                        "validation_time": None,
                        "response": patch_info['response'],
                        "input_tokens": patch_info['input_tokens'],
                        "output_tokens": patch_info['output_tokens'],
                        "total_cost": patch_info['total_cost']
                    },
                    validated_patch_file
                )
                continue
            
            validation_summary = dataset.validate(self.data_id, patch_info, self.time_limit)
            
            non_compilable, compilable, plausible, timeout, generation_error = validation_summary["result"]["non_compilable"], validation_summary["result"]["compilable"], validation_summary["result"]["plausible"], validation_summary["result"]["timeout"], validation_summary["result"]["generation_error"]
            total_non_compilable += non_compilable
            total_compilable += compilable
            total_plausible += plausible
            total_timeout += timeout
            total_generation_error += generation_error

            write_json_file(
                {
                    "patch": validation_summary["patch"],
                    "patched_method_loc": validation_summary["patched_method_loc"],
                    "status": validation_summary["status"],
                    "error_message": validation_summary["error_message"],
                    "validation_time": validation_summary["validation_time"],
                    "response": patch_info['response'],
                    "input_tokens": patch_info['input_tokens'],
                    "output_tokens": patch_info['output_tokens'],
                    "total_cost": patch_info['total_cost']
                },
                validated_patch_file
            )

            if self.early_stop and plausible > 0:
                logger.info(f"Early stop at patch {index + 1}")
                break
        
        logger.info("-" * 80)
        logger.info("Total patches         : {}".format(self.samples))
        logger.info("Non-compilable patches: {}".format(total_non_compilable))
        logger.info("Compilable patches    : {}".format(total_compilable))
        logger.info("Plausible patches     : {}".format(total_plausible))
        logger.info("Timeout patches       : {}".format(total_timeout))
        logger.info("Generation errors     : {}".format(total_generation_error))

    def _format_prompt(self, buggy_function: str, failedMessage: str) -> list:
        system_prompt = "You are an Automatic Program Repair Tool for Python."
        instruction = """The following Python function contains bugs:
{}
The code fails on the following test cases with the following error messages:
{}
Let's think step by step to fix the bug. Please provide a corrected version of the function.

CRITICAL REQUIREMENTS:
1. INDENTATION PRESERVATION: You must preserve the EXACT indentation of the original function.
   - If the function starts with 4 spaces, 8 spaces, or a Tab, the corrected version MUST start with the same.
   - Do NOT 'left-align' or 're-indent' the code.
   - The line-by-line leading whitespace must be an identical match to the input.
2. CONDITIONAL IMPORTS:
   - ONLY include import statements if your specific fix introduces a new library dependency not already present.
   - Place these imports inside the function body.
   - If no new library is needed to fix the bug, do NOT add any import statements.
"""

        messages = [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": instruction.format(buggy_function, failedMessage)},
        ]
        return messages