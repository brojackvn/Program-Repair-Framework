import os
import json
import tree_sitter
import tree_sitter_java as tsjava
import re
import difflib

# =============================================================================
# Json Utilities
# =============================================================================
def write_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def read_buggy_code(bug_id):
    with open(REGMINER4APR_BUG_JSON, 'r') as f:
        bug_data = json.load(f)
    
    for bug in bug_data:
        if int(bug.split("_", 1)[0]) == bug_id:
            return bug_data[bug]["context"]

# ============================================================================
# Extract the attempt and iteration number
# ============================================================================
def read_attempt_and_iteration(experiment_output_dir, dataset, setting, model):
    """
    This function only support the conversational APR setting.
    Returns a list of tuples, where each tuple containes the bug_id, #attempt, and #iteration.
    """
    plausible_list = []
    non_plausible_list = []

    patch_folder = os.path.join(experiment_output_dir, setting, dataset, model)
    bug_id_list = os.listdir(patch_folder)

    for bug_id in bug_id_list:
        bug_id_path = os.path.join(patch_folder, bug_id)
        if not os.path.isdir(bug_id_path):
            continue
        
        # Get the attempt folders for the current bug_id
        attempt_folders = [f for f in os.listdir(bug_id_path) if f.startswith("attempt-")]
        sorted_attempts = sorted(attempt_folders, key=lambda x: int(x.split("-")[1]))
        last_attempt_count = int(sorted_attempts[-1].split("-")[1])
        # print(f"Bug ID: {bug_id}, Last Attempt: {last_attempt_count}")
        
        last_attempt_path = os.path.join(bug_id_path, sorted_attempts[-1])
        json_files = [f for f in os.listdir(last_attempt_path) if f.endswith(".json")]
        for json_file in json_files:
            if not json_file[0].isdigit():
                file_path = os.path.join(last_attempt_path, json_files[0])
                with open(file_path, 'r') as f:
                    responses = json.load(f)
                    iteration = 0
                    plausible_found = False
                    for response in responses:
                        iteration += 1
                        if response['status'] == "[Plausible]":
                            plausible_list.append((bug_id, last_attempt_count, iteration))
                            plausible_found = True
                    if plausible_found == False:
                        non_plausible_list.append((bug_id, last_attempt_count, iteration))

    return plausible_list, non_plausible_list

def read_attempt(file_path):
    """
    This function only support the prompt APR setting, which has the following file structure:
    """
    pass

def summary_attempt_and_iteration(setting, model):
    """
    This is the summary of Java and Python APR experiments.
    """
    # Java experiment summary

    if model == "gpt-4o":
        if setting == "conversational-apr-bic":
            java_correct_patch_list = ["3", "4", "5", "21", "22", "30", "40", "43", "48", "56", "62", "65", "69", "70", "78", "84", "85", "99", "100", "102", "108", "114", "117", "126", "136", "137", "139", "146", "147"]
            python_correct_patch_list = ["4", "6", "9", "19", "20", "24", "28", "30", "35", "37"]
            java_experiment_output_dir = os.path.join("/external_disk/coding_space/ChatRepairRegression/experiments/output/regminer4apr-output")
            java_dataset = "regminer4apr"
            python_experiment_output_dir = os.path.join("/external_disk/coding_space/ChatRepairRegression/experiments/output/pyregression-output")
            python_dataset = "pyregression"
        else:
            print("This setting has not been implemented for the Java APR setting.")
            return
    else:
        print("This function has not been implemented for the Java APR setting.")
        return

    print("=" * 100)
    print(f"Setting: {setting}, Model: {model}")
    print("=" * 100)
    if "conversational-apr" in setting:
        print("=" * 100)

        print("JAVA EXPERIMENT SUMMARY")
        print("=" * 100)
        java_plausible_list, non_java_plausible_list = read_attempt_and_iteration(java_experiment_output_dir, java_dataset, setting, model)
        print(f"Total number of plausible patches: {len(java_plausible_list)}")
        print(f"Total number of non-plausible patches: {len(non_java_plausible_list)}")
        print(f"Total number of Java correct patches: {len(java_correct_patch_list)}")
        
        print("-" * 50)
        print(f"Non-plausible patches: {len(non_java_plausible_list)}")
        print(f"List of non-plausible patches: {non_java_plausible_list}")
        print("-" * 50)

        print(f"Plausible (but incorrect) patches with x attempts and 0 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and item[2] == 1])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and item[2] == 1]}")
        print(f"    + 5 <= x <= 10: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and item[2] == 1])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and item[2] == 1]}")
        print("-" * 50)
        
        print(f"Plausible (but incorrect) patches with x attempts and 2 <= y <= 3 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and 2 <= item[2] <= 3])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and 2 <= item[2] <= 3]}")
        print(f"    + 5 <= x <= 10: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and 2 <= item[2] <= 3])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and 2 <= item[2] <= 3]}")
        print("-" * 50)

        print(f"Plausible (but incorrect) patches with x attempts and 4 <= y <= 5 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and 4 <= item[2] <= 5])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] < 5 and 4 <= item[2] <= 5]}")
        print(f"    + 5 <= x <= 10: {len([item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and 4 <= item[2] <= 5])}")
        print(f"    List of these patches: {[item for item in java_plausible_list if item[0] not in java_correct_patch_list and item[1] >= 5 and 4 <= item[2] <= 5]}")
        print("=" * 100)

        print("PYTHON EXPERIMENT SUMMARY")
        print("=" * 100)
        python_plausible_list, non_python_plausible_list = read_attempt_and_iteration(python_experiment_output_dir, python_dataset, setting, model)
        print(f"Total number of plausible patches: {len(python_plausible_list)}")
        # print(f"List of plausible patches: {sorted(python_plausible_list, key=lambda x: int(x[0]))}")
        print(f"Total number of non-plausible patches: {len(non_python_plausible_list)}")
        print(f"Total number of Python correct patches: {len(python_correct_patch_list)}")

        print("-" * 50)
        print(f"Non-plausible patches: {len(non_python_plausible_list)}")
        print(f"List of non-plausible patches: {non_python_plausible_list}")
        print("-" * 50)

        print(f"Plausible (but incorrect) patches with x attempts and 0 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and item[2] == 1])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and item[2] == 1]}")
        print(f"    + 5 <= x <= 10: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and item[2] == 1])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and item[2] == 1]}")
        print("-" * 50)

        print(f"Plausible (but incorrect) patches with x attempts and 2 <= y <= 3 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and 2 <= item[2] <= 3])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and 2 <= item[2] <= 3]}")
        print(f"    + 5 <= x <= 10: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and 2 <= item[2] <= 3])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and 2 <= item[2] <= 3]}")
        print("-" * 50)
        
        print(f"Plausible (but incorrect) patches with x attempts and 4 <= y <= 5 iterations:")
        print(f"    + 1 <= x < 5: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and 4 <= item[2] <= 5])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] < 5 and 4 <= item[2] <= 5]}")
        print(f"    + 5 <= x <= 10: {len([item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and 4 <= item[2] <= 5])}")
        print(f"    List of these patches: {[item for item in python_plausible_list if item[0] not in python_correct_patch_list and item[1] >= 5 and 4 <= item[2] <= 5]}")
        print("=" * 100)
    else:
        print("This function has not been implemented for the prompt APR setting.")
        return

    

# ============================================================================
# Patch Extraction Utilities
# ============================================================================
def read_plausible_patch(file):
    no_plausible_patch = True
    responses = json.load(open(file, 'r'))
    count = 0
    for response in responses:
        count += 1
        # print(response['status'])
        # print(response)
        if response['status'] == "[Plausible]":
            no_plausible_patch = False
            return response["patch"], response["response"]
        if count == 10:
            break
    if no_plausible_patch:
        return None, None

def read_conversational_apr(setting, model, bug_id):
    patch_folder = os.path.join(EXPERIMENT_OUTPUT_DIR, setting, DATASET, model, str(bug_id))

    if not os.path.exists(patch_folder):
        print("No fixing for bug_id: ", bug_id)
        return None, None

    for attempt_folder in os.listdir(patch_folder):
        attempt_id = int(attempt_folder.split("-")[1])
        if attempt_id > 10:
            continue
        attempt_path = os.path.join(patch_folder, attempt_folder)
        json_files = [f for f in os.listdir(attempt_path) if f.endswith(".json")]
        for json_file in json_files:
            if not json_file[0].isdigit():
                file_path = os.path.join(attempt_path, json_files[0])
                plausible, response = read_plausible_patch(file_path)
                if plausible is not None:
                    print(bug_id)
                    return plausible, response
                
    print("No plausible patch found for bug_id: ", bug_id)
    return None, None

def read_prompt_apr(setting, model, bug_id):
    patch_folder = os.path.join(EXPERIMENT_OUTPUT_DIR, setting, DATASET, model, str(bug_id))

    if not os.path.exists(patch_folder):
        print("No fixing for bug_id: ", bug_id)
        return None, None
    
    json_files = [f for f in os.listdir(patch_folder) if f.endswith(".json")]
    print(json_files)
    for json_file in json_files:
        if not json_file[0].isdigit():
            file_path = os.path.join(patch_folder, json_file)
            print(file_path)
            plausible, response = read_plausible_patch(file_path)
            if plausible is not None:
                print(bug_id)
                return plausible, response

    print("No plausible patch found for bug_id: ", bug_id)
    return None, None

def write_patches(setting, model):
    file = os.path.join(PATCH_STORAGE_DIR, f"{setting}_{model}.json")

    patches = {}

    if "conversational-apr" in setting:
        for bug_id in range(1, 151):
            plausible, response = read_conversational_apr(setting, model, bug_id)
            if plausible is not None:
                patches[str(bug_id)] = {
                    "patched_method": plausible,
                    "diff": "",
                    "response": response
                }
    else:
        for bug_id in range(1, 151):
            plausible_patch, response = read_prompt_apr(setting, model, bug_id)
            if plausible_patch is not None:
                patches[str(bug_id)] = {
                    "patched_method": plausible_patch,
                    "diff": "",
                    "response": response
                } 

    write_json_file(file, patches)
    print(f"File {file} written with {len(patches)} patches.")

# ============================================================================
# Extract the cost of patch generation
# ============================================================================
def read_file(file):
    responses = json.load(open(file, 'r'))

    input_token_total = 0
    output_token_total = 0
    count = 0

    for response in responses:
        count += 1
        input_token_total += response["input_tokens"]
        output_token_total += response["output_tokens"]

        if count == 10:
            break
    
    return input_token_total, output_token_total

def read_prompt_cost(setting, model, bug_id):
    """
    Reads the prompt cost from a JSON file and returns the input tokens, output tokens, and total cost.
    Returns:
        - input_tokens: Number of input tokens
        - output_tokens: Number of output tokens
    """

    patch_folder = os.path.join(EXPERIMENT_OUTPUT_DIR, setting, DATASET, model, str(bug_id))

    if not os.path.exists(patch_folder):
        return None, None
    
    json_files = [f for f in os.listdir(patch_folder) if f.endswith(".json")]
    print(len(json_files))

    for json_file in json_files:
        if not json_file[0].isdigit():
            file_path = os.path.join(patch_folder, json_file)
            print(file_path)
            input_tokens, output_tokens = read_file(file_path)
            return input_tokens, output_tokens
    
    print(f"No JSON files found in {patch_folder}")
    return None, None

def read_conversational_cost(setting, model, bug_id):
    """
    Reads the conversational cost from a JSON file and returns the input tokens, output tokens, and total cost.
    Returns:
        - input_tokens: Number of input tokens
        - output_tokens: Number of output tokens
    """
    patch_folder = os.path.join(EXPERIMENT_OUTPUT_DIR, setting, DATASET, model, str(bug_id))

    if not os.path.exists(patch_folder):
        print("No fixing for bug_id: ", bug_id)
        return None, None
    
    input_tokens = 0
    output_tokens = 0

    for attempt_folder in os.listdir(patch_folder):
        attempt_id = int(attempt_folder.split("-")[1])
        if attempt_id > 10:
            continue

        attempt_path = os.path.join(patch_folder, attempt_folder)
        json_files = [f for f in os.listdir(attempt_path) if f.endswith(".json")]
        for json_file in json_files:
            if not json_file[0].isdigit():
                file_path = os.path.join(attempt_path, json_file)
                print(file_path)
                input_token_per_file, output_token_per_file = read_file(file_path)
                input_tokens += input_token_per_file
                output_tokens += output_token_per_file
    
    if input_tokens == 0 and output_tokens == 0:
        print(f"No JSON files found in {patch_folder}")
        return None, None
    return input_tokens, output_tokens

# ============================================================================
# Tree-sitter Utilities
# ============================================================================
def get_ast(code):
    """Parses a given Java code snippet and returns the AST using Tree-sitter."""
    JAVA_LANGUAGE = tree_sitter.Language(tsjava.language())
    parser = tree_sitter.Parser(JAVA_LANGUAGE)
    return parser.parse(code.encode('utf-8'))

def cleanup_comments(java_code):
    tree = get_ast(java_code)
    root_node = tree.root_node

    # Find all comment nodes
    comments = []
    def traverse(node):
        if node.type in {"line_comment", "block_comment"}:
            comments.append((node.start_byte, node.end_byte))
        for child in node.children:
            traverse(child)

    traverse(root_node)

    # Remove comments from the code
    cleaned_code = []
    last_index = 0
    for start, end in sorted(comments):
        cleaned_code.append(java_code[last_index:start])
        last_index = end
    cleaned_code.append(java_code[last_index:])

    return re.sub(r"\n\s*\n", "\n", "".join(cleaned_code).strip())
    # return "".join(cleaned_code).strip()

def get_code_diff(buggy_code, patched_code):
    # Create a generator of diff lines
    diff = difflib.unified_diff(
        buggy_code.splitlines(keepends=True),
        patched_code.splitlines(keepends=True),
        n=0
    )
    print("".join(diff))

# =============================================================================
# Testing
# =============================================================================
def test_cleanup_comments():
    # Example usage
    java_code = '''
    @Override
    public synchronized int available() throws IOException {
        // Check if the buffer is initialized and not null
        if (byteBuffer == null) {
            return 0;
        }
        
        // Return the number of bytes remaining in the buffer
        return byteBuffer.remaining();
    }
    '''
    print(cleanup_comments(java_code))

def test_read_buggy_code():
    print(read_buggy_code(100))

# =============================================================================
# Constants
# =============================================================================
EXPERIMENT_OUTPUT_DIR = "/external_disk/coding_space/ChatRepairRegression/experiments/output/regminer4apr-output"
REGMINER4APR_BUG_JSON = "/external_disk/coding_space/ChatRepairRegression/experiments/regminer4apr-bug-metadata.json"
DATASET = "regminer4apr"
PATCH_STORAGE_DIR = "/external_disk/coding_space/ChatRepairRegression/experiments/patches/regminer4apr-patches"

# =============================================================================
# Main Function
# =============================================================================
def main():
    # ====================================
    # test_cleanup_comments()
    # ====================================

    # ====================================
    # test_read_buggy_code()
    # ====================================

    # ====================================
    summary_attempt_and_iteration("conversational-apr-bic", "gpt-4o")
    # ====================================

    # ====================================
    # Read patches and write to file
    # ====================================
    setting = ["prompt-apr", "prompt-apr-bic", "conversational-apr", "conversational-apr-bic", "conversational-apr-cc", "conversational-apr-cm"]
    model   = ["gpt-3.5-turbo", "gpt-4o"]
    bug_id  = int()

    write_patches("conversational-apr-bic", "gpt-4o")

# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()