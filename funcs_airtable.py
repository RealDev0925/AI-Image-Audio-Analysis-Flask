import os
import json
from pyairtable import Table
from pyairtable.formulas import match


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read API key from environment variable
airtable_api_key = os.getenv("AIRTABLE_API_KEY")

if airtable_api_key is None:
    print("Warning: AIRTABLE_API_KEY not found in environment. Functions may not work as expected.")

base = "appTydARXWr2jFYRf"
table_name = "Actions"
table = Table(airtable_api_key, base, table_name)




def record_exists(table_name, Name_column, Name):
    table = Table(airtable_api_key, base, table_name)
    records = table.all()
    for record in records:
        if record['fields'].get(Name_column) == Name:
            return True
    return False

def search_and_add(table_name, Name_column, Name):
    table = Table(airtable_api_key, base, table_name)
    if not record_exists(table_name, Name_column, Name):
        New_Record_Dict = {Name_column: Name}
        resp = table.create(New_Record_Dict)
        print(f"Added new record with name: {Name}")
        return resp['id']

    counter = 1
    while True:
        new_name = f"{Name}_{counter}"
        if not record_exists(table_name, Name_column, new_name):
            New_Record_Dict = {Name_column: new_name}
            resp = table.create(New_Record_Dict)
            print(f"Added new record with name: {new_name}")
            return resp['id']
        counter += 1

# Example usage
# table_name = "Saved"
# Name_column = "Name"  # Replace with the actual column name where you want to search/add the Name
# Name = "JohnDoe"  # Replace with the name you want to search for/add

# id = search_and_add(table_name, Name_column, Name)
# print(id)






def Get_Record_Info(Find_in_Table, Find_In_Column, Find_This_Value, Return_Value_From_Column="id"):
    try:
        table = Table(airtable_api_key, base, Find_in_Table)
        records = table.all()
        for record in records:
            if record["fields"].get(Find_In_Column) == Find_This_Value:
                if Return_Value_From_Column == "id":
                    return record["id"]
                else:
                    return record["fields"].get(Return_Value_From_Column, None)
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# # Example usage:
# Find_in_Table = "Saved"
# Find_In_Column = "Name"
# Find_This_Value = "Generate Casino Avatar Prompt"
# Return_Value_From_Column = "Content"
# matched_data = Get_Record_Info(Find_in_Table, Find_In_Column, Find_This_Value, Return_Value_From_Column)
# print("Matched Data:", matched_data)




# Get All Record Data from ID
def Get_Record_Data_From_ID(Find_in_Table, RecordID):
    table = Table(airtable_api_key, base, Find_in_Table)
    records = table.get(RecordID)
    records = records["fields"]
    return records


# Get All Record Data from ID
# record_id = "recW0NVYMNAGJAeTZ"  # Replace with the actual record ID you are interested in
# in_table = "Actions"
# data = Get_Record_Data_From_ID(in_table, record_id)
# print(data)


def append_data_to_column(table_name, record_id, column_name, new_data, reverse_order=True):

    table = Table(airtable_api_key, base, table_name)

    # Fetch the existing record by its ID
    existing_record = table.get(record_id)
    
    # Fetch the existing value from the specified column (field)
    existing_value = existing_record.get("fields", {}).get(column_name, "")
    
    # strip only the begining spaces and newlines
    existing_value = existing_value.lstrip()
    
    if reverse_order:
        # Append the new data to the existing value
        updated_value = new_data + existing_value
    else:
        # Append the new data to the existing value
        updated_value = existing_value + new_data
        
    # Prepare the data to update
    updated_data = {
        "fields": {
            column_name: updated_value
        }
    }
    
    # Update the record

    resp = table.update(record_id, {column_name:updated_value})

    # table.update(record_id, updated_data)

    return resp

# # Example usage
# table_name = "Actions"  # Replace with the name of the table you want to update
# record_id = "rece6y7T5kJK0ncYR"  # Replace with the ID of the record you want to update
# column_name = "Response"  # Replace with the name of the column (field) you want to update
# new_data = "\n NEw New NEw"  # Replace with the new data you want to append

# resp = append_data_to_column(table_name, record_id, column_name, new_data)
# print(resp)



def get_bracket_values_content_dict(input_list):
    """
    Searches a list of Names and returns a dictionary of Name:Content pairs
    """

    # Specify the Airtable table and columns to search in
    Find_in_Table = "Saved"
    Find_In_Column = "Name"
    Return_Value_From_Column = "Content"

    # Initialize an empty dictionary to hold the bracket value-content pairs
    combined_dict = {}

    # Loop through each bracket value in the input list
    for b_v in input_list:
        # print(f"Looking for: {b_v}")

        # Use the Get_Record_Info function from funcs_airtable to look up the content
        matched_data = Get_Record_Info(Find_in_Table, Find_In_Column, b_v, Return_Value_From_Column)
        
        # print(f"Matched Data: {matched_data}")

        # If matching content is found, add it to the dictionary, otherwise set to None or empty string
        combined_dict[b_v] = matched_data if matched_data else ''

    # trim begning and end spaces and newlines
    for key, value in combined_dict.items():
        combined_dict[key] = value.strip()



    return combined_dict






    
# Add Linked Record
def Add_Linked_Record(Add_To_Record_ID, Add_To_Table, Add_To_Column_Name, Add_This_Record_ID):
    # Get the existing linked records
    ExistingRecords_data = Get_Record_Data_From_ID(Add_To_Table, Add_To_Record_ID)

    ExistingRecords = ExistingRecords_data.get(Add_To_Column_Name)
    if ExistingRecords == None:
        ExistingRecords = []


    New_Records_List =[]    
    New_Records_List.append(Add_This_Record_ID)
    New_Records_List = New_Records_List + ExistingRecords
    # Remove Duplicates from the list
    New_Records_List = list(dict.fromkeys(New_Records_List))

    if New_Records_List != ExistingRecords:
    
        # Update the record
        table = Table(airtable_api_key, base, Add_To_Table)
        resp = table.update(Add_To_Record_ID, {Add_To_Column_Name:New_Records_List})
        return resp


# Add_Linked_Record("recQ6186wBoWhiS5O", "PPs", "AAs", "recFpngdigjSBEFxR")    



def add_new_record(This_Table, New_Record_Dict):
    table = Table(airtable_api_key, base, This_Table)
    resp = table.create(New_Record_Dict)
    return resp

# This_Table = "Saved"
# New_Record_Dict = {"Name":"Test Profile", "Content":"Test djjjdj", "Actions [Saved Response]":["recMbTgpsYtOGeESm"]}
# resp = add_new_record(This_Table, New_Record_Dict)






def Update_Record(This_Table, RecordID, Update_This_Column, Update_This_Value):
    table = Table(airtable_api_key, base, This_Table)
    resp = table.update(RecordID, {Update_This_Column:Update_This_Value})
    return resp


def Update_Record_Dict(This_Table, RecordID, Update_Data_Dict):
    table = Table(airtable_api_key, base, This_Table)
    resp = table.update(RecordID, Update_Data_Dict)
    return resp




def Add_Pages_To_Profiles(Page_ID, Profile_ID):
    # get the recordID for the PageID 
    PagesTable = "PAGEs"
    Pages_Column_Name_For_PageID = "Page_ID"
    Page_RecordID = Get_Record_Info("Pages", Pages_Column_Name_For_PageID, Page_ID)
    print(Page_RecordID)


    # get the recordID for the ProfileID
    ProfilesTable = "PPs"
    Profiles_Column_Name_For_ProfileID = "PROFILE"
    Profile_RecordID = Get_Record_Info("PPs", Profiles_Column_Name_For_ProfileID, Profile_ID)
    print(Profile_RecordID)

    # Add the PageID to the ProfileID
    # Add_Linked_Record(Profile_RecordID, ProfilesTable, "PAGEs", Page_RecordID)



def get_all_records (Find_in_Table, fields="", matchthis=""):
    table = Table(airtable_api_key, base, Find_in_Table)

    if matchthis == "":
        records = table.all(fields=[fields])

    else:
        records = table.all(fields=[fields], formula=match(matchthis))
    
    return records

# All_Airtable_data = get_all_records("CAMPs", ["FB ID"], {'FB ID': '23851484778370311'})
# print(All_Airtable_data[0])

# All_Airtable_data = get_all_records("Actions", ["Prompt Template"])
# print(All_Airtable_data)



def Get_Campaign_Info(RecordID):
    table = "CAMPs"
    table = Table(airtable_api_key, base, table)
    Campaigns = table.get(RecordID)
    return Campaigns
