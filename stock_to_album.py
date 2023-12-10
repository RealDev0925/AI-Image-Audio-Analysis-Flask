import funcs_supabase
import actions
import pexels
import vector_search

# Constants
MATCH_THRESHOLD = 0.6
MATCH_COUNT = 20

def fetch_and_filter_vector_search_results(scene_text, match_threshold=MATCH_THRESHOLD, match_count=MATCH_COUNT, filters=None):
    """
    Performs a semantic vector search based on scene text and filters the results.

    :param scene_text: Text of the scene to perform search.
    :param match_threshold: Threshold for match relevance.
    :param match_count: Number of matches to return.
    :param filters: Dictionary of filters to apply on search results.
    :return: List of filtered search results.
    """
    my_vec = vector_search.get_embeddings(scene_text)
    vec_search_results = vector_search.search_vectors_with_media(my_vec, match_threshold, match_count)

    if filters is None:
        filters = {'media_source_type': 'stock'}

    return [item for item in vec_search_results if all(item.get(key) == value for key, value in filters.items())]


def process_scene(scene_id, include_stock_media=True):
    """
    Processes a given scene by its ID.

    :param scene_id: ID of the scene to be processed.
    :param include_stock_media: Boolean flag to include stock media search.
    """
    try:
        scene_data = funcs_supabase.select_data("scenes", "id", scene_id)[0]
    except IndexError:
        print(f"No data found for scene ID {scene_id}")
        return

    keywords = scene_data.get("theme_keywords")
    if include_stock_media:
        pexels_results = pexels.process_pexels_kw_list(keywords)
        print(pexels_results)
    else:
        print("Skipping stock search")

    album_id = scene_data.get("album_id")
    scene_text = scene_data.get("scene_text")
    print(scene_text)

    matching_media = fetch_and_filter_vector_search_results(scene_text)
    print(matching_media)

    for media in matching_media:
        media_id = media.get("vector_media_table_id")
        funcs_supabase.insert_data("album_media_link", {"album_id": album_id, "media_id": media_id})


def process_project_scenes(project_id, include_stock_media=True, scenes_list=None):
    """
    Processes all scenes for a given project.

    :param project_id: ID of the project.
    :param include_stock_media: Boolean flag to include stock media search.
    :param scenes_list: Optional list of scenes to process. If None, fetch scenes for the project.
    """
    if scenes_list is None:
        scenes = actions.get_scenes_for_project(project_id)
    else:
        scenes = scenes_list

    for scene_id in scenes:
        process_scene(scene_id, include_stock_media)

