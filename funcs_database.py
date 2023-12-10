import psycopg2
import os
import psycopg2.extras  # Import the extras
from dotenv import load_dotenv

def get_media_by_album_id(album_id):
    # Load environment variables
    load_dotenv()

    # Get database connection string from environment variables
    SUPABASE_DB_FULL_URL = os.getenv("SUPABASE_DB_FULL_URL")

    # Initialize connection and cursor
    conn = psycopg2.connect(SUPABASE_DB_FULL_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # SQL query
    sql_query = """
    SELECT media.*
    FROM album_media_link
    JOIN media ON album_media_link.media_id = media.id
    WHERE album_media_link.album_id = %s;
    """

    result_list = []

    try:
        # Execute the query
        cursor.execute(sql_query, (album_id,))

        # Fetch all rows and store them in a list of dictionaries
        rows = cursor.fetchall()
        for row in rows:
            result_list.append(dict(row))

    except Exception as e:
        print(f"An error occurred while executing the SQL query: {e}")

    finally:
        # Close the cursor and the connection
        cursor.close()
        conn.close()

    return result_list

# # Test the function
# album_id_to_search = 10  # Replace with your actual album_id
# result = get_media_by_album_id(album_id_to_search)
# print(result)  # This will print a list of dictionaries



def get_scene_and_clip_by_id(scene_id):
    # Load environment variables
    load_dotenv()

    # Get database connection string from environment variables
    SUPABASE_DB_FULL_URL = os.getenv("SUPABASE_DB_FULL_URL")

    # Initialize connection and cursor
    conn = psycopg2.connect(SUPABASE_DB_FULL_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch column names from media table
    cursor.execute("""
        SELECT attname 
        FROM pg_catalog.pg_attribute 
        WHERE attrelid = (SELECT oid FROM pg_catalog.pg_class WHERE relname='media') 
        AND attnum > 0 AND NOT attisdropped
    """)
    columns = cursor.fetchall()
    select_columns = ", ".join([f"media.{col[0]} AS \"media_{col[0]}\"" for col in columns])

    # SQL query
    sql_query = f"""
    SELECT scenes.*, {select_columns}
    FROM scenes
    LEFT JOIN media ON scenes.final_clip = media.id
    WHERE scenes.id = %s;
    """

    result_dict = {}

    try:
        # Execute the query
        cursor.execute(sql_query, (scene_id,))

        # Fetch the row
        row = cursor.fetchone()
        if row:
            result_dict = dict(row)

    except Exception as e:
        print(f"An error occurred while executing the SQL query: {e}")

    finally:
        # Close the cursor and the connection
        cursor.close()
        conn.close()

    return result_dict

# Example usage:
# scene_data = get_scene_and_clip_by_id(1)
# print(scene_data)
