import funcs_supabase
import nltk
from nltk.tokenize import sent_tokenize

# Download the Punkt tokenizer models
nltk.download('punkt')


# split the article into sentences
def split_article_into_sentences(article):
    """
    Splits an article into sentences and trims each sentence.
    
    Parameters:
        article (str): The article text to be split.
        
    Returns:
        List[str]: A list of trimmed sentences.
    """
    sentences = sent_tokenize(article)
    trimmed_sentences = [sentence.strip() for sentence in sentences]
    return trimmed_sentences


# put in a list of scenes, it will change the status of all the scenes in the list to the status you want
def change_scene_status (scene_id_list, status):
    resp_list = []
    for id in scene_id_list:
            resp = funcs_supabase.update_data("scenes", id, {"status": status})
            print(resp)
            resp_list.append(resp)
    return(resp_list)

# li = [1, 2]
# change_scene_status(li, "Deleted")


# Get the active scenes for a project -> Returns list of dicts. Each dict is a scene
def get_active_scenes(project):
    conditions = [
    {"column": "project_id", "operator": "eq", "value": project},
    {"column": "status", "operator": "eq", "value": "Active"}
    ]
    scenes_list = funcs_supabase.select_data_with_conditions("scenes", conditions)
    sorted_list = sorted(scenes_list, key=lambda x: x['scene_order_position'])
    # print(sorted_list)
    return sorted_list

# Get the active scenes for a project -> Returns list of ints. Each int is a scene id
def get_scenes_for_project (project):
    scenes_list = get_active_scenes(project)
    # get the list of ids for the scenes
    scenes_id_list = []
    for scene in scenes_list:
        sc_id = scene["id"]
        sc_id = int(sc_id)
        scenes_id_list.append(sc_id)    
    return scenes_id_list

# scenes = get_scenes_for_project (3)
# print(scenes)



# creates an empty album, then makes a scene which is linked to the new album 
def create_new_scene(project, extra_data = {}, scene_order_position = 0):

    new_album_id = funcs_supabase.insert_data("albums", data={})
    new_album_id = new_album_id["id"]

    scene_data = {"album_id":new_album_id, "project_id":project, "status":"Active", "scene_order_position":scene_order_position }

    merged_dict = {**scene_data, **extra_data}
    new_scene = funcs_supabase.insert_data("scenes", data=merged_dict)

    return new_scene




def split_article_into_scenes(project, article):
     # get a list of sentences which can be made into scenes
    split_sentences = split_article_into_sentences(article)
    active_scenes_list = get_scenes_for_project(project)
    change_scenes = change_scene_status(active_scenes_list, "Deleted")

    for index_number, scene_text in enumerate(split_sentences):
        print(index_number, scene_text)
        new_scene = create_new_scene(project, {"scene_text":scene_text}, index_number)

    return True






#####################
#####################
#####################
from jinja2 import Template
# import actions
import funcs_open_ai_chat
import funcs_supabase
import re

def get_joined_scenes(scenes):
    scene_texts = [scene['scene_text'] for scene in scenes]
    joined_scenes = "\n".join(f"Scene {i+1}: {val}" for i, val in enumerate(scene_texts))
    return joined_scenes


def render_template_from_file(file_path, variables):
    with open(file_path, 'r') as f:
        template_content = f.read()
    template = Template(template_content)
    return template.render(variables)

def get_gpt_response(rendered_content, settings={}):
    resp = funcs_open_ai_chat.get_chat_response(rendered_content, settings)
    return resp["choices"][0]["message"]["content"]

def extract_keywords(input_text):
    # remove empty lines
    lines = input_text.strip().split("\n")
    print(f"lines length: {len(lines)}")
    keywords_list = []
    for line in lines:
        clean_line = re.sub(r"Scene \d+: ", "", line)
        clean_line = re.sub(r"[^\w\s,]", "", clean_line)
        keywords = [keyword.strip() for keyword in clean_line.split(",")]
        keywords_list.append(keywords)
    return keywords_list

def create_data_list(keywords_list, scenes, keyword_column="theme_keywords"):
    data_list = []
    for i, keywords in enumerate(keywords_list):
        data = {keyword_column: keywords, 'id': scenes[i]['id']}
        data_list.append(data)
    return data_list




def update_theme_keywords(project_id):
    """For a project, it get all the keywords for each scene and updates the theme_keywords column in the scenes table."""
    
    # scenes = actions.get_active_scenes(project_id)
    scenes = get_active_scenes(project_id)
    joined_scenes = get_joined_scenes(scenes)
    variables = {'input': joined_scenes, "scene_length": len(scenes)}
    file_path = 'prompts/key_phrases.txt'

    rendered_content = render_template_from_file(file_path, variables)
    print (rendered_content)
    
    gpt_resp = get_gpt_response(rendered_content)
    print (gpt_resp)
    keywords_list = extract_keywords(gpt_resp)
    # print(keywords_list)
    # print(scenes)

    print(f"Number of keywords: {len(keywords_list)}, number of scenes: {len(scenes)}")

    if len(keywords_list) == len(scenes):
        data_list = create_data_list(keywords_list, scenes)
        # print(data_list)
        update_resp = funcs_supabase.update_multiple_rows("scenes", data_list)
        # print(update_resp)
        return data_list

    else:
        print("The lengths of keywords_list and scenes do not match.")

# update_theme_keywords(23)



#####################
#####################
#####################


import funcs_database

def get_cdn_link(url, width = None, height = None, resize = None):
    # resize: 'contain', // 'cover' | 'fill'
    # https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/object/public/media/4b8840f6-1d1a-4b78-b728-fcf039a2f366.jpeg    
    # https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/render/image/public/media/0bd35f13-e222-4504-9362-5183bda46a6b.png?width=300&height=300&resize=cover
    # parsed_url = urlparse(url)
    # print(f"Scheme: {parsed_url.scheme}")
    # print(f"Netloc: {parsed_url.netloc}")
    # print(f"Path: {parsed_url.path}")
    # print(f"Parameters: {parsed_url.params}")
    # print(f"Query: {parsed_url.query}")
    # print(f"Fragment: {parsed_url.fragment}")

    replace_me = "https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/object/public/media/"
    replace_with = "https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/render/image/public/media/"

    new_url = url.replace(replace_me, replace_with)
    # remove all the parameters
    new_url = new_url.split("?")[0]

    new_params = []

    if width is not None:
        new_params.append(f"width={width}")

    if height is not None:
        new_params.append(f"height={height}")

    if resize is not None:
        new_params.append(f"resize={resize}")

    if len(new_params) > 0:
        new_url = new_url + "?" + "&".join(new_params)

    # print(new_url)

    return new_url




# def process_media_list_for_display(media_list):
#     # print(media_list)

#     output_list = []

#     for media in media_list:
#         # id, media_type, description, url, caption, thumbnail, source_url, source_type
#         media_dict = {}
        

#         media_dict['id'] = media['id']
#         media_dict['media_type'] = media.get('media_type', None)


#         if media['description'] is not None:
#             media_dict['description'] = media['description']


#         if media["url"] is None:
#             if media["url_remote"] is not None:
#                 media_dict['url'] = media["url_remote"]
#         else:
#             media_dict['url'] = media["url"]


#         if media["caption"] is not None:
#             media_dict['caption'] = media["caption"]


#         if media["thumbnail_url"] is not None:
#             try:
#                 cdn_link = get_cdn_link(media["thumbnail_url"], width = 500,  resize = "contain")
#                 media_dict['thumbnail'] = cdn_link
                
#             except:
#                 media_dict['thumbnail'] = media["thumbnail_url"]

#         if media["source_type"] is not None:
#             media_dict['source_type'] = media["source_type"]

#         if media["source_data"] is not None:
#             if media["source_data"]["url"] is not None:
#                 media_dict['source_url'] = media["source_data"]["url"]


#         output_list.append(media_dict)


#     return output_list


def process_media_for_display(media, include_all_fields=False):
    # Process a single media item
    source_data = media.get('source_data')
    source_url = source_data.get('url') if source_data is not None else None

    media_dict = {
        'id': media['id'],
        'type': media.get('type'),
        'description': media.get('description'),
        'caption': media.get('caption'),
        'source_type': media.get('source_type'),
        'source_url': source_url
    }
    
    media_dict['url'] = media.get('url') or media.get('url_remote')
    
    thumbnail_url = media.get('thumbnail_url')
    if thumbnail_url is not None:
        try:
            cdn_link = get_cdn_link(thumbnail_url, width=500, resize="contain")
            media_dict['thumbnail'] = cdn_link
        except:
            media_dict['thumbnail'] = thumbnail_url

    if include_all_fields:
        # Combine original media item with processed fields, giving preference to processed fields
        return {**media, **{k: v for k, v in media_dict.items() if v is not None}}
    else:
        # Return only processed fields, excluding None values
        return {k: v for k, v in media_dict.items() if v is not None}


def process_media_list_for_display(media_list_or_dict, include_all_fields=False):
    output_list = []

    # Convert a single dictionary into a list
    if isinstance(media_list_or_dict, dict):
        media_list_or_dict = [media_list_or_dict]

    for media in media_list_or_dict:
        processed_media = process_media_for_display(media, include_all_fields)
        output_list.append(processed_media)
    
    return output_list



# Test the function
# album_id_to_search = 10  # Replace with your actual album_id
# result = get_media_by_album_id(album_id_to_search)
# print(result)  # This will print a list of dictionaries

# processed_result = process_media_list_for_display(result)
# print(processed_result)  # This will print a list of dictionaries



def return_processed_media_list(album):
    media_list = funcs_database.get_media_by_album_id(album)
    processed_output = process_media_list_for_display(media_list)
    return processed_output






###### Gen SD Prompts ######

def get_prompts_list(input_text):
    lines = input_text.split("\n")

    # Initialize an empty list to store non-empty lines
    filtered_lines = []

    # Split the original string into lines and loop through them
    for line in lines:
        # Remove leading and trailing whitespaces and check if the line is empty
        if line.strip():
            # If the line is not empty, append it to the filtered_lines list
            filtered_lines.append(line.strip())

    # print(filtered_lines)

    descriptions = []
    for line in filtered_lines:
        # print(line)
        # Split the string by ": " and get the second part
        description = line.split(": ", 1)[1]
        # Append the description to the descriptions list
        description = [description]
        descriptions.append(description)

    return descriptions


def get_scene_prompts(project_id, sd_workflow="sd_imgs_1"):

    # scenes = actions.get_active_scenes(project_id)
    scenes = get_active_scenes(project_id)
    joined_scenes = get_joined_scenes(scenes)

    # render the prompt for GPT using joined scenes and saved prompt as jijna template
    variables = {'input': joined_scenes}
    file_path = f'prompts/{sd_workflow}.txt'
    rendered_content = render_template_from_file(file_path, variables)
    # print(rendered_content)

    # get response from GPT
    gpt_resp = get_gpt_response(rendered_content)
    print("GPT RESPONSE HERE: ")
    print(gpt_resp)

    
    keywords_list = get_prompts_list(gpt_resp)
    print("KEYWORDS LIST HERE: ")
    print(keywords_list)

    # print(keywords_list)
    # print(scenes)

    if len(keywords_list) == len(scenes):
        data_list = create_data_list(keywords_list, scenes, keyword_column="sd_prompts")
        print(data_list)

        update_resp = funcs_supabase.update_multiple_rows("scenes", data_list)
        print(update_resp)

    #     return data_list

    # else:
    #     print("The lengths of keywords_list and scenes do not match.")


