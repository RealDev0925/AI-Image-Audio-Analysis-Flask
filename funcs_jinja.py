from jinja2 import Environment, meta, Template
from jinja2.nodes import Assign, Name, Const, Dict, List, Tuple
import json


def render_from_template (template_content, data_dict, return_dict=True):
    template = Template(template_content)
    rendered_template = template.render(data_dict)
    
    # returns a string instead of a dict
    if return_dict:
        rendered_template = json.loads(rendered_template)
    
    return rendered_template


def extract_variables_from_template(template_content):
    """
    Extracts variable names and their content from the provided Jinja2 template content.

    Args:
    template_content (str): A string containing Jinja2 template content.

    Returns:
    dict: A dictionary with variable names as keys and their contents as values.
    """

    # Create an environment
    env = Environment()

    # Parse the template content to create an AST
    parsed_content = env.parse(template_content)

    # Initialize a dictionary to hold the names and contents of the variables
    variable_contents = {}

    # Function to evaluate the literal node values
    def eval_node(node):
        if isinstance(node, Const):
            return node.value
        elif isinstance(node, List):
            return [eval_node(child) for child in node.items]
        elif isinstance(node, Dict):
            return {eval_node(pair.key): eval_node(pair.value) for pair in node.items}
        elif isinstance(node, Tuple):
            return tuple(eval_node(child) for child in node.items)
        # Add other types of nodes as needed...
        else:
            return None

    # Function to recursively traverse the AST
    def traverse(node):
        """Traverse the AST and add variable names and contents to the dictionary."""
        if isinstance(node, Assign):
            # Handle the `{% set %}` tag
            target = node.target
            value = eval_node(node.node)
            if isinstance(target, Name) and value is not None:
                variable_contents[target.name] = value
        # Recursively visit child nodes
        for child in node.iter_child_nodes():
            traverse(child)

    # Start the traversal from the root of the AST
    traverse(parsed_content)

    return variable_contents

# # Example usage:
# template_content = """
# {% set prompt = {"type": "image", "value": "blah blah", "src": "path/to/image.png"} %}
# {{ prompt }}
# {{ prompt.value }}
# {{ prompt.src }}

# {% set prompt_negative = {"type": "text", "value": "another_thing", "src": "path/to/image.png"} %}
# {{ prompt }}
# {{ prompt.value }}
# {{ prompt.src }}
# """

# # Call the function and print the result
# variable_data = extract_variables_from_template(template_content)
# print(variable_data)
