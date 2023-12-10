import os
import psycopg2
import psycopg2.extras  # Import the extras


import openai
# from openai.embeddings_utils import get_embedding, cosine_similarity


from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_embeddings(input = ""):
    """Get the vector embeddings from openAI for a given input string."""


    # replace new lines with spaces
    input = input.replace("\n", " ")

    # remove extra spaces
    input = " ".join(input.split())


    response = openai.Embedding.create( 
        input= input,
        model="text-embedding-ada-002"
    )

    embeddings = response['data'][0]['embedding']
    return embeddings




def search_vectors(query_embedding, match_threshold=0.7, match_count=10):
    # Load PostgreSQL full URL from .env file
    SUPABASE_DB_FULL_URL = os.getenv("SUPABASE_DB_FULL_URL")
    
    # Initialize connection and cursor
    conn = psycopg2.connect(SUPABASE_DB_FULL_URL)
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    
    try:
        # Prepare SQL query
        sql_query = """
        SELECT
            vectors.id,
            vectors.content,
            vectors.media_table_id,
            1 - (vectors.embedding <=> %s::vector) AS similarity
        FROM vectors
        WHERE 1 - (vectors.embedding <=> %s::vector) > %s
        AND vectors.media_table_id IS NOT NULL
        ORDER BY similarity DESC
        LIMIT %s;
        """



        
        # Execute SQL query
        cursor.execute(sql_query, (query_embedding, query_embedding, match_threshold, match_count))
        
        # Fetch results
        results = cursor.fetchall()
        results = [dict(row) for row in results]

        
        return results
    



    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



# # Example usage
# match_threshold = 0.8
# match_count = 50
# my_text = "not hot dog"
# my_vec = get_embeddings(my_text)
# results = search_vectors(my_vec, match_threshold, match_count)
# for item in results:
#     print(item)



# VECTOR SEARCH WITHIN AN ALBUM
def search_vectors_album_filter(query_embedding, match_threshold=0.7, match_count=10, album_id=None):
    # Load PostgreSQL full URL from .env file
    SUPABASE_DB_FULL_URL = os.getenv("SUPABASE_DB_FULL_URL")
    
    # Initialize connection and cursor
    conn = psycopg2.connect(SUPABASE_DB_FULL_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Base SQL query
        sql_query = """
        SELECT
            vectors.id,
            vectors.content,
            vectors.media_table_id,
            1 - (vectors.embedding <=> %s::vector) AS similarity
        FROM vectors
        """
        
        # Join with album_media_link table if album_id is specified
        if album_id:
            sql_query += """
            INNER JOIN album_media_link ON vectors.media_table_id = album_media_link.media_id
            WHERE album_media_link.album_id = %s
            AND 1 - (vectors.embedding <=> %s::vector) > %s
            """
        else:
            sql_query += """
            WHERE 1 - (vectors.embedding <=> %s::vector) > %s
            """
        
        sql_query += """
        AND vectors.media_table_id IS NOT NULL
        ORDER BY similarity DESC
        LIMIT %s;
        """
        
        # Execute SQL query
        if album_id:
            cursor.execute(sql_query, (query_embedding, album_id, query_embedding, match_threshold, match_count))
        else:
            cursor.execute(sql_query, (query_embedding, query_embedding, match_threshold, match_count))
        
        # Fetch results
        results = cursor.fetchall()
        results = [dict(row) for row in results]
        
        return results

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        cursor.close()
        conn.close()






def search_vectors_with_media(query_embedding, match_threshold=0.7, match_count=10):
    "vector search with data included from the media table related to this vector"

    SUPABASE_DB_FULL_URL = os.getenv("SUPABASE_DB_FULL_URL")
    conn = psycopg2.connect(SUPABASE_DB_FULL_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # Prepare SQL query
        sql_query = """
        SELECT
            v.id, v.content, v.media_table_id,  -- Select required columns from vectors table
            m.*,  -- Select everything from media table
            1 - (v.embedding <=> %s::vector) AS similarity
        FROM vectors v
        JOIN media m ON v.media_table_id = m.id
        WHERE 1 - (v.embedding <=> %s::vector) > %s
        ORDER BY similarity DESC
        LIMIT %s;
        """

        # Execute SQL query
        cursor.execute(sql_query, (query_embedding, query_embedding, match_threshold, match_count))
        results = cursor.fetchall()

        # Process results to differentiate between vectors and media data
        formatted_results = []
        for row in results:
            vector_data = {f"vector_{key}": value for key, value in row.items() if key in ['id', 'content', 'media_table_id']}
            media_data = {f"media_{key}": value for key, value in row.items() if key not in ['id', 'content', 'media_table_id', 'embedding']}
            formatted_results.append({**vector_data, **media_data, "similarity": row['similarity']})

        return formatted_results
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



# match_threshold = 0.8
# match_count = 50
# my_text = "not hot dog"
# my_vec = get_embeddings(my_text)
# results = search_vectors_with_media(my_vec, match_threshold, match_count)
# for item in results:
#     print(item)