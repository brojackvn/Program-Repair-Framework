import tree_sitter
import tree_sitter_java as tsjava

def get_ast(code):
    """Parses a given Java code snippet and returns the AST using Tree-sitter."""
    JAVA_LANGUAGE = tree_sitter.Language(tsjava.language())
    parser = tree_sitter.Parser(JAVA_LANGUAGE)
    return parser.parse(code.encode('utf-8'))

def is_java_function(code):
    """Detects whether a given Java snippet is a function using Tree-sitter."""
    tree = get_ast(code)
    root_node = tree.root_node

    # Traverse the AST to find method_declaration nodes
    for node in root_node.children:
        if node.type == "method_declaration":
            return True  # Function found

    return False  # No function found

def extract_imports_and_methods(code):
    '''
    Extract import statements and method declarations from code snippet
    '''
    tree = get_ast(code)
    root_node = tree.root_node

    imports, methods = [], []

    for child in root_node.children:
        if child.type == "import_declaration":
            imports.append(code[child.start_byte:child.end_byte])
        elif child.type == "method_declaration":
            methods.append(code[child.start_byte:child.end_byte])
    
    return imports, methods

def add_import_statement(code, imports):
    '''
    Add import statements to a Java file
    '''
    tree = get_ast(code)
    root_node = tree.root_node

    # Find last import statement position
    last_import_end = 0
    package_end = 0
    for child in root_node.children:
        if child.type == "package_declaration":
            package_end = child.end_byte  # Position after the package declaration
        elif child.type == "import_declaration":
            last_import_end = child.end_byte  # Update position to last import

    # Determine insertion point
    insert_position = last_import_end if last_import_end > 0 else package_end

    # Join imports as a string with newline characters
    import_statements = "\n".join(imports) + "\n"  # Ensure each import is on a new line

    # Count the number of lines added
    added_lines_count = import_statements.count("\n") + 1 # one "\n" added means one more line added

    modified_code = code[:insert_position] + "\n" + import_statements + code[insert_position:]

    return modified_code, added_lines_count

def find_method_end_line(node, start_line):
    """
    Given an AST node and a starting line number, find the end line of the method.

    :param node: tree_sitter.Node (AST root or subtree)
    :param start_line: int (1-based index)
    :return: int (end_line) or None if not found
    """
    if node is None:
        return None

    # Check if the node is a method declaration
    if node.type == "method_declaration":
        if abs(node.start_point[0] + 1 - start_line) <= 2:  # Convert to 1-based index
            return node.end_point[0] + 2  # Convert to 1-based index

    # Recursively search in child nodes
    for child in node.children:
        result = find_method_end_line(child, start_line)
        if result:
            return result

    return None  # Return None if no matching method is found

def get_method_end_line(code, start_line):
    """Wrapper function to get the end line of a method."""
    ast = get_ast(code)
    return find_method_end_line(ast.root_node, start_line)