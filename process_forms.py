def extract_values_if_same_key(dict_list):
    if not dict_list:
        return []

    # Check if all dictionaries have the same single key
    all_keys = {list(d.keys())[0] for d in dict_list if d}
    if len(all_keys) == 1:
        key = all_keys.pop()
        return [d[key] for d in dict_list if key in d]
    else:
        raise ValueError("Not all dictionaries have the same single key")




def convert_to_dict(js_data):
    python_dict = {}

    for item in js_data:
        key = item['name']
        value = item['value']

        if '[' in key and ']' in key:
            # Extract base key and sub-keys
            base_key, rest = key.split('[', 1)
            sub_key = rest.split(']', 1)[0]

            if base_key not in python_dict:
                python_dict[base_key] = []

            # Convert sub_key to int if possible
            try:
                sub_key = int(sub_key)
            except ValueError:
                pass

            # Expand the list if necessary
            while len(python_dict[base_key]) <= sub_key:
                python_dict[base_key].append(None)

            # Further nesting
            if '][' in rest:
                _, nested_key = rest.split('][')
                nested_key = nested_key.replace(']', '').replace('[', '')

                # If the final list item is None or not a dictionary, create a dictionary
                if not isinstance(python_dict[base_key][sub_key], dict):
                    python_dict[base_key][sub_key] = {}

                python_dict[base_key][sub_key][nested_key] = value
            else:
                # Directly assign the value for simple list scenarios
                python_dict[base_key][sub_key] = value
        else:
            python_dict[key] = value

    return python_dict



def process_python_dict (pythonic_dict):
    processed_dict = {}

    for item in pythonic_dict:
        value = pythonic_dict[item]


        if type(value) == list:
            # print(item)
            values = extract_values_if_same_key(value)
            # print(values)

            processed_dict[item] = values

        else:
            processed_dict[item] = value

    return processed_dict



def js_to_db_format(js_data):
    python_dict = convert_to_dict(js_data)
    processed = process_python_dict(python_dict)
    return processed



import actions
# Project Actions Form 
def execute_project_actions(data):
    project_id = data['project_id']
    scene_id = data.get('scene_id', None)

    response = []

    # Split Text
    if data.get("text_to_split_check") == "on":
        print("Splitting Text")
        text_to_split = True
        if data["text_to_split"] != "":
            text_to_split = data["text_to_split"]
            split_text_result = actions.split_article_into_scenes(project_id, text_to_split)
            response.append(split_text_result)

    # Get Keywords
    if data.get("get_keywords_check") == "on":
        print("Getting Keywords")
        keywords_result = actions.update_theme_keywords(project_id)

    # get prompts 
    if data.get("get_prompts_check") == "on":
        print("Getting Prompts")
        prompts_result = actions.get_scene_prompts(project_id)
        response.append(prompts_result)

    return response




#%%

def convert_to_dict_simple(input_list):
    result = {}
    for item in input_list:
        key = item['name']
        value = item['value']
        if key in result:
            # If the key already exists, append the value to the existing list.
            if isinstance(result[key], list):
                result[key].append(value)
            else:
                # If the key exists but is not a list, create a new list with the old and new values.
                result[key] = [result[key], value]
        else:
            # If the key does not exist, add it to the dictionary.
            result[key] = value
    return result

# # Example usage
# input_list = [{'name': 'project_id', 'value': '41'}, 
#               {'name': 'stock_check', 'value': 'on'}, 
#               {'name': 'stock_options', 'value': 'Default'}, 
#               {'name': 'ai_check', 'value': 'on'}, 
#               {'name': 'select_scenes', 'value': '342'}, 
#               {'name': 'select_scenes', 'value': '345'}, 
#               {'name': 'formId', 'value': 'get_clips'}]

# converted_dict = convert_to_dict(input_list)
# print(converted_dict)
# {'project_id': '41', 'stock_check': 'on', 'stock_options': 'Default', 'ai_check': 'on', 'select_scenes': ['342', '345'], 'formId': 'get_clips'}

#%%

# General all purpose forms
import compose_2
import get_clips


def process_form(input_data):

    # print("input_data")
    # print(input_data)

    python_dict = convert_to_dict(input_data)
    # print("python_dict")
    # print(python_dict)

    processed_data = process_python_dict(python_dict)
    # print("processed_data")
    # print(processed_data)





    formId = processed_data["formId"]
    
    if formId == "project_actions":
        response =  execute_project_actions(processed_data)
        return response
    
    
    elif formId == "get_clips":
            simple_dict = convert_to_dict_simple(input_data)
            response =  get_clips.get_clips_form_submit(simple_dict)
            return response



    elif formId == "compose_final":
        project_id = processed_data["project_id"]
        response =  compose_2.process(project_id)
        
        
        return response
    
    else :
        return processed_data
    


# Define the function to process the input list and extract the items with multiples of the same name.
def form_repeater_save_format (input_list):
    # Initialize a dictionary to hold the processed items
    processed = {}
    # Loop through each item in the input list
    for item in input_list:
        # Check if the name contains brackets indicating it is part of a repeated set
        if '[' in item['name'] and ']' in item['name']:
            # Extract the base key and the index from the name
            base_key = item['name'].split('[')[0]
            index = int(item['name'].split('[')[1].split(']')[0])
            sub_key = item['name'].split('[')[2].split(']')[0]
            # Initialize the base key if it is not already in the processed dictionary
            if base_key not in processed:
                processed[base_key] = {"key": base_key, "type": "repeater", "value": []}
            # Ensure the list has enough entries to include this index
            while len(processed[base_key]["value"]) <= index:
                processed[base_key]["value"].append({})
            # Add the sub key and value to the appropriate index
            processed[base_key]["value"][index][sub_key] = item['value']

    # Remove any non-repeated keys
    processed = {k: v for k, v in processed.items() if len(v["value"]) > 1}
    # Return the processed items as a list
    return list(processed.values())

# # Given input list
# input_list =[
#     {
#         "name": "workflow_id",
#         "value": ""
#     },
#     {
#         "name": "prompt_variables[0][key]",
#         "value": "rdas"
#     },
#     {
#         "name": "prompt_variables[0][value]",
#         "value": "asdsaD"
#     },
#     {
#         "name": "prompt_variables[1][key]",
#         "value": "asdsadS"
#     },
#     {
#         "name": "prompt_variables[1][value]",
#         "value": "ASDads"
#     },
#     {
#         "name": "prompt_variables[2][key]",
#         "value": "asdas"
#     },
#     {
#         "name": "prompt_variables[2][value]",
#         "value": "ss"
#     },
#     {
#         "name": "prompt_variables[3][key]",
#         "value": "ssd"
#     },
#     {
#         "name": "prompt_variables[3][value]",
#         "value": ""
#     },
#     {
#         "name": "prompt_variables[4][key]",
#         "value": ""
#     },
#     {
#         "name": "prompt_variables[4][value]",
#         "value": "sdsd"
#     }
# ]

# # Process the input list and store the result
# processed_list = form_repeater_save_format(input_list)
# print(processed_list)
