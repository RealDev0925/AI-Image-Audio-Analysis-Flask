from dotenv import load_dotenv
import os
import asyncio
from supabase import create_client, Client
load_dotenv()  # Load environment variables from .env file

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)




# AUTHENTICATION
def sign_up_user(email: str, password: str):
    """Sign up a new user."""
    return supabase.auth.sign_up({"email": email, "password": password})


def sign_in_user(email: str, password: str):
    """Sign in an existing user."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


# MANAGING DATA
def insert_data(table: str, data: dict):
    """Insert data into a table."""
    resp = supabase.table(table).insert(data).execute()
    resp = resp.data
    resp = resp[0]
    return resp


def select_data(table: str, column: str, value: str):
    """Select data from a table based on a column value."""
    resp = supabase.table(table).select("*").eq(column, value).execute()
    resp = resp.data
    return resp


# table = "video_creator_projects"
# column = "project_name"
# value = "New w"

# sel = select_data(table, column, value)
# sel = sel.data
# print(type(sel))


from typing import List, Dict

def select_data_with_conditions(table: str, conditions: List[Dict[str, str]]):
    """Select data from a table based on multiple conditions."""
    
    query = supabase.table(table).select("*")
    
    for condition in conditions:
        column = condition.get("column")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if column and operator and value is not None:
            query = query.filter(column, operator, value)
    
    resp = query.execute()
    return resp.data


# # Define your conditions
# conditions = [
#     {"column": "project_id", "operator": "eq", "value": 3},
#     {"column": "status", "operator": "eq", "value": "Active"}
# ]

# # Call the function
# result = select_data_with_conditions("scenes", conditions)
# print(result)





def update_multiple_rows(table: str, data_list: list):
    responses = []
    for data in data_list:
        id = data.get('id')
        if id is None:
            responses.append({'error': 'Missing id'})
            continue

        new_data = {key: value for key, value in data.items() if key != 'id'}
        
        try:
            resp = update_data(table, id, new_data)
            if resp:
                responses.append(resp)
            else:
                responses.append({"error": f"Failed to update id {id}"})
        except Exception as e:
            responses.append({"error": f"Exception while updating id {id}: {str(e)}"})

    return {"responses": responses}



# [
#     {'scene_text': 'Text 1', 'id': 1},
#     {'scene_text': 'Text 2', 'id': 2},
#     # ... and so on
# ]


def update_data(table: str, id: int, new_data: dict):
    """Update data in a table by ID."""
    try:
        resp = supabase.table(table).update(new_data).eq("id", id).execute()
        resp = resp.data
        if resp:
            return resp
        else:
            return {"error": f"Failed to update id {id}"}
    except Exception as e:
        return {"error": f"Exception while updating id {id}: {str(e)}"}




def upsert_data(table: str, data: dict):
    """Insert or update data if it already exists."""
    resp = supabase.table(table).upsert(data).execute()
    resp = resp.data
    resp = resp[0]
    return resp







def delete_data(table: str, id: int):
    """Delete data by ID."""

    resp = supabase.table(table).delete().eq("id", id).execute()
    resp = resp.data
    resp = resp[0]
    return resp




async def invoke_function():
    """Invoke a Supabase function."""
    func = supabase.functions()
    return await func.invoke("hello-world", invoke_options={'body': {}})





# STORAGE
def download_file(bucket: str, file_name: str):
    """Download a file from storage."""
    return supabase.storage.from_(bucket).download(file_name)


def upload_file(bucket: str, file_path: str, file_content, file_type="text/plain"):
    """Upload a file to storage."""
    return supabase.storage.from_(bucket).upload(file_path, file_content, {"content-type": file_type})

# def upload_file_2():
#     # storage_client.from_("bucket").upload("/folder/file.png", file_object, {"content-type": "image/png"})
#     resp = supabase.storage.from_("media").upload("001.mp3", "/Users/georgebennett/Downloads/ElevenLabs_2023-11-14T13_32_26_Clyde_pre_s50_sb75_se0_b_m2.mp3", {"content-type": "audio/mpeg"})
#     print(resp)
# upload_file_2()

# storage_client.from_("bucket").upload("/folder/file.png", file_object, {"content-type": "image/png"})


# bucket="media"
# file_path="uploads/"
# file_content="p1.jpg"
# upload_resp = upload_file(bucket, file_path, file_content)
# print(upload_resp)



def delete_files(bucket: str, file_paths: list):
    """Delete files from storage."""
    return supabase.storage.from_(bucket).delete(file_paths)


def list_files(bucket: str):
    """List all files in a bucket."""
    return supabase.storage.from_(bucket).list()


def move_file(bucket: str, old_path: str, new_path: str):
    """Move and rename a file."""
    return supabase.storage.from_(bucket).move(old_path, new_path)


# Example usages
# if __name__ == "__main__":
#     sign_up_user("test_email@test.com", "test_password")
#     sign_in_user("test_email@test.com", "test_password")
#     insert_data("sample_table", {"key": "value"})
#     select_data("sample_table", "key", "value")
#     update_data("sample_table", 1, {"key": "new_value"})
#     upsert_data("sample_table", {"key": "value"})
#     delete_data("sample_table", 1)

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(invoke_function())
#     loop.close()

#     download_file("photos", "photo1.png")
#     upload_file("photos", "/user1/profile.png", "file_content_here")
#     delete_files("photos", ["old_photo.png", "image5.jpg"])
#     list_files("charts")
#     move_file("charts", "generic/graph1.png", "important/revenue.png")
