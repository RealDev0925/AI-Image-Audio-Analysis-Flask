import os
import re


# Function to read .env file and set environment variables
def load_dotenv(dotenv_path=".env"):
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            os.environ[key] = value

# Call the function specifying the path to your .env file
load_dotenv()

# Now you can use the environment variable
# api_key = os.environ.get("OPENAI_API_KEY")

from datetime import datetime
import pytz



## Function to get the current time in London
def current_time_london():
    # Define the time zone for London
    london_tz = pytz.timezone('Europe/London')
    
    # Get the current time in UTC and convert it to London time
    utc_now = datetime.now(pytz.utc)
    london_time = utc_now.astimezone(london_tz)
    
    # Format the time string
    formatted_time = london_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return formatted_time

# Example usage
# print(current_time_london())


# def friendly_date (timestamp):
#     # Parse the timestamp
#     timestamp = datetime.fromisoformat(timestamp)

#     # Format the timestamp into the desired format
#     friendly_date = timestamp.strftime('%Y-%b-%d %H:%M')

from datetime import datetime

def friendly_date(timestamp):
    try:
        # Parse the timestamp
        timestamp = datetime.fromisoformat(timestamp)

        # Format the timestamp into the desired format
        friendly_date_str = timestamp.strftime('%Y-%b-%d %H:%M')

        return friendly_date_str
    except ValueError as e:
        # Handle the case where the timestamp is not in the expected format
        print(f"Error parsing timestamp: {e}")
        return None  # or return a default value or raise an exception, depending on your use case


import re
def find_unique_bracket_values(input_string):
    pattern = r'{{(.*?)}}'
    found_values = re.findall(pattern, input_string)
    unique_values = list(set(found_values))
    return unique_values


from jinja2 import Template

def correct_template_str(template_str, input_dict):
    for key in input_dict.keys():
        # Replace non-alphanumeric characters with underscores
        corrected_key = re.sub(r'[^a-zA-Z0-9]', '_', key)
        template_str = template_str.replace("{{" + key + "}}", "{{" + corrected_key + "}}")
    return template_str


import re

def render_template_with_dict(template_str, input_dict):
    # Correct the template string
    template_str = correct_template_str(template_str, input_dict)

    # Create a Jinja2 template object
    template = Template(template_str)

    # Replace None values with an empty string or any other default value
    for key, value in input_dict.items():
        if value is None:
            input_dict[key] = ''

    # Jinja2 template variables cannot contain non-alphanumeric characters,
    # so we need to replace them
    corrected_dict = {re.sub(r'[^a-zA-Z0-9]', '_', key): value for key, value in input_dict.items()}

    # Render the template
    return template.render(**corrected_dict)

# Example usage
# template = """
# AVATAR:
# {{Generated x}}
# ---
# {{offer}}
# """
# input_dict = {'Generated x': 'qweqwe', 'offer': 'asw'}
# result = render_template_with_dict(template, input_dict)
# print(result)


def shorten_and_filter_string(input_string, length=50):
    # Step 1: Remove spaces from the beginning and the end
    input_string = input_string.strip()
    
    # Step 2: Filter string to only include letters, numbers, and spaces
    filtered_string = "".join(char for char in input_string if char.isalnum() or char.isspace())
    
    # Step 3: Shorten the string to the first 100 characters
    shortened_string = filtered_string[:length]

    shortened_string = shortened_string.strip()
    
    return shortened_string

# # Test the function
# test_string = "   This is a sample string! It contains various types of characters: 123, !@#   "
# result = shorten_and_filter_string(test_string)
# print(f"The original string: '{test_string}'")
# print(f"The modified string: '{result}'")




def clean_up_variables(raw_string):
    # Normalize the string by replacing newlines and multiple spaces with a single space
    normalized_string = re.sub(r'\s+', ' ', raw_string).strip()
    
    # Add a comma at the end to make the pattern consistent
    if not normalized_string.endswith(','):
        normalized_string += ','
    
    # Find key-value pairs, but be tolerant of missing commas by looking ahead for the next key
    key_value_pairs = re.findall(r'(\w+)\s*=\s*("[^"]*"|\d+|\d+\.\d+|\w+)(?:,|\s+(?=\w+\s*=))', normalized_string)
    
    # Create a dictionary to hold the cleaned variables
    clean_dict = {}
    for key, value in key_value_pairs:
        # Strip extra whitespace from the keys and make them lowercase
        key = key.strip().lower()
        
        # If the value is numeric, convert it
        if value.isdigit():
            value = int(value)
        # If the value looks like a float, convert it
        elif re.fullmatch(r'\d+\.\d+', value):
            value = float(value)
        # If the value is wrapped in quotes, unwrap it
        elif value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        clean_dict[key] = value
    
    return clean_dict




# Example usages
# raw_string1 = 'role    =     "You are a badass motherfucker"  temperature=1  max_tokens=422,  top_p=1,  frequency_penalty=0,  presence_penalty=0, '
# raw_string2 = 'role = "Another role", temperature=1,'
# raw_string3 = 'role = "Yet another role"\n temperature = 2\n'

# print(clean_up_variables(raw_string1))
# print(clean_up_variables(raw_string2))
# print(clean_up_variables(raw_string3))




def combine_dict_and_string(my_dict, my_string, my_string_key ):
    # Initialize an empty dictionary if my_dict is None
    if my_dict is None:
        my_dict = {}

    # Add the new string to the dictionary
    my_dict[my_string_key] = my_string

    return my_dict