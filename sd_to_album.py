#%%

import funcs_supabase
import actions
import pexels
import random
import vector_search
import sd_images


def change_input_list_value(input_list, key, value):
    for item in input_list:
        if item['name'] == key:
            item['value'] = value
            break
    return input_list



def process_scene(scene_id):

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
    print(f"project data: {project_data}")
    sd_settings = project_data.get("sd_settings")
    print(f"sd_settings {sd_settings}")


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
        sd_images_list = sd_images.get_images_2(sd_settings)
        for media in sd_images_list:
            print(media)
            media_id = media.get("id")
            # add to media table and get id
            funcs_supabase.insert_data("album_media_link", {"album_id": album_id, "media_id": media_id})


def process_project_scenes(project_id, scenes_list=None):
    """
    Processes all scenes for a given project.

    :param project_id: ID of the project.
    :param scenes_list: Optional list of scenes to process. If None, fetch scenes for the project.
    """
    if scenes_list is None:
        scenes = actions.get_scenes_for_project(project_id)
    else:
        scenes = scenes_list

    for scene_id in scenes:
        process_scene(scene_id)



#%%

# ai_response = process_project_scenes(45, scenes_list=[390])



# %%
