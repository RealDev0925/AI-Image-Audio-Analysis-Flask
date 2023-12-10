# import stock_to_album
# import sd_to_album



# def get_clips_form_submit(data):
#     print(data)
#     # Example data: 
#     # {'project_id': '41', 'stock_check': 'on', 'stock_options': 'Default', 
#     #  'ai_check': 'on', 'select_scenes': '341', 'formId': 'get_clips'}

#     project_id = data.get("project_id", None)
#     response = []
    
#     # Extract and validate the select_scenes list
#     select_scenes = data.get("select_scenes", None)
#     if isinstance(select_scenes, str) and select_scenes.isdigit():
#         scenes_list = [int(select_scenes)]
#     elif isinstance(select_scenes, list) and all(scene.isdigit() for scene in select_scenes):
#         scenes_list = [int(scene) for scene in select_scenes]
#     else:
#         scenes_list = None

#     if data.get("stock_check", None) == "on":
#         stock_skip_search = data.get("stock_skip_search", None)
#         include_stock_media_input = False if stock_skip_search == "on" else True
#         resp = stock_to_album.process_project_scenes(project_id, include_stock_media=include_stock_media_input, scenes_list=scenes_list)
#         response.append(resp)

#     if data.get("ai_check", None) == "on":
#         print("getting ai images")    
#         resp = sd_to_album.process_project_scenes(project_id, scenes_list=scenes_list)
#         response.append(resp)
#     else:
#         resp = "nada"
#         response.append(resp)

#     return response

#%%

import threading
import stock_to_album
import sd_to_album

#%%

def get_clips_form_submit(data):
    print(data)
    project_id = data.get("project_id", None)

    # Extract and validate the select_scenes list
    select_scenes = data.get("select_scenes", None)
    if isinstance(select_scenes, str) and select_scenes.isdigit():
        scenes_list = [int(select_scenes)]
    elif isinstance(select_scenes, list) and all(scene.isdigit() for scene in select_scenes):
        scenes_list = [int(scene) for scene in select_scenes]
    else:
        scenes_list = None

    # Function to wrap the call and store the response
    def stock_wrapper():
        nonlocal stock_response
        stock_response = stock_to_album.process_project_scenes(project_id, include_stock_media=include_stock_media_input, scenes_list=scenes_list)

    def ai_wrapper():
        nonlocal ai_response
        ai_response = sd_to_album.process_project_scenes(project_id, scenes_list=scenes_list)

    stock_response, ai_response = None, None

    threads = []

    if data.get("stock_check", None) == "on":
        stock_skip_search = data.get("stock_skip_search", None)
        include_stock_media_input = False if stock_skip_search == "on" else True
        stock_thread = threading.Thread(target=stock_wrapper)
        threads.append(stock_thread)

    if data.get("ai_check", None) == "on":
        print("getting ai images")    
        ai_thread = threading.Thread(target=ai_wrapper)
        threads.append(ai_thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Collect the responses
    response = [resp for resp in [stock_response, ai_response] if resp is not None]
    return response if response else ["nada"]

# You would call this function normally:
# response = get_clips_form_submit(data)


#%%

# ai_response = sd_to_album.process_project_scenes(45, scenes_list=[390])



# %%
