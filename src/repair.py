import os
import time
from datetime import datetime
from typing import List, Literal
from src.utils.logger import logger
from src.benchmark import create_dataset
from src.model import create_repair_tool
from src.utils.json_utils import read_json_file

def prompt_apr(args):    
    # ==================  LOAD ARGUMENTS  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading arguments..." + " " * 33 + "│")
    logger.info("=" * 80)

    # Model arguments
    model_name = args.model_name # Name of the repair tool
    temperature = args.temperature # Temperature for sampling
    top_p = args.top_p # Top-p for sampling
    top_k = args.top_k # Top-k for sampling
    frequency_penalty = args.frequency_penalty # Frequency penalty for sampling
    presence_penalty = args.presence_penalty # Presence penalty for sampling
    # Running arguments
    samples = args.sample_size # Number of samples to generate
    # Environment arguments
    input_dir = args.input_dir # Path to the input file (i.e., the buggy program, buggy lines, context lines, ...)
    mapping_dir = args.mapping_dir # Path to the mapping file
    dataset_name = args.dataset # Name of the dataset
    data_id = args.data_id # ID of the buggy program
    time_limit = args.time_limit # Time limit for the repair process
    experiment_name = f"promptAPR_{model_name}_{dataset_name}_{data_id}_{samples}_{datetime.now().strftime('%d-%m-%H-%M')}" # Name of the experiment
    output_dir = os.path.join(args.output_dir, "prompt-apr", dataset_name, model_name, data_id)
    env_dir = args.env_dir # Path to the project directory
    tmp_dir = args.tmp_dir # Path to the temporary directory
    early_stop = args.early_stop # Early stop flag

    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    
    print()
    logger.info(">>>> Arguments are successfully loaded!")
    print()
    
    # ==================  LOAD DATASET  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
    logger.info("=" * 80)

    dataset = create_dataset(dataset_name, input_dir, mapping_dir, env_dir, tmp_dir, output_dir)

    # Load single data index
    bug_info = dataset.load_single_info(data_id)
    
    print()
    logger.info(">>>> Loading dataset is successfully!")
    logger.info("- bug id             : {}".format(bug_info["bug_id"]))
    logger.info("- src dir            : {}".format(bug_info["src_dir"]))
    logger.info("- buggy relative path: {}".format(bug_info["buggy_relative_path"]))
    logger.info("- buggy file         : {}".format(bug_info["buggy_file"]))
    logger.info("- buggy loc          : {}".format(bug_info["buggy_loc"]))
    logger.info("- method loc         : {}".format(bug_info["method_loc"]))
    print()

    # ==================   LOAD MODEL   ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading model..." + " " * 37 + "│")
    logger.info("=" * 80)

    repair_tool = create_repair_tool(args)
    print()
    logger.info(">>>> Model is successfully loaded!")
    print()

    # ================== FORMATTING QUERY ==================
    def format_prompt(buggy_function: str, failedMessage: str) -> list:
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
    
    # ================== RUNNING BUGGY PROGRAM ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Running buggy program..." + " " * 29 + "│")
    logger.info("=" * 80)
    print("")

    # Compile and Run test cases on Bug
    validation_dir = dataset.setup_validation_dir(data_id)
    execution_result = dataset.execute(validation_dir)
    if execution_result["status"] == "[CE]" or execution_result["status"] == "[Plausible]" or execution_result["status"] == "[Timeout]":
        logger.error("Please check the environment and the buggy program.")
        return
    failed_message_list = execution_result["error_message"]
    formatted_failed_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(failed_message_list))

    # ================== GENERATE & VALIDATE PATCHES ==================
    total_non_compilable = 0
    total_compilable = 0
    total_plausible = 0
    total_timeout = 0
    total_generation_error = 0

    for index in range(samples):
        # ================== GENERATE PATCH ==================
        logger.info(f".......... Validating patch {index + 1}/{samples} ..........")
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Generating patches..." + " " * 32 + "│")
        logger.info("=" * 80)
        print("")

        messages = format_prompt(bug_info["buggy_function"], formatted_failed_message)
        patch_info_list = repair_tool.generate_patch(1, messages)

        print("")
        # ================== VALIDATE PATCH ==================
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Validating patches..." + " " * 32 + "│")
        logger.info("=" * 80)
        print("")

        non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
        total_non_compilable += non_compilable
        total_compilable += compilable
        total_plausible += plausible
        total_timeout += timeout
        total_generation_error += generation_error

        if early_stop and plausible > 0:
            logger.info(f"Early stop at patch {index + 1}")
            break
        
    logger.info("Total patches         : {}".format(samples))
    logger.info("Non-compilable patches: {}".format(total_non_compilable))
    logger.info("Compilable patches    : {}".format(total_compilable))
    logger.info("Plausible patches     : {}".format(total_plausible))
    logger.info("Timeout patches       : {}".format(total_timeout))
    logger.info("Generation errors     : {}".format(total_generation_error))

def conversational_apr(args):
    # ==================  LOAD ARGUMENTS  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading arguments..." + " " * 33 + "│")
    logger.info("=" * 80)

    # Starting time
    marking_time = datetime.now().strftime('%d-%m-%H-%M')

    # Model arguments
    model_name = args.model_name # Name of the repair tool
    temperature = args.temperature # Temperature for sampling
    top_p = args.top_p # Top-p for sampling
    top_k = args.top_k # Top-k for sampling
    frequency_penalty = args.frequency_penalty # Frequency penalty for sampling
    presence_penalty = args.presence_penalty # Presence penalty for sampling
    # Running arguments
    attempts = args.attempts # Number of attempts to generate a patch
    iterations = args.iterations # Number of iterations for the conversational repair
    # Environment arguments
    input_dir = args.input_dir # Path to the input file (i.e., the buggy program, buggy lines, context lines, ...)
    mapping_dir = args.mapping_dir # Path to the mapping file
    dataset_name = args.dataset # Name of the dataset
    data_id = args.data_id # ID of the buggy program
    time_limit = args.time_limit # Time limit for the repair process
    # experiment_name = f"promptAPR_{model_name}_{dataset_name}_{data_id}_{attempts}_{datetime.now().strftime('%d-%m-%H-%M')}" # Name of the experiment
    output_dir = os.path.join(args.output_dir, "conversational-apr", dataset_name, model_name, data_id)
    env_dir = args.env_dir # Path to the project directory
    tmp_dir = args.tmp_dir # Path to the temporary directory
    early_stop = args.early_stop # Early stop flag

    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    
    print()
    logger.info(">>>> Arguments are successfully loaded!")
    print()
    
    # ==================  LOAD DATASET  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
    logger.info("=" * 80)

    dataset = create_dataset(dataset_name, input_dir, mapping_dir, env_dir, tmp_dir, output_dir)

    # Load single data index
    bug_info = dataset.load_single_info(data_id)
    
    print()
    logger.info(">>>> Loading dataset is successfully!")
    logger.info("- bug id             : {}".format(bug_info["bug_id"]))
    logger.info("- src dir            : {}".format(bug_info["src_dir"]))
    logger.info("- buggy relative path: {}".format(bug_info["buggy_relative_path"]))
    logger.info("- buggy file         : {}".format(bug_info["buggy_file"]))
    logger.info("- buggy loc          : {}".format(bug_info["buggy_loc"]))
    logger.info("- method loc         : {}".format(bug_info["method_loc"]))
    print()

    # ==================   LOAD MODEL   ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading model..." + " " * 37 + "│")
    logger.info("=" * 80)

    repair_tool = create_repair_tool(args)
    print()
    logger.info(">>>> Model is successfully loaded!")
    print()

    # ================== FORMATTING QUERY ==================
    def format_prompt(buggy_function: str, failedMessage: str) -> list:
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
    
    def format_feedback_query(messages: list, response: str, error_status: str, error_message: str) -> list:
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
    
    # ================== RUNNING BUGGY PROGRAM ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Running buggy program..." + " " * 29 + "│")
    logger.info("=" * 80)
    print("")

    # Compile and Run test cases on Bug
    validation_dir = dataset.setup_validation_dir(data_id)
    execution_result = dataset.execute(validation_dir)
    if execution_result["status"] == "[CE]" or execution_result["status"] == "[Plausible]" or execution_result["status"] == "[Timeout]":
        logger.error("Please check the environment and the buggy program.")
        return
    failed_message = execution_result["error_message"]
    formatted_failed_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(failed_message))

    # ================== GENERATE & VALIDATE PATCHES ==================
    last_attempt = attempts
    last_iteration = iterations
    for attempt in range(attempts):
        logger.info("=" * 80)
        logger.info("│" + " " * 31 + f"Attempt {attempt+1:2d}/{attempts:2d} ..." + " " * 30 + "│")
        logger.info("=" * 80)

        output_attempt_dir = os.path.join(output_dir, f'attempt-{attempt+1}-{attempts}')
        dataset.output_dir = output_attempt_dir
        experiment_name = f"conversational-APR_{model_name}_{dataset_name}_{data_id}_attempt-{attempt+1}-{attempts}_{marking_time}" # Name of the experiment
        
        # First attempt 
        # Generate patch
        logger.info("=" * 80)
        logger.info("│" + " " * 30 + f"Iteration  1/{iterations:2d} ..." + " " * 29 + "│")
        logger.info("=" * 80)
        logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration 1/{iterations} >>>> Generating patch ...")
        messages = format_prompt(bug_info["buggy_function"], formatted_failed_message)
        patch_info_list = repair_tool.generate_patch(1, messages)
        # Validate patch
        logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration 1/{iterations} >>>> Validating patch ...")

        error_status = str()
        error_message = str()
        response = str()
        
        non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
        if plausible == 1:
            logger.info(f"Early stop at attempt {attempt+1}/{attempts} and iteration 1/{iterations}")
            last_attempt = attempt + 1
            last_iteration = 1
            return
        elif non_compilable == 1:
            error_status = "[CE]"
            error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
        elif compilable == 1:
            error_status = "[FE]"
            error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))    
        elif timeout == 1:
            error_status = "[Timeout]"
            error_message = ""
        elif generation_error == 1:
            error_status = "[ResponseError]"
            error_message = ""

        for iteration in range(iterations-1):
            logger.info("=" * 80)
            logger.info("│" + " " * 30 + f"Iteration {iteration+2:2d}/{iterations:2d} ..." + " " * 29 + "│")
            logger.info("=" * 80)

            # Generate patch
            logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration {iteration+2:2d}/{iterations} >>>> Generating patch ...")
            messages = format_feedback_query(messages, response, error_status, error_message)
            patch_info_list = repair_tool.generate_patch(1, messages)
            # Validate patch
            logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration {iteration+2:2d}/{iterations} >>>> Validating patch ...")
            
            non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
            if plausible == 1:
                logger.info(f"Early stop at attempt {attempt+1}/{attempts} and iteration {iteration+2}/{iterations}")
                last_attempt = attempt + 1
                last_iteration = iteration + 2
                return
            elif non_compilable == 1:
                error_status = "[CE]"
                error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
            elif compilable == 1:
                error_status = "[FE]"
                error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
            elif timeout == 1:
                error_status = "[Timeout]"
                error_message = ""
            elif generation_error == 1:
                error_status = "[ResponseError]"
                error_message = ""
    
    logger.info("=" * 80)
    if last_attempt == attempts and last_iteration == iterations:
        logger.info(f"There is no plausible patch after {attempts} attempts and {iterations} iterations")
    else:
        logger.info(f"Early stop at attempt {last_attempt}/{attempts} and iteration {last_iteration}/{iterations}")

def prompt_apr_with_bic(args):
    # ==================  LOAD ARGUMENTS  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading arguments..." + " " * 33 + "│")
    logger.info("=" * 80)

    # Model arguments
    model_name = args.model_name # Name of the repair tool
    temperature = args.temperature # Temperature for sampling
    top_p = args.top_p # Top-p for sampling
    top_k = args.top_k # Top-k for sampling
    frequency_penalty = args.frequency_penalty # Frequency penalty for sampling
    presence_penalty = args.presence_penalty # Presence penalty for sampling
    # Running arguments
    samples = args.sample_size # Number of samples to generate
    # Environment arguments
    input_dir = args.input_dir # Path to the input file (i.e., the buggy program, buggy lines, context lines, ...)
    mapping_dir = args.mapping_dir # Path to the mapping file
    dataset_name = args.dataset # Name of the dataset
    data_id = args.data_id # ID of the buggy program
    time_limit = args.time_limit # Time limit for the repair process
    experiment_name = f"PromptAPR-BIC_{model_name}_{dataset_name}_{data_id}_{samples}_{datetime.now().strftime('%d-%m-%H-%M')}" # Name of the experiment
    output_dir = os.path.join(args.output_dir, "prompt-apr-bic", dataset_name, model_name, data_id)
    env_dir = args.env_dir # Path to the project directory
    tmp_dir = args.tmp_dir # Path to the temporary directory
    early_stop = args.early_stop # Early stop flag

    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    
    print()
    logger.info(">>>> Arguments are successfully loaded!")
    print()
    
    # ==================  LOAD DATASET  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
    logger.info("=" * 80)

    dataset = create_dataset(dataset_name, input_dir, mapping_dir, env_dir, tmp_dir, output_dir)

    # Load single data index
    bug_info = dataset.load_single_info(data_id)
    
    print()
    logger.info(">>>> Loading dataset is successfully!")
    logger.info("- bug id             : {}".format(bug_info["bug_id"]))
    logger.info("- src dir            : {}".format(bug_info["src_dir"]))
    logger.info("- buggy relative path: {}".format(bug_info["buggy_relative_path"]))
    logger.info("- buggy file         : {}".format(bug_info["buggy_file"]))
    logger.info("- buggy loc          : {}".format(bug_info["buggy_loc"]))
    logger.info("- method loc         : {}".format(bug_info["method_loc"]))
    print()

    # ==================   LOAD MODEL   ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading model..." + " " * 37 + "│")
    logger.info("=" * 80)

    repair_tool = create_repair_tool(args)
    print()
    logger.info(">>>> Model is successfully loaded!")
    print()

    # ================== FORMATTING QUERY ==================
    def format_prompt(buggy_function: str, failedMessage: str, bug_inducing_changes: str, bic_commit_message: str) -> list:
        system_prompt = "You are an expert Automatic Program Repair Tool specialized in fixing regression bugs."
        
        if bug_inducing_changes == "":
            instruction = """## Task\n
The following function contains a bug:\n{}\n
Bug-Inducing Changes: There are no changes in the buggy function itself. The bug is caused by other modifications in the bug-inducing commit. Focus on the bug-inducing commit message.\n
Bug-Inducing Commit Message:\n{}\n
Failing Test Cases and Error Messages:\n{}\n
## Instructions
Please think step by step to identify the root cause from the bug-inducing changes and their relationship to regression fixing patches. Provide the correct function."""
            messages = [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": instruction.format(buggy_function, bic_commit_message, failedMessage)},
            ]
        else:
            instruction = """## Task\n
The following function contains a bug:\n{}\n
Bug-Inducing Changes:\n{}\n
Bug-Inducing Commit Message:\n{}\n
Failing Test Cases and Error Messages:\n{}\n
## Instructions
Please think step by step to identify the root cause from the bug-inducing changes and their relationship to regression fixing patches. Provide the correct function."""
            messages = [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": instruction.format(buggy_function, bug_inducing_changes, bic_commit_message, failedMessage)},
            ]
        return messages
    
    # ================== RUNNING BUGGY PROGRAM ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Running buggy program..." + " " * 29 + "│")
    logger.info("=" * 80)
    print("")

    # Compile and Run test cases on Bug
    validation_dir = dataset.setup_validation_dir(data_id)
    execution_result = dataset.execute(validation_dir)
    if execution_result["status"] == "[CE]" or execution_result["status"] == "[Plausible]" or execution_result["status"] == "[Timeout]":
        logger.error("Please check the environment and the buggy program.")
        return
    failed_message_list = execution_result["error_message"]
    formatted_failed_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(failed_message_list))

    # ================== GENERATE & VALIDATE PATCHES ==================
    total_non_compilable = 0
    total_compilable = 0
    total_plausible = 0
    total_timeout = 0
    total_generation_error = 0

    for index in range(samples):
        # ================== GENERATE PATCH ==================
        logger.info(f".......... Validating patch {index + 1}/{samples} ..........")
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Generating patches..." + " " * 32 + "│")
        logger.info("=" * 80)
        print("")

        messages = format_prompt(bug_info["buggy_function"], formatted_failed_message, bug_info["bug_inducing_changes"], bug_info["bic_commit_message"])
        patch_info_list = repair_tool.generate_patch(1, messages)

        print("")
        # ================== VALIDATE PATCH ==================
        logger.info("=" * 80)
        logger.info("│" + " " * 25 + "Validating patches..." + " " * 32 + "│")
        logger.info("=" * 80)
        print("")

        non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
        total_non_compilable += non_compilable
        total_compilable += compilable
        total_plausible += plausible
        total_timeout += timeout
        total_generation_error += generation_error

        if early_stop and plausible > 0:
            logger.info(f"Early stop at patch {index + 1}")
            break
        
    logger.info("Total patches         : {}".format(samples))
    logger.info("Non-compilable patches: {}".format(total_non_compilable))
    logger.info("Compilable patches    : {}".format(total_compilable))
    logger.info("Plausible patches     : {}".format(total_plausible))
    logger.info("Timeout patches       : {}".format(total_timeout))
    logger.info("Generation errors     : {}".format(total_generation_error))

def conversational_apr_with_bic(args):
        # ==================  LOAD ARGUMENTS  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading arguments..." + " " * 33 + "│")
    logger.info("=" * 80)

    # Starting time
    marking_time = datetime.now().strftime('%d-%m-%H-%M')

    # Model arguments
    model_name = args.model_name # Name of the repair tool
    temperature = args.temperature # Temperature for sampling
    top_p = args.top_p # Top-p for sampling
    top_k = args.top_k # Top-k for sampling
    frequency_penalty = args.frequency_penalty # Frequency penalty for sampling
    presence_penalty = args.presence_penalty # Presence penalty for sampling
    # Running arguments
    attempts = args.attempts # Number of attempts to generate a patch
    iterations = args.iterations # Number of iterations for the conversational repair
    # Environment arguments
    input_dir = args.input_dir # Path to the input file (i.e., the buggy program, buggy lines, context lines, ...)
    mapping_dir = args.mapping_dir # Path to the mapping file
    dataset_name = args.dataset # Name of the dataset
    data_id = args.data_id # ID of the buggy program
    time_limit = args.time_limit # Time limit for the repair process
    # experiment_name = f"ConversationalAPR-BIC_{model_name}_{dataset_name}_{data_id}_{attempts}_{datetime.now().strftime('%d-%m-%H-%M')}" # Name of the experiment
    output_dir = os.path.join(args.output_dir, "conversational-apr-bic", dataset_name, model_name, data_id)
    env_dir = args.env_dir # Path to the project directory
    tmp_dir = args.tmp_dir # Path to the temporary directory
    early_stop = args.early_stop # Early stop flag

    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    
    print()
    logger.info(">>>> Arguments are successfully loaded!")
    print()
    
    # ==================  LOAD DATASET  ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading dataset..." + " " * 35 + "│")
    logger.info("=" * 80)

    dataset = create_dataset(dataset_name, input_dir, mapping_dir, env_dir, tmp_dir, output_dir)

    # Load single data index
    bug_info = dataset.load_single_info(data_id)
    
    print()
    logger.info(">>>> Loading dataset is successfully!")
    logger.info("- bug id             : {}".format(bug_info["bug_id"]))
    logger.info("- src dir            : {}".format(bug_info["src_dir"]))
    logger.info("- buggy relative path: {}".format(bug_info["buggy_relative_path"]))
    logger.info("- buggy file         : {}".format(bug_info["buggy_file"]))
    logger.info("- buggy loc          : {}".format(bug_info["buggy_loc"]))
    logger.info("- method loc         : {}".format(bug_info["method_loc"]))
    print()

    # ==================   LOAD MODEL   ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Loading model..." + " " * 37 + "│")
    logger.info("=" * 80)

    repair_tool = create_repair_tool(args)
    print()
    logger.info(">>>> Model is successfully loaded!")
    print()

    # ================== FORMATTING QUERY ==================
    def format_prompt(buggy_function: str, failedMessage: str, bug_inducing_changes: str, bic_commit_message: str) -> list:
        system_prompt = "You are an expert Automatic Program Repair Tool specialized in fixing regression bugs."
        
        if bug_inducing_changes == "":
            instruction = """## Task\n
The following function contains a bug:\n{}\n
Bug-Inducing Changes: There are no changes in the buggy function itself. The bug is caused by other modifications in the bug-inducing commit. Focus on the bug-inducing commit message.\n
Bug-Inducing Commit Message:\n{}\n
Failing Test Cases and Error Messages:\n{}\n
## Instructions
Please think step by step to identify the root cause from the bug-inducing changes and their relationship to regression fixing patches. Provide the correct function."""
            messages = [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": instruction.format(buggy_function, bic_commit_message, failedMessage)},
            ]
        else:
            instruction = """## Task\n
The following function contains a bug:\n{}\n
Bug-Inducing Changes:\n{}\n
Bug-Inducing Commit Message:\n{}\n
Failing Test Cases and Error Messages:\n{}\n
## Instructions
Please think step by step to identify the root cause from the bug-inducing changes and their relationship to regression fixing patches. Provide the correct function."""
            messages = [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": instruction.format(buggy_function, bug_inducing_changes, bic_commit_message, failedMessage)},
            ]
        return messages
    
    def format_feedback_query(messages: list, response: str, error_status: str, error_message: str) -> list:
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
    
    # ================== RUNNING BUGGY PROGRAM ==================
    logger.info("=" * 80)
    logger.info("│" + " " * 25 + "Running buggy program..." + " " * 29 + "│")
    logger.info("=" * 80)
    print("")

    # Compile and Run test cases on Bug
    validation_dir = dataset.setup_validation_dir(data_id)
    execution_result = dataset.execute(validation_dir)
    if execution_result["status"] == "[CE]" or execution_result["status"] == "[Plausible]" or execution_result["status"] == "[Timeout]":
        logger.error("Please check the environment and the buggy program.")
        return
    failed_message = execution_result["error_message"]
    formatted_failed_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(failed_message))

    # ================== GENERATE & VALIDATE PATCHES ==================
    last_attempt = attempts
    last_iteration = iterations
    for attempt in range(attempts):
        logger.info("=" * 80)
        logger.info("│" + " " * 31 + f"Attempt {attempt+1:2d}/{attempts:2d} ..." + " " * 30 + "│")
        logger.info("=" * 80)

        output_attempt_dir = os.path.join(output_dir, f'attempt-{attempt+1}-{attempts}')
        dataset.output_dir = output_attempt_dir
        experiment_name = f"ConversationalAPR-BIC_{model_name}_{dataset_name}_{data_id}_attempt-{attempt+1}-{attempts}_{marking_time}" # Name of the experiment
        
        # First attempt 
        # Generate patch
        logger.info("=" * 80)
        logger.info("│" + " " * 30 + f"Iteration  1/{iterations:2d} ..." + " " * 29 + "│")
        logger.info("=" * 80)
        logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration 1/{iterations} >>>> Generating patch ...")
        messages = format_prompt(bug_info["buggy_function"], formatted_failed_message, bug_info["bug_inducing_changes"], bug_info["bic_commit_message"])
        patch_info_list = repair_tool.generate_patch(1, messages)
        # Validate patch
        logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration 1/{iterations} >>>> Validating patch ...")

        error_status = str()
        error_message = str()
        response = str()
        
        non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
        if plausible == 1:
            logger.info(f"Early stop at attempt {attempt+1}/{attempts} and iteration 1/{iterations}")
            last_attempt = attempt + 1
            last_iteration = 1
            return
        elif non_compilable == 1:
            error_status = "[CE]"
            error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
        elif compilable == 1:
            error_status = "[FE]"
            error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))    
        elif timeout == 1:
            error_status = "[Timeout]"
            error_message = ""
        elif generation_error == 1:
            error_status = "[ResponseError]"
            error_message = ""

        for iteration in range(iterations-1):
            logger.info("=" * 80)
            logger.info("│" + " " * 30 + f"Iteration {iteration+2:2d}/{iterations:2d} ..." + " " * 29 + "│")
            logger.info("=" * 80)

            # Generate patch
            logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration {iteration+2:2d}/{iterations} >>>> Generating patch ...")
            messages = format_feedback_query(messages, response, error_status, error_message)
            patch_info_list = repair_tool.generate_patch(1, messages)
            # Validate patch
            logger.info(f">>>> Attempt {attempt+1:2d}/{attempts} >>>> Iteration {iteration+2:2d}/{iterations} >>>> Validating patch ...")
            
            non_compilable, compilable, plausible, timeout, generation_error = dataset.validate_and_store(data_id, patch_info_list, experiment_name, time_limit)
            if plausible == 1:
                logger.info(f"Early stop at attempt {attempt+1}/{attempts} and iteration {iteration+2}/{iterations}")
                last_attempt = attempt + 1
                last_iteration = iteration + 2
                return
            elif non_compilable == 1:
                error_status = "[CE]"
                error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
            elif compilable == 1:
                error_status = "[FE]"
                error_message = "\n".join(f"Error {i + 1}: {msg}" for i, msg in enumerate(read_json_file(os.path.join(output_attempt_dir, f'{experiment_name}.json'))["error_message"]))
            elif timeout == 1:
                error_status = "[Timeout]"
                error_message = ""
            elif generation_error == 1:
                error_status = "[ResponseError]"
                error_message = ""
    
    logger.info("=" * 80)
    if last_attempt == attempts and last_iteration == iterations:
        logger.info(f"There is no plausible patch after {attempts} attempts and {iterations} iterations")
    else:
        logger.info(f"Early stop at attempt {last_attempt}/{attempts} and iteration {last_iteration}/{iterations}")