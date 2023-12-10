import re
import funcs_airtable
import funcs_utility
import funcs_open_ai_chat


def process_airtable_gpt_response(record_id):
    record_data = funcs_airtable.Get_Record_Data_From_ID("Actions", record_id)
    record_content = record_data.get("Content")

    # settings 
    record_settings =  record_data.get("Settings")
    if record_settings == None or record_settings == "":
        record_settings = None

    else:
        record_settings = funcs_utility.clean_up_variables(record_settings)

    # variables in the content
    unique_values = funcs_utility.find_unique_bracket_values(record_content)
    variables_content_dict = funcs_airtable.get_bracket_values_content_dict(unique_values)
    combined_content = funcs_utility.render_template_with_dict(record_content, variables_content_dict)

    # Update the record name only if it doesn't exist
    record_name = record_data.get("Name")

    if not record_name:
        # Generate a new name for the record
        update_name = funcs_utility.shorten_and_filter_string(combined_content, length=25)
        
        # Create the updated record dictionary
        new_record_dict = {"Name": update_name}

        # Update the record in Airtable
        funcs_airtable.Update_Record_Dict("Actions", record_id, new_record_dict)


    full_gpt_response = funcs_open_ai_chat.get_chat_response(combined_content, settings=record_settings)
    gpt_response = full_gpt_response['choices'][0]['message']['content']


    airtable_response =  funcs_airtable.Update_Record("Actions", record_id, "Response", gpt_response)    
    current_time = funcs_utility.current_time_london()
    response_formatted =  current_time + " :\n" + gpt_response + "\n===\n"
    airtable_response = funcs_airtable.append_data_to_column("Actions", record_id, "Response Log", response_formatted)




    return gpt_response

def save_airtable_response(record_id):
    record_data = funcs_airtable.Get_Record_Data_From_ID("Actions", record_id)
    record_response = record_data.get("Response")
    record_content = record_data.get("Content")
    record_name = record_data.get("Name")
    

    # Remove linked records
    update =  funcs_airtable.Update_Record("Actions", record_id, "Saved Response", [])
    

    # When saving, use the record name if it exists, otherwise use the response
    if record_name:
        saved_record_name = record_name
    else:
        saved_record_name = funcs_utility.shorten_and_filter_string(record_response, length=40)

        # also add name to the record
        update_name = funcs_utility.shorten_and_filter_string(record_response, length=25)
        New_Record_Dict = {"Name":update_name}
        update =  funcs_airtable.Update_Record_Dict("Actions", record_id, New_Record_Dict)


    # get the prompt used to make the response
    unique_values = funcs_utility.find_unique_bracket_values(record_content)
    variables_content_dict = funcs_airtable.get_bracket_values_content_dict(unique_values)
    combined_content = funcs_utility.render_template_with_dict(record_content, variables_content_dict)


    This_Table = "Saved"
    New_Record_Dict = {"Content":record_response, "Created From Prompt":combined_content, "Actions [Saved Response]":[record_id]}
    saved_record_id = funcs_airtable.search_and_add(This_Table, "Name", saved_record_name)
    print("saved_record_id", saved_record_id)
    # update =  funcs_airtable.Update_Record(This_Table, saved_record_id, "Saved Response", [])
    update =  funcs_airtable.Update_Record_Dict(This_Table, saved_record_id, New_Record_Dict)

    update_response = update["result"]["fields"]["Content"]
    update_response = "### Saved"

    return update_response



