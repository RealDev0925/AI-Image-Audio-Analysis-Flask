import comfyui
import funcs_jinja
import json
import random
import funcs_supabase
import process_forms
import datetime
import actions


def add_to_media_link_table(data):
    # add to media table and get id
    media_id = funcs_supabase.insert_data("media", data)
    return media_id


def upload_media(upload_filepath, file_content, add_to_media_table=True):
    # upload to storage 
    upload = funcs_supabase.upload_file("media", upload_filepath, file_content)
    final_link = f"https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/object/public/media/{upload_filepath}"
    print(final_link)
    if add_to_media_table:
        data_to_send  = {"url": final_link, "type": "image"}
        media_id = add_to_media_link_table(data_to_send)
        print(media_id)
        return media_id
    else: 
        return final_link


# This function will save each image to a file on your computer
def save_images(image_data_list):
    for index, binary_data in enumerate(image_data_list):
        # Construct a filename for each image
        filename = f"image_{index + 1}.jpg"  # Change the file extension if necessary

        # Open a new file in binary write mode and write the image data
        with open(filename, 'wb') as image_file:
            image_file.write(binary_data)
        print(f"Image saved as {filename}")



def update_inputs(inputs_dict, input_data):
    # Create a new dictionary that's a copy of inputs_dict
    updated_dict = inputs_dict.copy()
    
    # Iterate through input_data and update updated_dict
    for key, value in input_data.items():
        # Check if the key is in updated_dict and the value is "available" (not None or other criteria)
        if key in updated_dict and value is not None:
            updated_dict[key] = value
            
    return updated_dict


def get_images(input_data):
    # print(input_data)
    sd_workflow = input_data["workflow_id"]
    workflow_data = funcs_supabase.select_data('sd_workflows', 'id', sd_workflow)
    workflow_data = workflow_data[0]
    print("WORKFLOW DATA")
    print(workflow_data)

    inputs = workflow_data.get("inputs", [])
    print("INPUTS")
    print(inputs)

    # Initialize an empty dictionary to store the extracted keys and values
    inputs_dict = {}
    # Iterate over each dictionary in the list and add the key-value pairs to the extracted_dict
    for item in inputs:
        key = item.get('key')
        value = item.get('value')
        if key and value:  # Make sure the key and value are not None
            inputs_dict[key] = value

    # print("INPUTS DICT")
    # print(inputs_dict)

    inputs_updated = update_inputs(inputs_dict, input_data)

    workflow_template = workflow_data.get("workflow_template")
    # print("WORKFLOW TEMPLATE")
    # print(workflow_template)

    # Render the template with the inputs
    rendered_template = funcs_jinja.render_from_template(workflow_template, inputs_updated)
    print("SENDING TO COMFY:")
    print(rendered_template)


  

    # template_rendered = funcs_jinja.render_from_template(template_content, inputs)
    # print(template_rendered)

    images_dict = comfyui.get_images(rendered_template)
    image_binaries = comfyui.collect_image_binaries(images_dict)

    outputs_list = []
    # upload_filepath = f"final_media/{project_id}/{timestamp}.mp4"

    for index, binary_data in enumerate(image_binaries):
        # Construct a filename for each image
        random_number = random.randint(1000, 1000000)

        filename = f"{random_number}_{index + 1}.jpg"

        media_complete = upload_media(filename, binary_data)

        outputs_list.append(media_complete)


    return outputs_list
 


def clean_dictionary_values(input_dict, lowercase=True):
    """
    This function takes a dictionary as input, and for each string value,
    it removes leading and trailing whitespaces, extra lines.
    It also converts it to lower case if the lowercase parameter is True (default).
    """
    # Iterate over all key-value pairs in the dictionary
    for key, value in input_dict.items():
        if isinstance(value, str):  # Check if the value is a string
            # Strip leading/trailing whitespace and replace newlines with space
            cleaned_value = ' '.join(value.split())
            # Convert to lower case if the lowercase flag is set
            if lowercase:
                cleaned_value = cleaned_value.lower()
            # Update the value in the dictionary
            input_dict[key] = cleaned_value

    return input_dict

# # Example dictionary with the lowercase option
# example_dict_lowercase = {
#     'key1': '   Some TEXT with Extra   Spaces   \n and new lines\n',
#     'key2': '\n\nAnother\nValue With \t Whitespaces\n   and lines. '
# }

# # Clean the dictionary values without converting to lower case
# cleaned_dict_no_lowercase = clean_dictionary_values(example_dict_lowercase, lowercase=False)
# cleaned_dict_no_lowercase



def get_prompt_variables(data):
    """gets the prompt variables for a given list of data, also removes the prompt_variables from the list
    input and output data format is a list of dictionaries:
    [{'name': 'workflow_id', 'value': '5'},

    """
    prompt_variables_dict = {}
    for item in data:
        if 'prompt_variables' in item['name']:
            parts = item['name'].split('[')
            parts = item['name'].split('[')

            position = int(parts[1].split(']')[0])
            key_or_value = parts[2].split(']')[0]
            if position not in prompt_variables_dict:
                prompt_variables_dict[position] = {}            
            prompt_variables_dict[position][key_or_value] = item['value']

    prompt_variables = [val for key, val in sorted(prompt_variables_dict.items())]
    
    # clean the prompt_variables
    prompt_variables_cleaned = []
    for pv in prompt_variables:
        pv = clean_dictionary_values(pv)
        prompt_variables_cleaned.append(pv)
    
    prompt_variables = prompt_variables_cleaned

    # remove the prompt_variables from the list
    cleaned_list = []  #
    for item in data:
        if 'prompt_variables' not in item['name']:
            cleaned_list.append(item)

    # if the key contain prompt, clean the values
    for item in cleaned_list:
        if 'prompt' in item['name']:
            item = clean_dictionary_values(item)

    # cleaned_list.append({'name': 'prompt_variables', 'value': prompt_variables})        
    return (prompt_variables, cleaned_list)



# prompt_variables, input_data_cleaned = get_prompt_variables(input_data)
# print(prompt_variables)
# print(input_data_cleaned)


def name_value_to_dict(list_of_dicts):
    """Converts a list of dicts with 'name'/'key' and 'value' keys to a single dict."""
    # Initialize an empty dictionary to store the results
    combined_dict = {}
    
    # Loop over each dictionary in the list
    for item in list_of_dicts:
        # The key can be under either 'name' or 'key'
        # We use the `get` method to try 'name' first, then 'key' if 'name' doesn't exist
        key = item.get('name') or item.get('key')
        value = item['value']
        
        # Add the key-value pair to the combined dictionary
        combined_dict[key] = value
        
    return combined_dict



def variables_into_prompts(input_data_cleaned, prompt_variables):
    for item in input_data_cleaned:
        if "prompt" in item:
            # print (item, input_data_cleaned[item])
            template = input_data_cleaned[item]
            input_data_cleaned[item] = funcs_jinja.render_from_template(template, prompt_variables, False)
            # print (input_data_cleaned[item])
    return input_data_cleaned
        # print(input_data_cleaned)
        # input_data_cleaned_w_vars = variables_into_prompts(input_data_cleaned, prompt_variables)
        # print(input_data_cleaned_w_vars)


def send_data_get_imgs(rendered_template):
    images_dict = comfyui.get_images(rendered_template)
    image_binaries = comfyui.collect_image_binaries(images_dict)
    outputs_list = []
    # upload_filepath = f"final_media/{project_id}/{timestamp}.mp4"
    for index, binary_data in enumerate(image_binaries):
        # Construct a filename for each image
        random_number = random.randint(1000, 1000000)
        filename = f"{random_number}_{index + 1}.jpg"
        media_complete = upload_media(filename, binary_data)
        outputs_list.append(media_complete)
    return outputs_list


def get_value_for_name(list_of_dicts, key)   :
    for item in list_of_dicts:
        if item['name'] == key:
            return item['value']
# data = [{'name': 'workflow_id', 'value': '5'}, {'name': 'prompt_start', 'value': 'HELLO masterpiece HDR'}, {'name': 'prompt_text', 'value': '(man, black hair, New York City skyline in the background), standing alone'}, {'name': 'prompt_end', 'value': 'SHARP focus, amazing fine detail, hyper realistic, lifelike, dramatic lighting'}, {'name': 'prompt_neg', 'value': 'hands, text, watermark, nsfw, painting, drawing, sketch, cartoon, anime, manga, render, 3d, watermark, signature, label, long neck'}, {'name': 'seed', 'value': '4956763'}, {'name': 'batch_size', 'value': '5'}, {'name': 'size-width', 'value': '512'}, {'name': 'size-height', 'value': '512'}, {'name': 'cfg_scale', 'value': '7'}, {'name': 'steps', 'value': '30'}, {'name': 'hi_res_fix', 'value': 'on'}, {'name': 'model', 'value': 'protovisionXLHighFidelity3D_beta0520Bakedvae.safetensors'}, {'name': 'prompt_variables', 'value': [{'key': 'man', 'value': 'indian rabi'}, {'key': 'city', 'value': 'London'}, {'key': 'dog', 'value': 'Golden retriever'}]}]
# [{'key': 'man', 'value': 'indian rabi'}, {'key': 'city', 'value': 'London'}, {'key': 'dog', 'value': 'Golden retriever'}]

def remove_name_for_value (list_of_dicts, key):
    for item in list_of_dicts:
        if item['name'] == key:
            list_of_dicts.remove(item)
            return list_of_dicts
        
# data = [{'name': 'workflow_id', 'value': '5'}, {'name': 'prompt_start', 'value': 'HELLO masterpiece HDR'}, {'name': 'prompt_text', 'value': '(man, black hair, New York City skyline in the background), standing alone'}, {'name': 'prompt_end', 'value': 'SHARP focus, amazing fine detail, hyper realistic, lifelike, dramatic lighting'}, {'name': 'prompt_neg', 'value': 'hands, text, watermark, nsfw, painting, drawing, sketch, cartoon, anime, manga, render, 3d, watermark, signature, label,'}, {'name': 'seed', 'value': '4956763'}, {'name': 'batch_size', 'value': '5'}, {'name': 'size-width', 'value': '512'}, {'name': 'size-height', 'value': '512'}, {'name': 'cfg_scale', 'value': '7'}, {'name': 'steps', 'value': '30'}, {'name': 'hi_res_fix', 'value': 'on'}, {'name': 'model', 'value': 'protovisionXLHighFidelity3D_beta0520Bakedvae.safetensors'}, {'name': 'prompt_variables', 'value': [{'key': 'man', 'value': 'indian rabi'}, {'key': 'city', 'value': 'London'}, {'key': 'dog', 'value': 'Golden retriever'}]}]
# key = 'prompt_variables'
# removed_list = remove_name_for_value(data, key)
# [{'name': 'workflow_id', 'value': '5'}, {'name': 'prompt_start', 'value': 'HELLO masterpiece HDR'}, {'name': 'prompt_text', 'value': '(man, black hair, New York City skyline in the background), standing alone'}, {'name': 'prompt_end', 'value': 'SHARP focus, amazing fine detail, hyper realistic,  '}, {'name': 'prompt_neg', 'value': 'hands, text, watermark, nsfw, painting, drawing, sketch, cartoon, anime, manga, render, 3d, watermark, signature, label'}, {'name': 'seed', 'value': '4956763'}, {'name': 'batch_size', 'value': '5'}, {'name': 'size-width', 'value': '512'}, {'name': 'size-height', 'value': '512'}, {'name': 'cfg_scale', 'value': '7'}, {'name': 'steps', 'value': '30'}, {'name': 'hi_res_fix', 'value': 'on'}, {'name': 'model', 'value': 'protovisionXLHighFidelity3D_beta0520Bakedvae.safetensors'}]


def change_input_list_value(input_list, key, value):
    for item in input_list:
        if item['name'] == key:
            item['value'] = value
            break
    return input_list

# # Example usage
# test_list = [{'name': 'workflow_id', 'value': '5'}, {'name': 'prompt_start', 'value': 'HELLO masterpiece HDR'}, {'name': 'prompt_text', 'value': '{{man}} bakes pizza'}, {'name': 'prompt_end', 'value': 'SHARP focus, amazing fine detail, hyper realistic, lifelike '}, {'name': 'prompt_neg', 'value': 'hands, text, watermark, nsfw, painting, drawing, sketch, cartoon, anime, manga, render, 3d, watermark, signature, label, long neck'}, {'name': 'seed', 'value': '4956763'}, {'name': 'batch_size', 'value': '5'}, {'name': 'size-width', 'value': '512'}, {'name': 'size-height', 'value': '512'}, {'name': 'cfg_scale', 'value': '7'}, {'name': 'steps', 'value': '30'}, {'name': 'hi_res_fix', 'value': 'on'}, {'name': 'model', 'value': 'protovisionXLHighFidelity3D_beta0520Bakedvae.safetensors'}, {'name': 'prompt_variables', 'value': [{'key': 'man', 'value': 'indian rabi'}, {'key': 'city', 'value': 'London'}, {'key': 'dog', 'value': 'Golden retriever'}]}]
# new_prompt_text = "A cat lounging in a sunny garden"
# updated_list = change_input_list_value(test_list, new_prompt_text)
# print(updated_list)

def get_images_2(input_data_original):

    # #1 extract prompt variables and remove from input data
    # prompt_variables, input_data_cleaned = get_prompt_variables(input_data_original)
    # # print(prompt_variables)
    # # print(input_data_cleaned)

    # #2 convert input data and prompt variables to dicts
    # prompt_variables = name_value_to_dict(prompt_variables)
    # # print(prompt_variables)
    # input_data = name_value_to_dict(input_data_cleaned)
    # # print(input_data)

    prompt_variables = get_value_for_name(input_data_original, 'prompt_variables')
    input_data_cleaned = remove_name_for_value(input_data_original, 'prompt_variables')
    input_data = name_value_to_dict(input_data_cleaned)



    #3 puts the prompt variables into the input data dict
    input_data = variables_into_prompts(input_data, prompt_variables)
    # print(input_data)

    #4 get the workflow template 
    workflow_id = input_data.get('workflow_id')
    workflow_data = funcs_supabase.select_data('sd_workflows', 'id', workflow_id)
    workflow_data = workflow_data[0]
    workflow_template = workflow_data['workflow_template']
    
    #5 replace the variables in the workflow_template with new input data.
    rendered_template = funcs_jinja.render_from_template(workflow_template, input_data, True)


    print("SENDING TO COMFY:")
    print(rendered_template)
    # print(type(rendered_template))

    # # get the images
    imgs = send_data_get_imgs(rendered_template)
    return imgs
    

    
# input_data = [{'name': 'workflow_id', 'value': '5'}, {'name': 'prompt_start', 'value': 'masterpiece HDR'}, {'name': 'prompt_text', 'value': '{{man}} in {{city}} with {{dog}}'}, {'name': 'prompt_end', 'value': 'sharp focus, amazing fine detail, hyper realistic, lifelike, dramatic lighting'}, {'name': 'prompt_neg', 'value': 'bad hands, text, watermark, nsfw, painting, drawing, sketch, cartoon, anime, manga, render, 3d, watermark, signature, label, long neck'}, {'name': 'seed', 'value': '3688084'}, {'name': 'batch_size', 'value': '3'}, {'name': 'size-width', 'value': '512'}, {'name': 'size-height', 'value': '512'}, {'name': 'cfg_scale', 'value': '7'}, {'name': 'steps', 'value': '30'}, {'name': 'hi_res_fix', 'value': 'on'}, {'name': 'model', 'value': 'protovisionXLHighFidelity3D_beta0520Bakedvae.safetensors'}, {'name': 'prompt_variables[0][key]', 'value': 'man'}, {'name': 'prompt_variables[0][value]', 'value': 'Sexy, blonde, big butt, skimpy outfit'}, {'name': 'prompt_variables[1][key]', 'value': 'city'}, {'name': 'prompt_variables[1][value]', 'value': 'new york city, chrysler building in the background'}, {'name': 'prompt_variables[2][key]', 'value': 'dog'}, {'name': 'prompt_variables[2][value]', 'value': 'Merle cockapoo'}]
# get_images_2(input_data)






def process_scene(scene_id):
    """
    """
    try:
        scene_data = funcs_supabase.select_data("scenes", "id", scene_id)[0]
    except IndexError:
        print(f"No data found for scene ID {scene_id}")
        return

    sd_prompts = scene_data.get("sd_prompts")
    album_id = scene_data.get("album_id")
    scene_text = scene_data.get("scene_text")


    project_id = scene_data.get("project_id")
    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
    print(project_data)
    sd_settings = project_data.get("sd_settings")
    print(sd_settings)


    # if sd_settings is None:
    #     sd_settings


    # # get default workflow id
    # workflows = funcs_supabase.select_data("sd_workflows", "status", "Active")
    # for workflow in workflows:
    #     if workflow.get("name") == "Default":
    #         workflow_id = workflow.get("id")
    #         data_to_send["workflow_id"] = workflow_id
    #         break


    # change the prompt_text in the workflow/sd_settings 

    # send to sd_images as input_data for get_images

    # get images for each prompt 
    for prompt in sd_prompts:
        sd_settings = change_input_list_value(sd_settings, "prompt_text", prompt)

        print(sd_settings)
        sd_images_list = get_images_2(sd_settings)
        for media in sd_images_list:
            print(media)
            media_id = media.get("id")
            # add to media table and get id
            funcs_supabase.insert_data("album_media_link", {"album_id": album_id, "media_id": media_id})


def process_project_scenes(project_id):
    """
    """
    scenes = actions.get_scenes_for_project(project_id)
    for scene_id in scenes:
        process_scene(scene_id)

# Usage
# process_project_scenes(39)
#


def save_sd_settings(input_data):
    project_id = get_value_for_name(input_data, 'project_id')
    print(project_id)

    # prompt_variables = get_value_for_name(input_data, 'prompt_variables')
    # print(prompt_variables)

    prompt_variables, cleaned_list = get_prompt_variables(input_data)
    print(prompt_variables)

    # input_data_cleaned = remove_name_for_value(input_data, 'prompt_variables')
    cleaned_list.append({'name': 'prompt_variables', 'value': prompt_variables})
    update = funcs_supabase.update_data("video_creator_projects", project_id, {"sd_settings": cleaned_list})
    print(update)
    return update





def save_and_run(input_data):
    save_sd_settings(input_data)
    project_id = get_value_for_name(input_data, 'project_id')


    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
    sd_settings = project_data.get("sd_settings")
    print(sd_settings)



    sd_images_list = get_images_2(sd_settings)
    for media in sd_images_list:
        print(media)
            

    return sd_images_list