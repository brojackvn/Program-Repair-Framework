from src.repair.AbstractRepair import AbstractRepair
import os
import time
from datetime import datetime
from typing import List, Literal
from src.utils.logger import logger
from src.benchmark import create_dataset
from src.model import create_repair_tool
from src.utils.json_utils import write_json_file

class RegMiner4APR_ChatGPT_ConversationalAPR(AbstractRepair):
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
        self.attempts = args.attempts # Number of attempts to generate a patch
        self.iterations = args.iterations # Number of iterations for the conversational repair

        # Environment & dataset arguments
        self.input_dir = args.input_dir
        self.mapping_dir = args.mapping_dir
        self.dataset_name = args.dataset
        self.data_id = args.data_id
        self.time_limit = args.time_limit
        self.env_dir = args.env_dir
        self.tmp_dir = args.tmp_dir
        self.early_stop = args.early_stop
         
        self.marking_time = datetime.now().strftime('%d-%m-%H-%M')
        # self.experiment_name = f"conversationalAPR_{self.model_name}_{self.dataset_name}_{self.data_id}_{self.samples}_{timestamp}"
        self.output_dir = os.path.join(args.output_dir, "conversational-apr", self.dataset_name, self.model_name, self.data_id)

        # Ensure necessary directories exist
        for dir_path in [self.env_dir, self.output_dir, self.tmp_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        print()
        logger.info(">>>> Arguments are successfully loaded!")
        print()

    def _load_dataset(self):
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
        logger.info("=" * 80)

        dataset = create_dataset(self.dataset_name, self.input_dir, self.mapping_dir, self.env_dir, self.tmp_dir)

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

        # Compile and Run test cases on Bug
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
        last_attempt = self.attempts
        last_iteration = self.iterations
        for attempt in range(self.attempts):
            logger.info("=" * 80)
            logger.info("│" + " " * 31 + f"Attempt {attempt+1:2d}/{self.attempts:2d} ..." + " " * 30 + "│")
            logger.info("=" * 80)

            output_attempt_dir = os.path.join(self.output_dir, f'attempt-{attempt+1}-{self.attempts}')
            experiment_name = f"conversational-APR_{self.model_name}_{self.dataset_name}_{self.data_id}_attempt-{attempt+1}-{self.attempts}_{self.marking_time}" # Name of the experiment
            validated_patch_file = os.path.join(output_attempt_dir, f'{experiment_name}.json')

            plausible_found = False
            messages = []
            error_status = str()
            error_message = str()
            response = str()
            for iteration in range(self.iterations):
                logger.info("=" * 80)
                logger.info("│" + " " * 30 + f"Iteration {iteration+1:2d}/{self.iterations:2d} ..." + " " * 29 + "│")
                logger.info("=" * 80)

                # Patch generation
                logger.info(f">>>> Attempt {attempt+1:2d}/{self.attempts} >>>> Iteration {iteration+1}/{self.iterations} >>>> Generating patch ...")
                if iteration == 0:
                    messages = self._format_prompt(bug_info["buggy_function"], formatted_failed_message)
                else:
                    messages = self._format_feedback_query(messages, response, error_status, error_message)
                patch_info = repair_tool.generate_patch(1, messages)[0]
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
                    error_status = "[ResponseError]"
                    error_message = ""
                    response = patch_info['response']
                    continue
                
                # Patch validation
                logger.info(f">>>> Attempt {attempt+1:2d}/{self.attempts} >>>> Iteration {iteration+1:2d}/{self.iterations} >>>> Validating patch ...")
                validation_summary = dataset.validate(self.data_id, patch_info, self.time_limit)

                non_compilable, compilable, plausible, timeout, generation_error = validation_summary["result"]["non_compilable"], validation_summary["result"]["compilable"], validation_summary["result"]["plausible"], validation_summary["result"]["timeout"], validation_summary["result"]["generation_error"]
                if plausible == 1:
                    last_attempt = attempt + 1
                    last_iteration = iteration + 1
                    plausible_found = True
                elif non_compilable == 1:
                    error_status = "[CE]"
                    error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(validation_summary["error_message"]))
                elif compilable == 1:
                    error_status = "[FE]"
                    error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(validation_summary["error_message"]))
                elif timeout == 1:
                    error_status = "[Timeout]"
                    error_message = ""
                elif generation_error == 1:
                    error_status = "[ResponseError]"
                    error_message = ""
                response = patch_info['response']

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
                if plausible_found:
                    break
            
            if self.early_stop and plausible_found:
                break

        logger.info("=" * 80)
        if last_attempt == self.attempts and last_iteration == self.iterations:
            logger.info(f"There is no plausible patch after {self.attempts} attempts and {self.iterations} iterations")
        else:
            logger.info(f"Early stop at attempt {last_attempt}/{self.attempts} and iteration {last_iteration}/{self.iterations}")

    # ================== FORMATTING QUERY ==================
    def _format_prompt(self, buggy_function: str, failedMessage: str) -> list:
        system_prompt = "You are an Automatic Program Repair Tool."
        instruction = """The following function contains bugs:\n {}
            The code fails on the following test cases with the following error messages:\n {}
            Let's think step by step to fix the bug. Please provide a correct function.
            """
        messages = [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": instruction.format(buggy_function, failedMessage)},
        ]
        return messages
    
    def _format_feedback_query(self, messages: list, response: str, error_status: str, error_message: str) -> list:
        messages.append({"role": "assistant", "content": response})
        if error_status   == "[CE]":
            messages.append({"role": "user", "content": f'The fixed version is not compilable. The code has the following compilation error:\n{error_message}\nPlease provide the correct function along with any required imports'})
        elif error_status == "[FE]":
            messages.append({"role": "user", "content": f'The fixed version is still not correct. The code fails on the following test cases with the following error messages:\n{error_message}\nPlease provide the correct function again.'})
        elif error_status == "[ResponseError]":
            messages.append({"role": "user", "content": f'The repsonse does not provide the code function. Please provide the correct function again.'})
        elif error_status == "[Timeout]":
            messages.append({"role": "user", "content": f'The fixed version is still not correct and run out of time. Please provide the correct function again.'})
        return messages