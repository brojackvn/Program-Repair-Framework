from src.benchmark.AbstractBenchmark import AbstractBenchmark
from src.utils.logger import logger
from src.utils.tree_sitter_utils import is_java_function, extract_imports_and_methods, add_import_statement, get_method_end_line
from src.utils.json_utils import write_json_file
import subprocess
import shutil
import os
import json
import re
import time

def extract_compilation_error(log: str) -> str:
    '''
    Extract the compilation error from the log

    Return:
        - List of error messages
    '''
    # Round 1: Extract the compilation error
    pattern = r"\[ERROR\] COMPILATION ERROR : \n\[INFO\] -------------------------------------------------------------\n"
    split_log = re.split(pattern, log)
    if len(split_log) > 1:
        log = split_log[1]
    else:
        return ""
    
    # Round 2: Extract the error message
    pattern = r"\[INFO\] \d+ errors?"
    log = re.split(pattern, log)[0]

    # Round 3: Extract the more detailed error message
    results = []
    result = log.strip().split("[ERROR]")
    for res in result[1:]:
        if "cannot find symbol" in res:
            start_index = res.find(":[")
            end_index = res.find("location:")
            results.append(res[start_index+1:end_index].strip())
        else:
            start_index = res.find(":[")
            results.append(res[start_index+1:].strip())
    
    return results

def extract_test_results(message, max_message_length=1000, max_test_cases=10):
    '''
    Extract the test results from the message

    Return:
        - List of test results
    '''
    # Define the regex pattern to extract the summary line
    pattern = r"Test:\s(.+?)\nType:\s(.+?)\nMessage:\s(.+?)\n"
    # Use re.findall to extract all matches
    test_cases = re.findall(pattern, message)

    results = set()
    for test_case in test_cases:
        if len(results) <= max_test_cases:
            if len(test_case[2]) <= max_message_length:
                results.add(test_case[0] + ": " + test_case[1] + ": " + test_case[2])
            else:
                results.add(test_case[0] + ": " + test_case[1])
    return list(results)

class RegMiner4APR(AbstractBenchmark):
    def __init__(self, input_path, mapping_path, enviroment_dir, tmp_dir, output_dir):
        self.enviroment_dir = enviroment_dir
        self.tmp_dir = tmp_dir
        self.output_dir = output_dir
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
            data_id = id.split("_")[0] # e,g. 1,2,3,...
            bug_id = self.mapping[data_id] # e.g., RegressionBug_1,...
            buggy_relative_path = id.split("_")[1]
            src_dir = os.path.join(self.enviroment_dir, bug_id, "BUGGY")
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
                'bic_commit_message': bic_commit_message
            }
        return info

    def load_single_info(self, data_id):
        '''
        Load the information of a single data ID

        Return:
            {
                "bug_id": str,
                "src_dir": str,
                "buggy_relative_path": str,
                "buggy_file": str,
                "buggy_loc": List[int],
                "method_loc": List[int]
            }
        '''
        if data_id not in self.info:
            logger.error("Cannot find data ID: {}".format(data_id))
              
        bug_id = self.mapping[data_id] # data_id = 1, 2, ... ==> bug_id = RegressionBug_1, RegressionBug_2, ...
        if not os.path.exists(os.path.join(self.enviroment_dir, bug_id)):
            cmd = "regminer4apr checkout" + " -rb " + data_id + " -w " + self.enviroment_dir
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if result.returncode != 0:
                logger.error("Failed to checkout the benchmark!")
                return None
            else:
                logger.info("Successfully checkout the benchmark!")
        return self.info[data_id]
    
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

        environment_dir = os.path.join(self.enviroment_dir, self.mapping[data_id], "BUGGY")
        validation_dir = os.path.join(self.tmp_dir, self.mapping[data_id], "BUGGY")
        
        if os.path.exists(validation_dir):
            subprocess.run('rm -rf ' + validation_dir, shell=True)
        shutil.copytree(environment_dir, validation_dir)
        
        logger.info("Validation directory is created successfully!")
        return validation_dir
    
    def clear_validation_dir(self, data_id):
        validation_dir = os.path.join(self.tmp_dir, self.mapping[data_id])
        if os.path.exists(validation_dir):
            subprocess.run('rm -rf ' + validation_dir, shell=True)

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
        
        compile_error_flag = True

        # Get compile result
        cmd = "cd " + validation_dir + ";"
        cmd += 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 && export PATH=$JAVA_HOME/bin:$PATH && regminer4apr compile' # Compile the program

        command_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        result_message = command_result.stdout.decode('utf-8')
        logger.debug(command_result.stdout.decode('utf-8'))

        # Evaluate the compile result
        if command_result.returncode == 1:
            running_result["status"] = "[CE]"
            running_result["error_message"] = extract_compilation_error(result_message)
        elif 'Successfully compiled test' in result_message:
            compile_error_flag = False

        # Evaluate the plausible patches
        if not compile_error_flag:
            # Running the test cases
            cmd = "cd " + validation_dir + ";"
            cmd += 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 && export PATH=$JAVA_HOME/bin:$PATH && timeout 720 regminer4apr test' # Test the program
            command_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            result_message = command_result.stdout.decode('utf-8')
            logger.debug(command_result.stdout.decode('utf-8'))

            if command_result.returncode == 0 and '- Failed test cases: 0' in result_message:
                running_result["status"] = "[Plausible]"
                running_result["error_message"] = None
            elif command_result.returncode == 1:
                running_result["status"] = "[FE]"
                running_result["error_message"] = extract_test_results(result_message)
            else:
                running_result["status"] = "[Timeout]"
                running_result["error_message"] = None
        return running_result
    
    def validate(self, data_id, patches, output_file_name, time_limit=1800):
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
        # Extract the bug information
        bug_info = self.load_single_info(data_id)
        bug_id, src_dir, buggy_relative_path, buggy_file, buggy_loc, method_loc = bug_info["bug_id"], bug_info["src_dir"], bug_info["buggy_relative_path"], bug_info["buggy_file"], bug_info["buggy_loc"], bug_info["method_loc"]
        # Setup the output directory
        validated_patch_file = os.path.join(self.output_dir, f'{output_file_name}.json')
        os.makedirs(os.path.dirname(validated_patch_file), exist_ok=True)
        
        plausible = 0
        compliable = 0
        non_compliable = 0
        timeout = 0
        generation_error = 0
        # Iterate over the patches
        for rank, patch in enumerate(patches):
            # Setup the validation directory
            validation_dir = self.setup_validation_dir(data_id)
            start_time = time.time()

            # Apply the patched method only
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
                
                # Split the patch into method and its imports
                imports, methods = extract_imports_and_methods(patch)
                if len(methods) == 0:
                    logger.warning("Cannot find the patched method!")
                    return None, None
                patched_method = methods[0]

                # Apply the patch to the buggy file
                for index in range(len(lines)):
                    if index < start_method_loc or index > end_method_loc - 1:
                        patched_file += lines[index]
                    elif index == start_method_loc:
                        patched_file += patched_method + "\n"
                
                # Add the imports to the patched file, if any
                added_lines_count = 0
                if len(imports) > 0:
                    patched_file, added_lines_count = add_import_statement(patched_file, imports)

                # Write the patched file to the buggy file
                with open(buggy_file, "w") as f:
                    f.write(patched_file)

                # Retrive the method location
                new_start_method_loc, new_end_method_loc = (start_method_loc + 1) + added_lines_count, get_method_end_line(patched_file, (start_method_loc + 1) + added_lines_count)
                
                return patched_method, (new_start_method_loc, new_end_method_loc)
            
            # If the response is None, meaning the patch is not generated
            if patch is None:
                logger.warning("Cannot generate the patch!")
                write_json_file(
                    {
                        "patch": None,
                        "patched_method_loc": None,
                        "status": "[ResponseError]",
                        "error_message": None,
                        "validation_time": None,
                    },
                    validated_patch_file
                )
                generation_error += 1
                self.clear_validation_dir(data_id)
                continue

            patched_method, patched_method_loc = apply_patch(validation_dir, buggy_relative_path, patch, method_loc)
            
            # If the response does not contain the patched method, meaning the patch is not generated
            if patched_method is None:
                generation_error += 1
                write_json_file(
                    {
                        "patch": None,
                        "patched_method_loc": None,
                        "status": "[ResponseError]",
                        "error_message": None,
                        "validation_time": None,
                    },
                    validated_patch_file
                )
                self.clear_validation_dir(data_id)
                continue

            # Execute the program
            executionResult = self.execute(validation_dir)
            
            # Save the results
            write_json_file(
                {
                    "patch": patched_method,
                    "patched_method_loc": patched_method_loc,
                    "status": executionResult["status"],
                    "error_message": executionResult["error_message"],
                    "validation_time": time.time() - start_time
                },
                validated_patch_file
            )
        
            # Evaluate the results
            if executionResult["status"] == "[Plausible]":
                plausible += 1
            elif executionResult["status"] == "[FE]":
                compliable += 1
            elif executionResult["status"] == "[CE]":
                non_compliable += 1
            elif executionResult["status"] == "[Timeout]":
                timeout += 1
            
            self.clear_validation_dir(data_id)

        return non_compliable, compliable, plausible, timeout, generation_error

    def validate_and_store(self, data_id, patch_info_list, output_file_name, time_limit=1800):
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
        # Extract the bug information
        bug_info = self.load_single_info(data_id)
        bug_id, src_dir, buggy_relative_path, buggy_file, buggy_loc, method_loc = bug_info["bug_id"], bug_info["src_dir"], bug_info["buggy_relative_path"], bug_info["buggy_file"], bug_info["buggy_loc"], bug_info["method_loc"]
        # Setup the output directory
        validated_patch_file = os.path.join(self.output_dir, f'{output_file_name}.json')
        os.makedirs(os.path.dirname(validated_patch_file), exist_ok=True)
        
        plausible = 0
        compliable = 0
        non_compliable = 0
        timeout = 0
        generation_error = 0
        # Iterate over the patches
        for rank, patch_info in enumerate(patch_info_list):
            # Setup the validation directory
            validation_dir = self.setup_validation_dir(data_id)
            start_time = time.time()

            # Apply the patched method only
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
                
                # Split the patch into method and its imports
                imports, methods = extract_imports_and_methods(patch)
                if len(methods) == 0:
                    logger.warning("Cannot find the patched method!")
                    return None, None
                patched_method = methods[0]

                # Apply the patch to the buggy file
                for index in range(len(lines)):
                    if index < start_method_loc or index > end_method_loc - 1:
                        patched_file += lines[index]
                    elif index == start_method_loc:
                        patched_file += patched_method + "\n"
                
                # Add the imports to the patched file, if any
                added_lines_count = 0
                if len(imports) > 0:
                    patched_file, added_lines_count = add_import_statement(patched_file, imports)

                # Write the patched file to the buggy file
                with open(buggy_file, "w") as f:
                    f.write(patched_file)

                # Retrive the method location
                new_start_method_loc, new_end_method_loc = (start_method_loc + 1) + added_lines_count, get_method_end_line(patched_file, (start_method_loc + 1) + added_lines_count)
                
                return patched_method, (new_start_method_loc, new_end_method_loc)
            
            # If the response is None, meaning API response is error
            if patch_info['patch'] is None:
                logger.warning("Cannot generate the patch!")
                generation_error += 1
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
                self.clear_validation_dir(data_id)
                continue
            
            patched_method, patched_method_loc = apply_patch(validation_dir, buggy_relative_path, patch_info['patch'], method_loc)
            
            # If the response does not contain the patched method, meaning the patch is not generated
            if patched_method is None:
                generation_error += 1
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
                self.clear_validation_dir(data_id)
                continue

            # Execute the program
            executionResult = self.execute(validation_dir)
            
            # Save the results
            write_json_file(
                {
                    "patch": patch_info['patch'],
                    "patched_method_loc": patched_method_loc,
                    "status": executionResult["status"],
                    "error_message": executionResult["error_message"],
                    "validation_time": time.time() - start_time,
                    "response": patch_info['response'],
                    "input_tokens": patch_info['input_tokens'],
                    "output_tokens": patch_info['output_tokens'],
                    "total_cost": patch_info['total_cost']
                },
                validated_patch_file
            )
        
            # Evaluate the results
            if executionResult["status"] == "[Plausible]":
                plausible += 1
            elif executionResult["status"] == "[FE]":
                compliable += 1
            elif executionResult["status"] == "[CE]":
                non_compliable += 1
            elif executionResult["status"] == "[Timeout]":
                timeout += 1
            
            self.clear_validation_dir(data_id)

        return non_compliable, compliable, plausible, timeout, generation_error