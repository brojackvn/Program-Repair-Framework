from src.benchmark.AbstractBenchmark import AbstractBenchmark
from src.utils.logger import logger
from src.utils.json_utils import write_json_file
import subprocess
import shutil
import os
import json
import re
import time

def extract_compilation_errors(log: str, max_length: int = 1000):
    """
    Extract compilation errors from the log and return a list of error messages.
    """
    split_logs = log.split("================================================================================")
    return split_logs[-1][:max_length]

def extract_test_results(log: str, max_length: int = 700, max_cases: int = 10):
    """
    Extract test results from the log and return a list of test case results.
    Return:
        - List of test results
    """
    split_logs = log.split("--------------------------------------------------------------------------------")
    test_results = split_logs[1:-1]

    results = set()

    for result in test_results:
        match = re.search(r"-\s*Test:\s*(.+?)\n-\s*Type:\s*(.+?)\n-\s*Message:\s*(.*)", result.strip(), re.DOTALL)
        if match:
            test_name = match.group(1).strip()
            error_type = match.group(2).strip()
            error_message = match.group(3).strip()
            if len(results) < max_cases:
                results.add(f"- Test: {test_name} - Type: {error_type} - Message: {error_message[:max_length]}")

    return list(results)

class PyRegression(AbstractBenchmark):
    def __init__(self, input_path, mapping_path, environment_dir):
        self.environment_dir = environment_dir
        self.mapping = self.load_mappings(mapping_path)
        self.info = self.load_info(input_path)

    def load_info(self, input_path):
        '''
        Load the information of the nbemchmark

        Return:
            - info: {
                "data_id": {
                    "bug_id": str,
                    "src_dir": str,
                    "buggy_relative_path": str,
                    "buggy_file": str,
                    "buggy_loc": List[int],
                    "method_loc": List[int]
                }
            }
        '''
        dataset = json.load(open(input_path, 'r'))
        info = {}
        for id in dataset:
            data_id = id.split("_", 1)[0] # e,g. 1,2,3,...
            bug_id = self.mapping[data_id] # e.g., RegressionBug_1,...
            buggy_relative_path = id.split("_", 1)[1]
            src_dir = os.path.join(self.environment_dir, self._get_project(data_id))
            buggy_file = os.path.join(src_dir, buggy_relative_path)
            method_loc = (int(dataset[id]['method_start_line']), int(dataset[id]['method_end_line']))
            buggy_function = dataset[id]['context']
            before_buggy = dataset[id]['before']
            buggy_lines = dataset[id]['buggy_lines']
            after_buggy = dataset[id]['after']

            buggy_loc = None
            if 'start_line' in dataset[id] and 'end_line' in dataset[id]:
                buggy_loc = (int(dataset[id]['start_line']), int(dataset[id]['end_line']))

            bug_inducing_changes = None
            if 'bug_inducing_changes' in dataset[id]:
                bug_inducing_changes = dataset[id]['bug_inducing_changes']
            
            bic_commit_message = None
            if 'bic_commit_message' in dataset[id]:
                bic_commit_message = dataset[id]['bic_commit_message']
            
            changed_files = None
            if 'changed_files' in dataset[id]:
                changed_files = dataset[id]['changed_files']

            info[data_id] = {
                'bug_id': bug_id,
                'src_dir': src_dir, # environment directory + Bug ID + BUGGY
                'buggy_relative_path': buggy_relative_path,
                'buggy_file': buggy_file, # src_dir + buggy_relative_path
                'buggy_function': buggy_function,
                'before_buggy': before_buggy,
                'buggy_lines': buggy_lines,
                'after_buggy': after_buggy,
                'buggy_loc': buggy_loc,
                'method_loc': method_loc,
                'bug_inducing_changes': bug_inducing_changes,
                'bic_commit_message': bic_commit_message,
                'changed_files': changed_files
            }
        return info

    def load_single_info(self, data_id): 
        if data_id not in self.info:
            logger.error("Cannot find data ID: {}".format(data_id))
              
        if not os.path.exists(os.path.join(self.environment_dir)):
            logger.error("Environment directory does not exist: {}. Please run `pyregression setup -w {}` to initialize it.".format(self.environment_dir, self.environment_dir))
            return None
        else:
            cmd = "pyregression checkout" + " -v " + "buggy" + " -r " + data_id
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if result.returncode != 0:
                logger.error("Failed to checkout the benchmark!")
                return None
            else:
                logger.info("Successfully checkout the benchmark!")
        return self.info[data_id]

    def _get_project(self, data_id):
        pandas_ids = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 21, 22]
        django_ids = [15, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 43, 44, 45, 46, 48, 49, 50]
        if int(data_id) in pandas_ids:
            return "pandas"
        elif int(data_id) in django_ids:
            return "django"
        else:
            logger.error("Cannot find the project for data ID: {}".format(data_id))
            return None

    def load_mappings(self, mapping_path):
        mappings = {}
        with open(mapping_path, "r") as f:
            for line in f:
                data_id = line.split()[0]
                data_id = data_id.replace("_", "-")
                mappings[data_id] = line.split()[1].strip()
        return mappings

    def setup_validation_dir(self, data_id):
        logger.info("Setting up validation directory...")
        
        return os.path.join(self.environment_dir, self._get_project(data_id))


    def clear_validation_dir(self, data_id):
        cmd = "pyregression checkout" + " -v " + "buggy" + " -r " + data_id
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if result.returncode != 0:
            logger.error("Failed to clear the validation directory!\n")
        else:
            logger.info("Successfully clear the validation directory!\n")

    def execute(self, validation_dir):
        '''
        Execute the program and return the result

        Return:
            - status: [CE]. [FE], [Plausible], [Timeout]
            - ErrorMessage: str || None (if status is [Timeout] || [Plausible])
        '''
        running_result = {
            "status": None,
            "error_message": None
        }

        cmd = "pyregression test -w " + validation_dir
        try:
            command_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=720)
            result_message = command_result.stdout.decode('utf-8')
            logger.debug(command_result.stdout.decode('utf-8'))

            if command_result.returncode == 0:
                running_result["status"] = "[Plausible]"
                running_result["error_message"] = None
            elif command_result.returncode == 1:
                running_result["status"] = "[FE]"
                running_result["error_message"] = extract_test_results(result_message)
            elif command_result.returncode == 2:
                running_result["status"] = "[CE]"
                running_result["error_message"] = extract_compilation_errors(result_message)
        except subprocess.TimeoutExpired:
            running_result["status"] = "[Timeout]"
            running_result["error_message"] = None
        
        return running_result

    def validate(self, data_id, patch_info, time_limit=720):
        '''
        Validate the patches and return the results

        Return: Save the results in the output_dir as validated_patches.json
        {
            {
                "id": patch_id,
                "status": [CE] || [FE] || [Plausible],
                "error_message": str,
                "time": float
            }
        }
        '''
        bug_info = self.load_single_info(data_id)
        bug_id, src_dir, buggy_relative_path, buggy_file, buggy_loc, method_loc = bug_info["bug_id"], bug_info["src_dir"], bug_info["buggy_relative_path"], bug_info["buggy_file"], bug_info["buggy_loc"], bug_info["method_loc"]
        
        plausible = 0
        compilable = 0
        non_compilable = 0
        timeout = 0
        generation_error = 0
        
        # Setup the validation directory
        validation_dir = self.setup_validation_dir(data_id)
        start_time = time.time()

        def apply_patch(validation_dir, buggy_relative_path, patch, method_loc):
            '''
            Apply the patch to the buggy file

            Args:
                - validation_dir: str
                - buggy_relative_path: str
                - patch: str
                - method_loc: (start, end)
            Return:
                - patched_method: str
                - (new_start_method_loc, new_end_method_loc): (int, int)                
            '''
            # print(patch)

            # Initialize the patched file
            patched_file = ''
            # Initialize the patched method
            patched_method = str()

            # Read the buggy file
            buggy_file = os.path.join(validation_dir, buggy_relative_path)
            with open(buggy_file, "r") as f:
                lines = f.readlines()

            # Convert 1-based index to 0-based index
            start_method_loc = method_loc[0] - 1
            end_method_loc   = method_loc[1] - 1

            # Apply the patch to the buggy file
            for index in range(len(lines)):
                if index < start_method_loc or index > end_method_loc - 1:
                    patched_file += lines[index]
                elif index == start_method_loc:
                    patched_file += patch + "\n"
            
            # Write the patched file to the buggy file
            with open(buggy_file, "w") as f:
                f.write(patched_file)

            # Retrive the method location
            new_start_method_loc, new_end_method_loc = start_method_loc + 1, start_method_loc + len(patch.splitlines()) + 1
            
            # print("New method location: ", new_start_method_loc, new_end_method_loc)
            # breakpoint()

            return patched_method, (new_start_method_loc, new_end_method_loc)

        patched_method, patched_method_loc = apply_patch(validation_dir, buggy_relative_path, patch_info['patch'], method_loc)
        
        # If the response does not contain the patched method, meaning the patch is not generated
        if patched_method is None:
            generation_error += 1
            self.clear_validation_dir(data_id)
            return {
                "patch": None,
                "patched_method_loc": None,
                "status": "[ResponseError]",
                "error_message": None,
                "validation_time": None,
                "result": {
                    "non_compilable": non_compilable, 
                    "compilable": compilable, 
                    "plausible": plausible, 
                    "timeout": timeout, 
                    "generation_error": generation_error
                }
            }

        # Execute the program
        executionResult = self.execute(validation_dir)
        
        # Evaluate the results
        if executionResult["status"] == "[Plausible]":
            plausible += 1
        elif executionResult["status"] == "[FE]":
            compilable += 1
        elif executionResult["status"] == "[CE]":
            non_compilable += 1
        elif executionResult["status"] == "[Timeout]":
            timeout += 1
        
        self.clear_validation_dir(data_id)

        # Save the results
        return {
            "patch": patch_info['patch'],
            "patched_method_loc": patched_method_loc,
            "status": executionResult["status"],
            "error_message": executionResult["error_message"],
            "validation_time": time.time() - start_time,
            "result": {
                    "non_compilable": non_compilable, 
                    "compilable": compilable, 
                    "plausible": plausible, 
                    "timeout": timeout, 
                    "generation_error": generation_error
                }
        }
