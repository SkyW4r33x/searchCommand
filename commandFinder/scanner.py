from utils import normalize_text, replace_variables
from fuzzywuzzy import process
from services import read_tool_file
from typing import List
from config import Config  

def search_generic(search_command, query: str, search_type: str) -> List[str]:
    try:
        query_normalized = normalize_text(query)
        if query_normalized is None:
            return []
        results = []
        search_command.search_mode = search_type
        items = search_command.categories if search_type == "category" else search_command.tool_to_file
        item_normalized = {normalize_text(k): k for k in items.keys() if normalize_text(k)}
        
        if query_normalized in item_normalized:
            key = item_normalized[query_normalized]
            if search_type == "category":
                search_command.current_category = key
                search_command.last_query = key
                for tool in search_command.categories[key]:
                    results.append(f"[*] {tool}")
                    tool_content = read_tool_file(search_command.tool_to_file[tool], Config.MAX_FILE_SIZE, search_command.root_dir)
                    results.extend([replace_variables(line, search_command.ip_value, search_command.url_value) for line in tool_content if line.strip()])
            else:
                search_command.current_category = search_command.tool_to_category.get(key, "")
                search_command.last_query = key
                tool_content = read_tool_file(search_command.tool_to_file[key], Config.MAX_FILE_SIZE, search_command.root_dir)
                results.append(f"[*] {key}")
                results.extend([replace_variables(line, search_command.ip_value, search_command.url_value) for line in tool_content if line.strip()])
            search_command.last_results_count = len(results)
            return results
        
        matches = process.extract(query_normalized, item_normalized.keys(), limit=1, scorer=process.fuzz.partial_ratio)
        if matches and matches[0][1] >= 80:
            key = item_normalized[matches[0][0]]
            if search_type == "category":
                search_command.current_category = key
                search_command.last_query = key
                for tool in search_command.categories[key]:
                    results.append(f"[*] {tool}")
                    tool_content = read_tool_file(search_command.tool_to_file[tool], Config.MAX_FILE_SIZE, search_command.root_dir)
                    results.extend([replace_variables(line, search_command.ip_value, search_command.url_value) for line in tool_content if line.strip()])
            else:
                search_command.current_category = search_command.tool_to_category.get(key, "")
                search_command.last_query = key
                tool_content = read_tool_file(search_command.tool_to_file[key], Config.MAX_FILE_SIZE, search_command.root_dir)
                results.append(f"[*] {key}")
                results.extend([replace_variables(line, search_command.ip_value, search_command.url_value) for line in tool_content if line.strip()])
            search_command.last_results_count = len(results)
            return results
        
        search_command.current_category = ""
        search_command.last_query = ""
        search_command.last_results_count = 0
        return []
    except AttributeError as e:
        handle_exception(f"Error searching by {search_type}", e)
        return []

def search_by_category(search_command, query: str) -> List[str]:
    return search_generic(search_command, query, "category")

def search_by_tool(search_command, query: str) -> List[str]:
    return search_generic(search_command, query, "tool")