from flask import Flask, request, jsonify, render_template, abort, send_from_directory, Blueprint

# from flask_cors import cross_origin
from flask_cors import CORS

# import funcs_flask
import funcs_supabase

import os

  

app = Flask(__name__)
# Uncomment this line to disable CORS for all routes
CORS(app)


# Register the blueprint
from blueprint_supabase import supabase_api
app.register_blueprint(supabase_api, url_prefix='/supabase')


import media
import funcs_elevenlabs
import random
import funcs_utility
import actions
import compose_2

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join('uploads', uploaded_file.filename))
    return 'File uploaded'


import transcriber
@app.route('/do_transcription', methods=['POST'])
def transcriber_run_app():
    request_data = request.get_json()
    # rd_str = str(request_data)
    # request_data = request.get_json()
    # print(request_data)
    result = transcriber.transcriber_run(request_data)
    # print(result)
    # res_str = str(result)
    response = { 'download_link': result }
    return jsonify(response)
 

# Route for serving files
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('uploads', filename, as_attachment=True)


import funcs_database

@app.route('/edit_scene/<int:scene_id>')
def edit_scene(scene_id):
    # scene_data = funcs_supabase.select_data("scenes", "id", scene_id)
    # scene_data = scene_data[0]
    scene_data = funcs_database.get_scene_and_clip_by_id(scene_id)

    final_clip_id = scene_data["final_clip"]
    final_clip_data = None
    if final_clip_id is not None:
        final_clip_data = funcs_supabase.select_data("media", "id", final_clip_id)[0]
        
    return render_template('edit_scene.html', scene_data=scene_data, media_data = final_clip_data)


# Library stuff

@app.route('/library')    
def show_album():
    return render_template('library.html', active_page="library")

@app.route('/search_album', methods=['GET'])
def search_album():
    # Create a dictionary from the request arguments
    args_dict = {key: request.args[key] for key in request.args}
    album_id = args_dict['album']
    type_filter = args_dict['type']
    source_filter = args_dict['source']
    album_results = actions.return_processed_media_list(album_id)
    # Return the dictionary as a JSON response
    return jsonify(album_results)


@app.route('/media_selected', methods=['GET'])
def media_selected():
    # Create a dictionary from the request arguments
    args_dict = {key: request.args[key] for key in request.args}
    media_id = args_dict['media']
    media_data = funcs_supabase.select_data("media", "id", media_id)[0]
    resp = actions.process_media_list_for_display(media_data, include_all_fields=True)[0]
    return render_template('media_selected.html', media_data=resp )

@app.route('/library_render', methods=['GET'])
def render_album_2():
    args_dict = {key: request.args[key] for key in request.args}
    album_id = args_dict['album']
    resp = actions.return_processed_media_list(album_id)    
    return render_template('library_render.html', album_data=resp )

# Library stuff

@app.route('/update_scene_data', methods=['POST'])
def update_scene_data():
    data = request.json

    # Extracting scene and new_data with error handling
    scene = data.get('scene')
    new_data = data.get('new_data')

    if scene is None or new_data is None:
        return jsonify({'error': 'Missing scene or new data'}), 400

    # Assuming funcs_supabase.update_data handles the update logic
    resp = funcs_supabase.update_data("scenes", scene, new_data)

    return jsonify(resp)

@app.route('/scene_actions', methods=['GET'])
def scene_actions():
    args_dict = {key: request.args[key] for key in request.args}

    if args_dict["action"] == "create":
        project_id = args_dict["project_id"]
        scene_id = actions.create_new_scene(project_id)
        return jsonify({"scene_id": scene_id})
    

    elif args_dict["action"] == "delete":
        scene_id = args_dict["scene_id"]
        resp = funcs_supabase.update_data("scenes", scene_id, {"status": "Deleted"})
        return jsonify(resp)
    

import process_forms
@app.route('/process_edit_scene', methods=['POST'])
def process_edit_scene():
    data = request.json
    print(data)
    processed_data = process_forms.js_to_db_format(data)
    scene_id = processed_data.get('scene_id')
    # Create a copy of the dictionary
    new_dict = processed_data.copy()
    # Remove 'scene_id' from the new dictionary
    new_dict.pop('scene_id', None)  # The second argument prevents KeyError if 'scene_id' is not in the dictionary
    resp = funcs_supabase.update_data("scenes", scene_id, new_dict)
    return jsonify(resp)




# Form to do things in a selected project
@app.route('/project_actions', methods=['GET'])
def project_actions():
    args_dict = {key: request.args[key] for key in request.args}
    return render_template('project_actions.html', data=args_dict)

@app.route('/project_actions_form', methods=['POST'])
def project_actions_form():
    data = request.json
    processed_data = process_forms.js_to_db_format(data)
    processed_data =  process_forms.execute_project_actions(processed_data)
    return jsonify(processed_data)



@app.route('/process_forms', methods=['POST'])
def process_forms_def():
    data = request.json
    processed_data = process_forms.process_form(data)
    return jsonify(processed_data)



# Render all pages in this folder... 
@app.route('/pages/<path:page_name>')
def pages(page_name):
    if '..' in page_name or page_name.startswith('/'):
        abort(404)  # Basic security check against directory traversal

    args_dict = {key: request.args[key] for key in request.args}
    full_path = os.path.join('pages/', page_name + '.html')
    # print(full_path)
    if os.path.exists(os.path.join('templates', full_path)):
        return render_template(full_path, data=args_dict)
    else:
        abort(404)

@app.route('/get_clips', methods=['GET'])
def get_clips():
    # Debug: Print all incoming arguments
    print("Incoming args:", request.args)

    # Check if project_id is present in the arguments
    project_id = request.args.get("project_id")
    if not project_id:
        return "Project ID not provided", 400

    # Retrieve active scenes (assuming actions.get_active_scenes() is a valid function)
    active_scenes = actions.get_active_scenes(project_id)


    # Ensure args_dict contains all necessary data
    args_dict = {key: request.args[key] for key in request.args}

    args_dict["selected_scene"] = int(args_dict["selected_scene"]) if "selected_scene" in args_dict else None


    return render_template('get_clips_form.html', data=args_dict, active_scenes=active_scenes)

# @app.route('/process_forms', methods=['POST'])
# def project_actions_form():
#     data = request.json
#     processed_data = process_forms.js_to_db_format(data)


# List of all projects
@app.route('/projects')
def route_projects():
    projects_list = funcs_supabase.select_data("video_creator_projects", "status", "Active")

    # Apply friendly_time to the 'created_at' value if it exists
    for item in projects_list:
        if 'created_at' in item:
            item['created_at'] = funcs_utility.friendly_date(item['created_at'])

    # projects_list = [
    #     {'id': '1', 'name': 'Project A', 'created_at': '2023-01-01'},
    #     {'id': '2', 'name': 'Project B', 'created_at': '2023-02-15'},
    #     # Add more projects as needed
    # ]

    # Sorting the list by 'id' in descending order
    sorted_projects = sorted(projects_list, key=lambda x: int(x['id']), reverse=True)
    return render_template('projects.html', projects=sorted_projects, active_page = "projects")



# delete a project
@app.route('/delete_project/<int:project_id>', methods=['GET'])
def delete_project(project_id):
    # There's no need to fetch project_id from request.args since you already have it from the route

    # Assuming funcs_supabase.update_data() returns a success or failure response, you can do:
    success = funcs_supabase.update_data("video_creator_projects", project_id, {"status": "Deleted"})
    
    if success:
        return jsonify({"success": "Project Deleted"})
        
    else:
        return jsonify({"error": "Failed to delete project"}), 400

# Edit a project
@app.route('/project/<int:project_id>')
def edit_project(project_id):
    return render_template('project.html', project_id=project_id, active_page="projects", subpage="scenes")

@app.route('/compose/<int:project_id>')
def compose(project_id):
    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
    scenes_list = actions.get_active_scenes(project_id)

    return render_template('compose.html', project_id=project_id, project_data=project_data,scenes_data=scenes_list, active_page="projects", subpage="compose")

# Create a project
@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.json
    project_name = data['project_name']
    
    success = funcs_supabase.insert_data("video_creator_projects", {"project_name": project_name})
    
    if success:
        return jsonify({"success": "Project Created"})
    else:
        return jsonify({"error": "Failed to create project"}), 400


@app.route('/upload_media')
def upload_media_1():    
    return render_template('upload_media.html')

# The buttons on edit project page 

@app.route('/split_text/<int:project_id>')
def split_text(project_id):
    return render_template('split_text.html', project_id=project_id)



@app.route('/split_text_api', methods=['POST'])
def split_text_2():
    data = request.json
    article = data['article']
    project_id = data["project_id"]  # Retrieve project_id
    result = actions.split_article_into_scenes(project_id, article)
    return jsonify({"result": article})
 
@app.route('/get_prompts', methods=['GET'])
def get_prompts_update():
    project_id = request.args.get('project_id')
    project_id = int(project_id)
    new_prompts = actions.update_theme_keywords(project_id)
    return jsonify({"result": new_prompts})

# Get Stable Diffusion Prompts
@app.route('/button3/<int:project_id>')
def button3(project_id):
    return render_template('drawer_button_3.html', project_id=project_id)

# on submit in drawer_button_3.html SD Prompts. 
@app.route('/button3_api', methods=['POST'])
def button3_api():
    data = request.json
    return jsonify({"result": "data"})


# # Generate SD Images for all scenes
@app.route('/button4/<int:project_id>')
def button4(project_id):
    return render_template('drawer_button_4.html', project_id=project_id)



import funcs_elevenlabs
# Get Audio File
@app.route('/text_to_speech_form/<int:project_id>')
def button5(project_id):
    el_voices = funcs_elevenlabs.get_voices()
    el_voices = el_voices['voices']
    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]


    return render_template('text_to_speech_form.html', project_id=project_id, voices=el_voices, project_data=project_data)

# audio file 
@app.route('/text_to_speech_api', methods=['GET'])
def button5_api():
    project_id = request.args.get('project_id')
    project_id = int(project_id)
    voice_id = request.args.get('voice_id')
    stability = request.args.get('stability')
    similarity_boost = request.args.get('clarity')
    style = request.args.get('style')
    use_speaker_boost = request.args.get('speakerBoost')
    use_speaker_boost = True if use_speaker_boost == 'on' else False
    # {stability: '0.15', clarity: '0.83', style: '0.67', speakerBoost: 'on', voice_id: 'D38z5RcWu1voky8WS1ja', …}
    
    scenes_list = actions.get_active_scenes(project_id)
    joined_scenes_text = ""
    for scene in scenes_list:
        scene_text = scene["scene_text"]
        joined_scenes_text = joined_scenes_text + scene_text + " "


    audio_bin = funcs_elevenlabs.text_to_speech(voice_id, joined_scenes_text, stability, similarity_boost, style, use_speaker_boost)
    rand_no = random.randint(0, 1000000000000000)
    filename = f"{rand_no}.mp3"
    
    url = media.upload_to_supabase("media", audio_bin, is_binary=True, custom_filename=filename)
    
    new_data_dict = {"speech_audio": url}
    funcs_supabase.update_data("video_creator_projects", project_id, new_data_dict)

    # delete existing words_list for project
    new_data_dict = {"words_list": None}
    funcs_supabase.update_data("video_creator_projects", project_id, new_data_dict)

    # save new words_list for project
    # transcriber.save_word_list_to_db(project_id)

    # update scene timings
    # scene_timings.process(project_id)

    


    return jsonify({"result": url})


# Get subtitles file 
# @app.route('/button6/<int:project_id>')
# def button6(project_id):
#     project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
#     return render_template('drawer_button_6.html', project_id=project_id, project_data=project_data)


@app.route('/get_subs_api', methods=['GET'])
def get_subs_api():
    project_id = request.args.get('project_id')
    project_id = int(project_id)
    characters = request.args.get('char_count')
    url = transcriber.get_subs_for_project(project_id,characters )
    return jsonify({"result": url})

@app.route('/words_list/<int:project_id>')
def words_list_page(project_id):
    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
    return render_template('words_list.html', project_id=project_id, project_data=project_data)


import transcriber
@app.route('/get_words_list', methods=['GET'])
def get_words_list():
    project_id = request.args.get('project_id')

    if request.args.get('get_new') == "true":
        transcriber_output= transcriber.save_word_list_to_db(project_id)
        print(transcriber_output)


        words_list_from_db = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]["words_list"]
        return jsonify(words_list_from_db)

    words_list_from_db = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]["words_list"]

    if words_list_from_db is None:
        transcriber.save_word_list_to_db(project_id)
        words_list_from_db = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]["words_list"]

    return jsonify(words_list_from_db)


@app.route ('/update_words_list', methods=['POST'])
def update_words_list():
    data = request.json
    project_id = data["project_id"]
    words_list = data["words_list"]
    new_data_dict = {"words_list": words_list}
    db_resp = funcs_supabase.update_data("video_creator_projects", project_id, new_data_dict)
    new_words_list = db_resp[0]["words_list"]
    return jsonify(new_words_list)

import scene_timings
@app.route('/scene_words_len_match', methods=['GET'])
def scene_words_len_match():
    project_id = request.args.get('project_id')
    project_id = int(project_id)
    resp = scene_timings.scene_words_len_match(project_id)
    return jsonify({"result": resp})









import comfyui
import funcs_jinja
import sd_images
@app.route('/sd_input', methods=['GET'])
def sd_input():
    data = request.args
    # workflows = funcs_supabase.select_data("sd_workflows", "status", "Active")
    return render_template('sd_input.html', data=data)


@app.route('/sd_workflows', methods=['GET'])
def sd_workflows():
    workflows = funcs_supabase.select_data("sd_workflows", "status", "Active")
    for wf in workflows:
        # Initialize inputs as an empty list
        inputs = wf.get("inputs", [])
        # Ensure inputs is always a list, if it's None or not a list, handle appropriately
        if not isinstance(inputs, list):
            inputs = []
        # If inputs is empty, extract variables from the template
        if not inputs:
            template = wf.get("workflow_template")
            extracted_inputs = funcs_jinja.extract_variables_from_template(template)
            # Ensure that extracted_inputs is a list before extending
            if isinstance(extracted_inputs, list):
                inputs.extend(extracted_inputs)
            else:
                inputs.append(extracted_inputs)
        # Assign the list back to the workflow dict
        wf["inputs"] = inputs

    return jsonify(workflows)


@app.route('/gen_sd_images', methods=['POST'])
def sd_workflow_run():
    data = request.json
    print("data received")
    print(data)

    processed_data = process_forms.js_to_db_format(data)
    print("format for sd_images.get_images")
    print(processed_data)
    resp = sd_images.get_images(processed_data)
    print(resp)
    return jsonify(resp)

@app.route('/gen_sd_images_2', methods=['POST'])
def sd_workflow_run_2():
    data = request.json
    print("data received")
    print(data)
    resp = sd_images.save_and_run(data)
    return jsonify(resp)


@app.route('/sd_models')
def sd_models():
    models = comfyui.get_models()
    return jsonify(models)


import re
@app.route('/save_sd_settings', methods=['POST'])
def save_sd_settings():
    data = request.json
    print("data received")
    print(data)

    rsp = sd_images.save_sd_settings(data)

    # prompt_variables_dict = {}
    # for item in data:
    #     if 'prompt_variables' in item['name']:
    #         parts = item['name'].split('[')
    #         position = int(parts[1].split(']')[0])
    #         key_or_value = parts[2].split(']')[0]
    #         if position not in prompt_variables_dict:
    #             prompt_variables_dict[position] = {}            
    #         prompt_variables_dict[position][key_or_value] = item['value']

    # prompt_variables = [val for key, val in sorted(prompt_variables_dict.items())]
    # cleaned_list = []  # This will be our new list without the 'prompt_variables'
    # for item in data:
    #     if 'prompt_variables' not in item['name']:
    #         cleaned_list.append(item)
    # cleaned_list.append({'name': 'prompt_variables', 'value': prompt_variables})
    
    
    # project_id = 38
    # update = funcs_supabase.update_data("video_creator_projects", project_id, {"sd_settings": cleaned_list})


    return jsonify(rsp)


@app.route('/load_sd_settings', methods=['GET'])
def load_sd_settings():
    project_id = request.args.get('project_id')
    project_id = int(project_id)
    project_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0]
    sd_settings = project_data.get("sd_settings")
    print("sd_settings")
    print(sd_settings)
    return jsonify(sd_settings)




if __name__ == '__main__':
    app.run(debug=True)
