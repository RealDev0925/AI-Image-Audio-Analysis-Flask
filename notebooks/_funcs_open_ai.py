import config
import openai
import json
import database_stuff
import tiktoken

openai.api_key= config.openai_key

def process_saved_outputs():
    """Reads the saved_outputs.jsonl file and returns a string of all the prompts and completions."""

    # read the jsonl file
    with open("saved_outputs.jsonl", 'r') as f:
        lines = f.readlines()

    # create a list of dictionaries
    lines = [json.loads(line) for line in lines]

    # create a list of prompts and completions
    prompts = [line["prompt"] for line in lines]
    completions = [line["completion"] for line in lines]

    # combine the prompts and completions into one list
    prompts_and_completions = [prompt + " " +completion for prompt, completion in zip(prompts, completions)]

    # join the list of prompts and completions into one string
    prompts_and_completions = "\n".join(prompts_and_completions)

    return prompts_and_completions




def get_prepend_completions(prompt_match=""):
    """gets the completions from the database and returns a string of all the prompts and completions."""

    data = database_stuff.read_data("completions")
    final = ""
    for line in data:
        if line["prompt"] and line ["completion"]:
            prompt = line["prompt"]
            completion = line["completion"]

            if prompt_match:
                if prompt_match not in prompt:
                    continue

            d = prompt + " " + completion
            final = final + d + "\n"
    # remove empty line from the end 
    final = final[:-1]

    return final

# d = get_prepend_completions(prompt_match="write a pattern interrupt about social approval ->")
# print(d)



def complete(**kwargs):
    d_input = kwargs
    d_defaults = {"model":"text-davinci-003","prompt":"","temperature":1,"max_tokens":256,"top_p":1,"frequency_penalty":0,"presence_penalty":0}
    open_ai_args = ["model", "prompt", "suffix", "max_tokens", "temperature", "top_p", "n", "stream", "logprobs", "echo", "stop", "presence_penalty", "frequency_penalty", "best_of", "logit_bias", "user"]


    # from d_input, remove any key-value pairs which have empty values
    for key in list(d_input.keys()):
        if d_input[key] == "" or d_input[key] == "None" or d_input[key] == None or d_input[key] == []:
            del d_input[key]


    # if n is present and best of is present, make sure the number of best of is equal to or higher than n
    if "n" in d_input:
        if "best_of" in d_input:
            if d_input["best_of"] < d_input["n"]:
                d_input["best_of"] = d_input["n"]

    # output dictionary with default values if they were missing from the input 
    d_output = {**d_defaults, **d_input}


    # in d_output, check if key "suffix" exists, if it does, remove the key "echo" if it exists, append it back after the response... 
    if "suffix" in d_output:
        if "echo" in d_output:
            del d_output["echo"]

    # Check if Stop is an empty list, if it is, remove it from the dictionary
    if "stop" in d_output:
        if d_output["stop"] == [] or d_output["stop"] == "None" or d_output["stop"] == None or d_output["stop"] == "":
            del d_output["stop"]

    # if "prepend_completions" is a key in d_output, and the value is not "None"
    if "prepend_completions" in d_output:
        # print("prepend_completions")
        
        if d_output["prepend_completions"] != "None":
            initial_prompt = d_output.get("prompt")
            if d_output["prepend_completions"] == "Prompt Match":
                prepend_completions_output = get_prepend_completions(prompt_match=initial_prompt)
        
            elif d_output["prepend_completions"] == "All":
                prepend_completions_output = get_prepend_completions()
    
            final_prompt = prepend_completions_output + "\n" + initial_prompt
            # replace the value of the key "prompt" in d_output with the value of final_prompt
            d_output["prompt"] = final_prompt


    # from the dictionary d_output, if a key is not in the list of open_ai_args, remove it from the dictionary
    # Removes all keys not required for openAI
    for key in list(d_output.keys()):
        if key not in open_ai_args:
            del d_output[key]

    # print("Sending this to openAI:")
    # print(d_output)
    response = openai.Completion.create(**d_output)
    # print(response)


    responses_list = []
    choices = response['choices']
    for choice in choices:
        response = choice['text']
    #     response = choice['text'].strip()
        responses_list.append(response)

    # remove duplicates
    responses_list = list(dict.fromkeys(responses_list))

    # if suffix was present append prompt to each item in the list if echo was present
    if "suffix" in d_output:
        if d_input.get("echo") == True:
            responses_list = [d_output["prompt"] + item  for item in responses_list]

    # print(responses_list)
    return responses_list


# testing = complete(prompt="write a pattern interrupt about social approval ->", prepend_completions=None)
# print(testing)












def chat():

    # ask for user input

    while True:

        user_input = input("You: ")

        if user_input:

            if user_input == "close":
                break

            # if variable response exists in local scope
            if "response" in locals():
                # print(response + user_input)
                response = complete(prompt = response + user_input)            
    
            else:
                response = complete(prompt = user_input)
    
            print("Bot: " + response)

        else:
            print("Please enter a valid input")



def edit(**kwargs):

    defaults = {"model":"text-davinci-edit-001","input":"","instruction":"Fix the spelling mistakes","n":1,"temperature":1,"top_p":1}
    d_input = kwargs

    # make a list of unique keys from the defaults dictionary
    open_ai_args = list(defaults.keys())
    # print(open_ai_args)
    # ['model', 'input', 'instruction', 'n', 'temperature', 'top_p']
    

    # from d_input, remove any key-value pairs which have empty values
    for key in list(d_input.keys()):
        if d_input[key] == "" or d_input[key] == "None" or d_input[key] == None or d_input[key] == []:
            del d_input[key]

    # output dictionary with default values if they were missing from the input
    d_output = {**defaults, **d_input}


    # from the dictionary d_output, if a key is not in the list of open_ai_args, remove it from the dictionary
    # Removes all keys not required for openAI
    for key in list(d_output.keys()):
        if key not in open_ai_args:
            del d_output[key]

    print("Sending this to openAI:")
    print(d_output)

    response = openai.Edit.create(**d_output)


    responses_list = []
    choices = response['choices']
    for choice in choices:
        response = choice['text']
        responses_list.append(response)
    responses_list = list(dict.fromkeys(responses_list))
    return responses_list
 
# edit_output = edit(input="Place this bitter substance in your mouth every morning to rapidly balance blood sugar levels.", instruction="Rewrite this for weight loss instead of diabetes.", n=10)
# print(edit_output)


def insert(input):

    prompt = input.split("[insert]")[0]
    suffix = input.split("[insert]")[1]

    # prompt="I like big "
    # suffix=" and i cannot lie"
    # print(prompt)
    # print(suffix)

    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    suffix=suffix,
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    resp =  response['choices'][0]['text'].strip()
    return prompt + resp

# insert_test = insert("I like big [insert] and i cannot lie")
# print(insert_test)

def list_models():
    resp = openai.Model.list()

    # reorder list by created
    resp.data.sort(key=lambda x: x.created, reverse=True)
    model_list = []
    for model in resp.data:
        # print(model)
        model_list.append(model.id)
    return model_list

# models = list_models()
# print(models)

def list_fine_tunes():
    ft = openai.FineTune.list()
    ft_list = []

    for f in ft.data:
        q = f.get("fine_tuned_model")
        # print(q)
        ft_list.append(q)
    return ft_list
        
# print(list_fine_tunes())


def get_models_filtered():
    all_models = list_models()
    # print(all_models)


    filter_by_word = ["text-davinci-003", "text-curie-001", "text-ada-001", "code-davinci-002"]
    # for each model in all_models, check if they contain any of the words in filter_by_word
    
    models_filtered= []
    
    for model in all_models:
        # print(model)
        for word in filter_by_word:
            if word in model:
                print(model)
                models_filtered.append(model)    


    all_fine_tunes = list_fine_tunes()
    for fine_tune in all_fine_tunes:
        # print(fine_tune)
        models_filtered.append(fine_tune)


    return models_filtered

# models = get_models_filtered()
# print(models)



def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# num_tokens_from_string("tiktoken is great!", "cl100k_base")



from openai.embeddings_utils import get_embedding, cosine_similarity
def get_embeddings(input = ""):
    """Get the vector embeddings from openAI for a given input string."""

    response = openai.Embedding.create( 
        input= input,
        model="text-embedding-ada-002"
    )

    embeddings = response['data'][0]['embedding']
    return embeddings


def get_similarity(input1, input2):
    """Get the similarity between two strings."""

    embedding1 = get_embeddings(input1)
    embedding2 = get_embeddings(input2)

    similarity = cosine_similarity(embedding1, embedding2)
    return similarity

# similarity = get_similarity("I like large bottoms", "I like big butts")
# print


def main ():
    ...
    # print("Hello World")
    # test = complete(prompt = "Hello how are you? ")
    # print(test)
    # chat()


if __name__ == "__main__":
    main()