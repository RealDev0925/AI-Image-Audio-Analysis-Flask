import openai

# Function to send API request to OpenAI and return the response
def send_request_to_openai(custom_dict):
    response = openai.ChatCompletion.create(
        model=custom_dict["model"],
        messages=custom_dict["messages"],
        temperature=custom_dict["temperature"],
        max_tokens=custom_dict["max_tokens"],
        top_p=custom_dict["top_p"],
        frequency_penalty=custom_dict["frequency_penalty"],
        presence_penalty=custom_dict["presence_penalty"]
    )
    return response


def prepare_custom_dict(input_data, settings):
    # Default settings for API request
    default_dict = {
        "model": "gpt-4",
        "temperature": 1.05,
        "max_tokens": 500,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "messages": []
    }
    
    # Initialize messages list and dict_to_send
    messages = []
    dict_to_send = default_dict.copy()

    # Update system message if present in settings
    if settings and "system" in settings:
        messages.append({"role": "system", "content": settings["system"]})

    # Filter settings to only include keys that are in default_dict
    if settings:
        filtered_settings = {k: settings[k] for k in settings if k in default_dict}
        dict_to_send.update(filtered_settings)

    # Add user message to messages list
    messages.append({"role": "user", "content": input_data})

    # Update dict_to_send with messages
    dict_to_send["messages"] = messages

    return dict_to_send



def get_chat_response(input, settings):
    # if settings dict does not contain key "do nothing"
    dict_to_send = prepare_custom_dict(input, settings)
    print("dict_to_send: ")
    print (dict_to_send)

    gpt_resp = send_request_to_openai(dict_to_send)
    print("gpt_resp: ")
    print (gpt_resp)
    return gpt_resp