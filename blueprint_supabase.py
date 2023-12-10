from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import funcs_supabase


load_dotenv()  # Load environment variables from .env file

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

supabase_api = Blueprint('supabase_api', __name__)

# AUTHENTICATION
@supabase_api.route('/signup', methods=['POST'])
def sign_up_user():
    data = request.json
    email = data['email']
    password = data['password']
    return jsonify(supabase.auth.sign_up({"email": email, "password": password}))

@supabase_api.route('/signin', methods=['POST'])
def sign_in_user():
    data = request.json
    email = data['email']
    password = data['password']
    return jsonify(supabase.auth.sign_in_with_password({"email": email, "password": password}))

# MANAGING DATA
@supabase_api.route('/insert', methods=['POST'])
def insert_data():
    data = request.json
    table = data['table']
    payload = data['data']
    return jsonify(supabase.table(table).insert(payload).execute())

@supabase_api.route('/select', methods=['GET'])
def select_data():
    table = request.args.get('table')
    column = request.args.get('column')
    value = request.args.get('value')
    resp = supabase.table(table).select("*").eq(column, value).execute()
    resp = resp.data
    return jsonify(resp)



# get all from table 
# response = supabase.table('countries').select("*").execute()





# @supabase_api.route('/update', methods=['PUT'])
# def update_data():
#     data = request.json
    
#     table = data['table']
#     id = data['id']
#     new_data = data['new_data']
#     resp = supabase.table(table).update(new_data).eq(id, 1).execute()
#     resp = resp.data
#     return jsonify(resp)

#     # data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()

#     # return jsonify(supabase.table(table).update(new_data).eq("id", id).execute())



@supabase_api.route('/update', methods=['POST'])
def update():
    """Update data in a table by ID."""
    payload = request.json
    table = payload['table']
    id = payload['id']
    new_data = payload['new_data']
    response = supabase.table(table).update(new_data).eq("id", id).execute()
    
    response = response.data
    return response




@supabase_api.route('/bulk_update', methods=['POST'])
def bulk_update():
    """Bulk update data in a table."""
    payload = request.json
    table = payload['table']
    records = payload['records']  # Expecting a list of records to update
    
    responses = []
    for record in records:
        id = record['id']
        new_data = record['new_data']
        response = supabase.table(table).update(new_data).eq("id", id).execute()
        
        # Assuming the response has a "data" attribute that is JSON-serializable
        if response.data:
            responses.append(response.data)
        else:
            responses.append({"error": "Failed to update id {}".format(id)})
    
    return jsonify({"responses": responses})

# {
#     "table": "your_table_name",
#     "records": [
#         {"id": 1, "new_data": {"field1": "new_value1", "field2": "new_value2"}},
#         {"id": 2, "new_data": {"field1": "new_value3", "field2": "new_value4"}},
#         {"id": 3, "new_data": {"field1": "new_value5", "field2": "new_value6"}}
#     ]
# }




# Echo route that takes a POST request and returns the same data back
@supabase_api.route('/echo', methods=['POST'])
def echo():
    data = request.json
    return jsonify(data)



# def update_data(table: str, id: int, new_data: dict):
#     """Update data in a table by ID."""
#     return 'ss'


# @supabase_api.route('/test', methods=['POST'])
# def test():
#     try:
#         # Parse JSON data from request
#         data = request.json
#         table = data['table']
#         id = data['id']
#         new_data = data['new_data']


#         test_resp = {"table is": table, "id is": id, "new_data is": new_data}

#     except Exception as e:
#         return jsonify({'error': 'Invalid JSON'}), 400

#     new_data = {"project_name": "Indonesia"}
#     print(type(id))
#     print(type(new_data))
#     print(type(table))


    # resp = supabase.table(table).update(new_data).eq("id", id).execute()

    # # Respond with the received JSON data
    # return jsonify({'received': resp}), 200




@supabase_api.route('/upsert', methods=['POST'])
def upsert_data():
    data = request.json
    table = data['table']
    payload = data['data']
    return jsonify(supabase.table(table).upsert(payload).execute())

@supabase_api.route('/delete', methods=['DELETE'])
def delete_data():
    data = request.json
    table = data['table']
    id = data['id']
    return jsonify(supabase.table(table).delete().eq("id", id).execute())

# STORAGE
@supabase_api.route('/download', methods=['GET'])
def download_file():
    bucket = request.args.get('bucket')
    file_name = request.args.get('file_name')
    return jsonify(supabase.storage.from_(bucket).download(file_name))

@supabase_api.route('/upload', methods=['POST'])
def upload_file():
    data = request.json
    bucket = data['bucket']
    file_path = data['file_path']
    file_content = data['file_content']
    return jsonify(supabase.storage.from_(bucket).upload(file_path, file_content))

@supabase_api.route('/delete_files', methods=['DELETE'])
def delete_files():
    data = request.json
    bucket = data['bucket']
    file_paths = data['file_paths']
    return jsonify(supabase.storage.from_(bucket).delete(file_paths))

@supabase_api.route('/list_files', methods=['GET'])
def list_files():
    bucket = request.args.get('bucket')
    return jsonify(supabase.storage.from_(bucket).list())

@supabase_api.route('/move_file', methods=['PUT'])
def move_file():
    data = request.json
    bucket = data['bucket']
    old_path = data['old_path']
    new_path = data['new_path']
    return jsonify(supabase.storage.from_(bucket).move(old_path, new_path))





@supabase_api.route('/active_scenes_for_project', methods=['GET'])

def active_scenes_for_project():

    project_id = request.args.get('project_id')


    # Define your conditions
    conditions = [
    {"column": "project_id", "operator": "eq", "value": project_id},
    {"column": "status", "operator": "eq", "value": "Active"}
    ]

    # Call the function
    result = funcs_supabase.select_data_with_conditions("scenes", conditions)
    return jsonify(result)



