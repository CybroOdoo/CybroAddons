# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
import ast
import os
import re

results = []
module_technical_name = ['no_module']


def is_camel_case(name):
    """
    Check if a given name follows CamelCase format.

    Args:
        name (str): The variable or class name.

    Returns:
        bool: True if name is CamelCase.
    """
    return re.match(r'^[A-Z][a-zA-Z0-9]+$', name)

def is_snake_case(name):
    """
    Check if a given name follows snake_case format.

    Args:
        name (str): The variable or function name.

    Returns:
        bool: True if name is snake_case.
    """
    return re.match(r'^[a-z_][a-z0-9_]*$', name)

def check_class_name(node, file_path):
    """
    Validate that the class name follows CamelCase.

    Args:
        node (ast.ClassDef): The class node from AST.
        file_path (str): The source file path.
    """
    if not is_camel_case(node.name):
        file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Class name '{node.name}' is not CamelCase",
            "suggestion": "Use CamelCase (e.g., MyClassName)"
        })

def check_model_class(node, file_path):
    """
    Check Odoo model class rules, including naming consistency.

    Args:
        node (ast.ClassDef): The class node from AST.
        file_path (str): The source file path.
    """
    model_type = None
    model_name = None
    inherit_found = False
    name_found = False

    for base in node.bases:
        if isinstance(base, ast.Attribute) and base.attr in ["Model", "TransientModel"]:
            model_type = base.attr

    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    if target.id == "_name":
                        name_found = True
                        if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                            model_name = item.value.value
                    elif target.id == "_inherit":
                        inherit_found = True

    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"

    # Check if _name or _inherit is present
    if model_type and not (name_found or inherit_found):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Class '{node.name}' is missing both '_name' and '_inherit'",
            "suggestion": "Add either _name (for new model) or _inherit (for extending existing model)"
        })

    # Consistency Check
    filename = os.path.basename(file_path).replace(".py", "")
    expected_class_name = "".join(part.capitalize() for part in filename.split("_"))
    expected_model_name = filename.replace("_", ".")

    if node.name != expected_class_name:
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Class name '{node.name}' does not match file name '{filename}.py'",
            "suggestion": f"Rename class to '{expected_class_name}' to match file name"
        })

    if model_name and model_type == "Model":
        if model_name != expected_model_name:
            results.append({
                "file": file_path_shorten,
                "line": node.lineno,
                "issue": f"_name '{model_name}' does not match file-based model name '{expected_model_name}'",
                "suggestion": f"Use _name = '{expected_model_name}'"
            })

    if model_name:
        if "." not in model_name:
            results.append({
                "file": file_path_shorten,
                "line": node.lineno,
                "issue": f"Model name '{model_name}' should use dot notation",
                "suggestion": "Use format: <module>.<model> (e.g., res.partner)"
            })

        if model_type == "TransientModel" and "wizard" in model_name:
            results.append({
                "file": file_path_shorten,
                "line": node.lineno,
                "issue": f"Transient model name '{model_name}' contains 'wizard'",
                "suggestion": "Avoid using 'wizard'; use format: <related_model>.<action>"
            })

        if ".report." in model_name and len(model_name.split(".")) < 3:
            parts = model_name.split(".")
            if len(parts) < 3:
                results.append({
                    "file": file_path_shorten,
                    "line": node.lineno,
                    "issue": f"Report model name '{model_name}' should follow '<model>.report.<action>'",
                    "suggestion": "Ensure full dot-notation like 'sale.report.invoice'"
                })

        if model_type == "Model":
            last_part = model_name.split(".")[-1]
            if last_part.endswith("s"):
                results.append({
                    "file": file_path_shorten,
                    "line": node.lineno,
                    "issue": f"Model name '{model_name}' seems plural",
                    "suggestion": "Use singular form (e.g., 'res.partner', not 'res.partners')"
                })

def check_missing_docstring(node, file_path, type="function"):
    """
    Check whether a class or function has a docstring.

    Args:
        node (ast.AST): The node (ClassDef or FunctionDef).
        file_path (str): File path.
        type (str): Either 'function' or 'class'.
    """
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"
    if not ast.get_docstring(node):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"{type.capitalize()} '{node.name}' is missing a docstring",
            "suggestion": f"Add a docstring to the {type}"
        })

def check_function_name(node, file_path):
    """
    Check function or method names for snake_case and method type prefixes.

    Args:
        node (ast.FunctionDef): The function node.
        file_path (str): Path to the source file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"
    if not is_snake_case(node.name):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Function name '{node.name}' is not snake_case",
            "suggestion": "Use snake_case (e.g., my_function_name)"
        })

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute):
            if decorator.attr in ["multi", "one"]:
                results.append({
                    "file": file_path_shorten,
                    "line": node.lineno,
                    "issue": f"Decorator '@api.{decorator.attr}' is deprecated",
                    "suggestion": "Remove it; use '@api.model' or '@api.depends' based on logic"
                })
    check_method_prefix(node, file_path)

def check_method_prefix(node, file_path):
    """
    Check method prefix based on decorators like @api.depends, @api.onchange, etc.

    Args:
        node (ast.FunctionDef): The method definition.
        file_path (str): Path to the Python file.
    """
    method_prefix_map = {
        'depends': '_compute_',
        'onchange': '_onchange_',
        'constrains': '_check_',
    }
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            deco_name = decorator.func.attr
            expected_prefix = method_prefix_map.get(deco_name)
            if expected_prefix and not node.name.startswith(expected_prefix):
                results.append({
                    "file": file_path_shorten,
                    "line": node.lineno,
                    "issue": f"Method '{node.name}' uses @{deco_name} but doesn't start with '{expected_prefix}'",
                    "suggestion": f"Prefix method name with '{expected_prefix}'"
                })

    if 'default_' in node.name and not node.name.startswith('_default_'):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Default method '{node.name}' should start with '_default_'",
            "suggestion": "Rename method to start with '_default_'"
        })

    if 'selection' in node.name and not node.name.startswith('_selection_'):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Selection method '{node.name}' should start with '_selection_'",
            "suggestion": "Rename method to start with '_selection_'"
        })

    if node.name.startswith('do_'):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Action method '{node.name}' should start with 'action_'",
            "suggestion": "Rename method to start with 'action_'"
        })

def check_field_suffix(node, file_path):
    """
    Ensure field names have correct suffixes based on field type.

    Args:
        node (ast.Assign): The field definition node.
        file_path (str): Path to the Python file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"
    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
        field_type = node.value.func.attr
        if field_type in ['Many2one', 'One2many', 'Many2many']:
            target = node.targets[0]
            name = target.id if isinstance(target, ast.Name) else getattr(target, 'attr', None)
            if name:
                correct_suffix = '_id' if field_type == 'Many2one' else '_ids'
                if not name.endswith(correct_suffix):
                    results.append({
                        "file": file_path_shorten,
                        "line": node.lineno,
                        "issue": f"{field_type} field '{name}' should end with '{correct_suffix}'",
                        "suggestion": f"Rename variable to end with '{correct_suffix}'"
                    })

def check_variable_naming(node, file_path):
    """
    Check local variable naming conventions and suffixes for record/recordsets.

    Args:
        node (ast.Assign): The assignment statement node.
        file_path (str): Source file path.
    """
    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
        return

    targets = node.targets
    if not targets:
        return

    var_name = targets[0].id if isinstance(targets[0], ast.Name) else None
    if not var_name:
        return

    call_func = node.value.func
    call_attr = call_func.attr if isinstance(call_func, ast.Attribute) else ''

    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"

    if isinstance(call_func, ast.Subscript):
        if isinstance(call_func.value, ast.Attribute) and call_func.value.attr == 'env':
            if not is_camel_case(var_name):
                results.append({
                    "file": file_path_shorten,
                    "line": node.lineno,
                    "issue": f"Model variable '{var_name}' is not CamelCase",
                    "suggestion": "Use CamelCase (e.g., MyModelVariable)"
                })

    if call_attr in ['browse', 'search', 'search_read']:
        if call_attr == 'browse' and not var_name.endswith('_id'):
            results.append({
                "file": file_path_shorten,
                "line": node.lineno,
                "issue": f"Variable '{var_name}' may represent a single record, use _id suffix",
                "suggestion": "Rename variable to end with '_id'"
            })
        elif call_attr in ['search', 'search_read'] and not var_name.endswith('_ids'):
            results.append({
                "file": file_path_shorten,
                "line": node.lineno,
                "issue": f"Variable '{var_name}' may represent multiple records, use _ids suffix",
                "suggestion": "Rename variable to end with '_ids'"
            })

    if not is_snake_case(var_name):
        results.append({
            "file": file_path_shorten,
            "line": node.lineno,
            "issue": f"Variable name '{var_name}' is not snake_case",
            "suggestion": "Use snake_case (e.g., my_variable)"
        })

def check_python_file_name(file_path):
    """
    Check if the Python file name follows snake_case convention.

    Args:
        file_path (str): Full path to the Python file.
    """
    filename = os.path.basename(file_path)
    if not filename.endswith(".py") or filename in {"__init__.py", "__manifest__.py"}:
        return

    name_without_ext = filename[:-3]  # Remove .py
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"

    if not re.fullmatch(r"[a-z0-9_]+", name_without_ext):
        results.append({
            "file": file_path_shorten,
            "line": 0,
            "issue": f"File name '{filename}' does not follow snake_case",
            "suggestion": "Rename file using lowercase and underscores (e.g., my_model.py)"
        })

    if name_without_ext in {"temp", "test", "test1", "new", "misc"}:
        results.append({
            "file": file_path_shorten,
            "line": 0,
            "issue": f"File name '{filename}' is too generic or non-descriptive",
            "suggestion": "Use meaningful file names related to model or logic"
        })

def check_manifest_file(file_path):
    """
    Check the manifest file for any standard issues.

    Args:
        file_path (str): Full path to the Python file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{file_path.split(f'/{module_technical_name[0]}/')[1]}"
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        results.append({
            "file": file_path_shorten,
            "line": 0,
            "issue": "Invalid Python syntax in __manifest__.py",
            "suggestion": "Fix the syntax error"
        })
        return

    manifest_data = {}
    seen_keys = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k_node, v_node in zip(node.keys, node.values):
                if isinstance(k_node, ast.Str):
                    key = k_node.s
                    if key in seen_keys:
                        results.append({
                            "file": file_path_shorten,
                            "line": k_node.lineno if hasattr(k_node, "lineno") else 1,
                            "issue": f"Duplicate field '{key}' in manifest",
                            "suggestion": "Remove the duplicate entry"
                        })
                    seen_keys.add(key)
                    manifest_data[key] = v_node
            break  # Assume top-level dict is the manifest

    required_fields = {"name", "version", "depends", "author", "category", "summary", "data", "installable", "license"}
    for field in required_fields:
        if field not in manifest_data:
            results.append({
                "file": file_path_shorten,
                "line": 1,
                "issue": f"Missing required field '{field}' in manifest",
                "suggestion": f"Add '{field}' to the manifest dictionary"
            })

    # Version check
    version = manifest_data.get("version")
    if isinstance(version, ast.Constant):
        version_val = version.value
        if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+\.\d+", version_val):
            results.append({
                "file": file_path_shorten,
                "line": version.lineno if hasattr(version, "lineno") else 1,
                "issue": f"Version '{version_val}' does not follow '18.0.1.0.0' format",
                "suggestion": "Use 5-level semantic versioning like '18.0.1.0.0'"
            })

    # Depends check
    depends = manifest_data.get("depends")
    if isinstance(depends, ast.List):
        for d in depends.elts:
            if isinstance(d, ast.Constant) and not d.value.strip():
                results.append({
                    "file": file_path_shorten,
                    "line": d.lineno if hasattr(d, "lineno") else 1,
                    "issue": "Empty string in 'depends'",
                    "suggestion": "Remove empty string or specify actual dependency"
                })

    # Maintainer email format check
    maintainer = manifest_data.get("maintainer")
    if maintainer and isinstance(maintainer, ast.Constant):
        email = maintainer.value
        # Use this if not worked properly: r".*<[^@]+@[^@]+\.[^@]+>"
        if "@" not in email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            results.append({
                "file": file_path_shorten,
                "line": maintainer.lineno if hasattr(maintainer, "lineno") else 1,
                "issue": f"Invalid email format for 'maintainer': '{email}'",
                "suggestion": "Use a valid email address (e.g., john@example.com)"
            })

    # Check license
    valid_licenses = {"LGPL-3", "AGPL-3", "OEEL-1", "OPL-1", "GPL-3", "MIT"}
    license_node = manifest_data.get("license")
    if isinstance(license_node, ast.Constant):
        license_val = license_node.value
        if license_val not in valid_licenses:
            results.append({
                "file": file_path_shorten,
                "line": license_node.lineno if hasattr(license_node, "lineno") else 1,
                "issue": f"License '{license_val}' is not a recognized Odoo-compatible license",
                "suggestion": f"Use one of the valid licenses: {', '.join(valid_licenses)}"
            })
    # Data file order check: security/ files must come first
    data_node = manifest_data.get("data")
    if isinstance(data_node, ast.List):
        found_non_security = False
        for file_node in data_node.elts:
            if isinstance(file_node, ast.Constant):
                file_value = file_node.value
                if not file_value.startswith("security/"):
                    found_non_security = True
                elif found_non_security:
                    results.append({
                        "file": file_path_shorten,
                        "line": file_node.lineno if hasattr(file_node, "lineno") else 1,
                        "issue": f"'security' file '{file_value}' appears after non-security files",
                        "suggestion": "Move all 'security/' files to the top of the 'data' list"
                    })


def check_transient_model_location(py_file_path):
    """
    Check the transient model is in the wizard folder.

    Args:
        file_path (str): Full path to the Python file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{py_file_path.split(f'/{module_technical_name[0]}/')[1]}"
    with open(py_file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Attribute) and base.attr == "TransientModel":
                    if "wizard" not in py_file_path.replace("\\", "/").split("/"):
                        results.append({
                            "file": file_path_shorten,
                            "line": node.lineno,
                            "issue": f"TransientModel class '{node.name}' is not in a 'wizard/' directory",
                            "suggestion": "Move the file to a 'wizard/' folder to follow Odoo best practices"
                        })


def check_report_model_location(py_file_path):
    """
    Check the report model is in the report folder.

    Args:
        file_path (str): Full path to the Python file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{py_file_path.split(f'/{module_technical_name[0]}/')[1]}"
    with open(py_file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_abstract_model = any(
                isinstance(base, ast.Attribute) and base.attr == "AbstractModel"
                for base in node.bases
            )

            if is_abstract_model:
                for body_item in node.body:
                    if isinstance(body_item, ast.Assign):
                        for target in body_item.targets:
                            if isinstance(target, ast.Name) and target.id == "_name":
                                if isinstance(body_item.value, ast.Constant):
                                    model_name = body_item.value.value
                                    if (model_name.startswith("report.") and
                                            "report" not in py_file_path.replace("\\", "/").split("/")):
                                        results.append({
                                            "file": file_path_shorten,
                                            "line": node.lineno,
                                            "issue": f"Report model '{model_name}' is not in a 'report/' directory",
                                            "suggestion": "Move the report model to a 'report/' folder"
                                        })


def check_controller_naming(module_path, module_name):
    """
    Check the controller file naming.

    Args:
        module_path (str): Full path to the Python file.
        module_name (str): Module technical name.
    """
    controller_dir = os.path.join(module_path, "controllers")
    file_path_shorten = f"{module_technical_name[0]}/{module_path.split(f'/{module_technical_name[0]}/')[1]}"
    if not os.path.isdir(controller_dir):
        return

    for filename in os.listdir(controller_dir):
        filepath = os.path.join(controller_dir, filename)

        if not filename.endswith(".py"):
            continue

        if filename == "main.py":
            results.append({
                "file": file_path_shorten,
                "line": 1,
                "issue": "'main.py' is deprecated for controller files",
                "suggestion": f"Rename to '{module_name}.py' or the name of the inherited module"
            })

        if filename != f"{module_name}.py" and not filename.startswith("portal") and not filename.startswith("website"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if "http.Controller" in content and f"{module_name}.py" not in os.listdir(controller_dir):
                    results.append({
                        "file": file_path_shorten,
                        "line": 1,
                        "issue": f"'{filename}' may not follow the controller naming convention",
                        "suggestion": f"Use '{module_name}.py' for your base controller, "
                                      f"or name after the module you're inheriting"
                    })


def check_compute_method_exact_naming(py_file_path):
    """
    Check the compute function naming.

    Args:
        file_path (str): Full path to the Python file.
    """
    file_path_shorten = f"{module_technical_name[0]}/{py_file_path.split(f'/{module_technical_name[0]}/')[1]}"
    with open(py_file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    field_name = target.id
                    for value in ast.walk(node.value):
                        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
                            if value.func.attr in {
                                "Char", "Text", "Integer", "Float", "Boolean", "Date", "Datetime",
                                "Many2one", "One2many", "Many2many", "Html", "Binary", "Selection"
                            }:
                                for keyword in value.keywords:
                                    if keyword.arg == "compute" and isinstance(keyword.value, ast.Constant):
                                        compute_func = keyword.value.value
                                        expected_name = f"_compute_{field_name}"
                                        if compute_func != expected_name:
                                            results.append({
                                                "file": file_path_shorten,
                                                "line": keyword.lineno,
                                                "issue": f"Compute method should be named '{expected_name}' for "
                                                         f"field '{field_name}', found '{compute_func}'",
                                                "suggestion": f"Rename compute method to '{expected_name}'"
                                            })


def analyze_file(file_path):
    """
    Analyze a Python file using AST and apply all naming rules.

    Args:
        file_path (str): Full path to the .py file.
    """
    module_name = os.path.basename(file_path.rstrip("/\\"))  # Get folder name

    check_python_file_name(file_path)
    check_transient_model_location(file_path)
    check_report_model_location(file_path)
    check_controller_naming(file_path, module_name)
    check_compute_method_exact_naming(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            check_class_name(node, file_path)
            check_model_class(node, file_path)
            check_missing_docstring(node, file_path, type="class")
        elif isinstance(node, ast.FunctionDef):
            check_function_name(node, file_path)
            check_missing_docstring(node, file_path, type="function")
        elif isinstance(node, ast.Assign):
            check_field_suffix(node, file_path)
            check_variable_naming(node, file_path)


def scan_directory(directory):
    """
    Recursively scan a directory and analyze all .py files, skipping __init__.py and __manifest__.py.

    Args:
        directory (str): Path to the root directory.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_"):
                continue
            if file == "__manifest__.py":
                check_manifest_file(os.path.join(root, file))
            if file.endswith(".py") and file not in {"__init__.py", "__manifest__.py"}:
                analyze_file(os.path.join(root, file))


def check_odoo_python_standards(name, path):
    """
       Perform a scan of Python files in the given directory to check for Odoo-specific coding standard violations.

       This function clears previous results, sets the current module's technical name, and recursively scans the
       given directory for Python files. Each file is analyzed for adherence to Odoo's Python coding standards,
       and the results are accumulated.

       Args:
           name (str): The technical name of the Odoo module being checked.
           path (str): The absolute or relative file path to the directory containing the module's Python code.

       Returns:
           list: A list of dictionaries containing information about detected coding standard violations.
       """
    results.clear()
    module_technical_name[0] = name
    scan_directory(path)
    return results
