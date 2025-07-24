import re
from typing import Dict, List, Tuple
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from collections import defaultdict
import time
import urllib.parse
from utils import normalize_text, process

class EnhancedCompleter(Completer):
    # ------------------------ Initialization with Data Structures for Categories and Tools ------------------------ #
    def __init__(self, categories: List[str], tools: List[str], tools_by_category: Dict[str, List[str]], 
                 recent_ips: List[str], recent_urls: List[str], tool_to_category: Dict[str, str], 
                 tool_to_file: Dict[str, str]):
        self.original_categories = categories
        self.original_tools = [tool for tool in tools if tool in tool_to_file]
        self.categories_normalized = [normalize_text(cat) for cat in categories if normalize_text(cat)]
        self.tools_normalized = [normalize_text(tool) for tool in self.original_tools if normalize_text(tool)]
        self.tools_by_category = tools_by_category
        self.recent_ips = recent_ips
        self.recent_urls = recent_urls
        self.tool_to_category = tool_to_category
        self.tool_to_file = tool_to_file

        self._completion_cache = {}
        self._last_cache_clear = time.time()
        
        self.usage_stats = defaultdict(int)
        
        self._build_search_indices()

        if not categories or not self.original_tools or not tools_by_category:
            print(f"{Colors.RED}[-]{Colors.RESET} Error: Empty or invalid autocomplete data")

        self._setup_internal_commands()

    # ------------------------ Building N-gram Indices for Fuzzy Searching ------------------------ #
    def _build_search_indices(self):
        self.tool_ngram_index = defaultdict(list)
        self.category_ngram_index = defaultdict(list)
        
        for tool in self.original_tools:
            for ngram in self._generate_ngrams(normalize_text(tool), 2):
                self.tool_ngram_index[ngram].append(tool)
        
        for category in self.original_categories:
            for ngram in self._generate_ngrams(normalize_text(category), 2):
                self.category_ngram_index[ngram].append(category)

    # ------------------------ Generating N-grams for Text Matching ------------------------ #
    def _generate_ngrams(self, text: str, n: int = 2) -> set:
        if not text or len(text) < n:
            return {text} if text else set()
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    # ------------------------ Calculating Fuzzy Matching Score ------------------------ #
    def _fuzzy_score(self, query: str, target: str) -> float:
        if not query or not target:
            return 0.0
            
        if query == target:
            return 1.0
            
        if target.startswith(query):
            return 0.9 + (len(query) / len(target)) * 0.1
            
        query_ngrams = self._generate_ngrams(query, 2)
        target_ngrams = self._generate_ngrams(target, 2)
        
        if not query_ngrams or not target_ngrams:
            return 0.0
            
        intersection = len(query_ngrams & target_ngrams)
        union = len(query_ngrams | target_ngrams)
        jaccard = intersection / union if union > 0 else 0.0
        
        consecutive_bonus = self._consecutive_match_bonus(query, target)
        
        return min(0.89, jaccard * 0.7 + consecutive_bonus * 0.3)

    # ------------------------ Computing Bonus for Consecutive Matches ------------------------ #
    def _consecutive_match_bonus(self, query: str, target: str) -> float:
        if not query or not target:
            return 0.0
            
        max_consecutive = 0
        current_consecutive = 0
        
        i = j = 0
        while i < len(query) and j < len(target):
            if query[i] == target[j]:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
                i += 1
            else:
                current_consecutive = 0
            j += 1
            
        return max_consecutive / len(query) if len(query) > 0 else 0.0

    # ------------------------ Setting Up Internal Commands and Aliases ------------------------ #
    def _setup_internal_commands(self):
        self.internal_commands = [
            ('help', 'Show help menu'),
            ('clear', 'Clear screen'),
            ('list tools', 'List tools'),
            ('list categories', 'List categories'),
            ('setip', 'Set $IP for commands'),
            ('seturl', 'Set $URL for commands'),
            ('refresh', 'Reload tools or configuration'),
            ('gtfsearch', 'Search in GTFOBins'),
            ('add categories', 'Create new category'),
            ('add tools', 'Create new tool'),
            ('edit', 'Edit tool file'),
            ('delete category', 'Delete a category'),
            ('delete tool', 'Delete a tool'),
            ('exit', 'Exit the program')
        ]
        self.command_to_alias = {
            'help': 'h', 'clear': 'c', 'list tools': 'lt', 'list categories': 'lc',
            'setip': 'si', 'seturl': 'su', 'refresh': 'r', 'edit': 'e', 
            'gtfsearch': 'gtf', 'add categories': 'ac', 'add tools': 'at',
            'delete category': 'dc', 'delete tool': 'dt', 'exit': 'q'
        }

    # ------------------------ Normalizing URL for Consistent Handling ------------------------ #
    def _normalize_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            path = re.sub(r'/+', '/', parsed.path.lstrip('/'))
            scheme = parsed.scheme if parsed.scheme in ['http', 'https'] else 'http'
            return urllib.parse.urlunparse((
                scheme, parsed.netloc.lower(), path,
                parsed.params, parsed.query, parsed.fragment
            ))
        except Exception:
            return url

    # ------------------------ Parsing Command Context for Completion Logic ------------------------ #
    def _parse_command_context(self, text: str) -> Dict[str, bool]:
        parts = text.strip().split()
        if len(parts) < 2:
            return {}
        
        first_cmd = normalize_text(parts[0])
        return {
            'is_setip_arg': first_cmd in ['setip', 'si'],
            'is_seturl_arg': first_cmd in ['seturl', 'su'],
            'is_refresh_arg': first_cmd in ['refresh', 'r'],
            'is_edit_arg': first_cmd in ['edit', 'e'],
            'is_gtfsearch_arg': first_cmd in ['gtfsearch', 'gtf']
        }

    # ------------------------ Clearing Cache Periodically ------------------------ #
    def _clear_cache_if_needed(self):
        current_time = time.time()
        if current_time - self._last_cache_clear > 300:
            self._completion_cache.clear()
            self._last_cache_clear = current_time

    # ------------------------ Retrieving Cached Completions ------------------------ #
    def _get_cached_completions(self, cache_key: str):
        self._clear_cache_if_needed()
        return self._completion_cache.get(cache_key)

    # ------------------------ Caching Completions for Performance ------------------------ #
    def _cache_completions(self, cache_key: str, completions: List):
        if len(self._completion_cache) < 100:
            self._completion_cache[cache_key] = completions

    # ------------------------ Smart Matching for Tools Using Fuzzy Logic ------------------------ #
    def _smart_match_tools(self, query: str) -> List[Tuple[float, str, str]]:
        results = []
        query_norm = normalize_text(query)
        query_ngrams = self._generate_ngrams(query_norm, 2)
        
        candidates = set()
        for ngram in query_ngrams:
            candidates.update(self.tool_ngram_index.get(ngram, []))
        
        for tool in candidates:
            tool_norm = normalize_text(tool)
            score = self._fuzzy_score(query_norm, tool_norm)
            if score > 0.3:
                usage_bonus = min(0.1, self.usage_stats[tool] * 0.01)
                final_score = score + usage_bonus
                category = self.tool_to_category.get(tool, "")
                results.append((final_score, tool, category))
        
        return sorted(results, key=lambda x: x[0], reverse=True)

    # ------------------------ Smart Matching for Categories Using Fuzzy Logic ------------------------ #
    def _smart_match_categories(self, query: str) -> List[Tuple[float, str]]:
        results = []
        query_norm = normalize_text(query)
        
        if not query_norm:
            return results
            
        for category in self.original_categories:
            cat_norm = normalize_text(category)
            if not cat_norm:
                continue
                
            score = self._fuzzy_score(query_norm, cat_norm)
            if score > 0.3:
                results.append((score, category))
                
        return sorted(results, key=lambda x: x[0], reverse=True)

    # ------------------------ Adding Completions for Internal Commands ------------------------ #
    def _add_internal_command_completions(self, word: str, word_normalized: str, completions: List):
        for cmd, meta in self.internal_commands:
            alias = self.command_to_alias.get(cmd, cmd[:2])
            
            cmd_score = self._fuzzy_score(word_normalized, normalize_text(cmd))
            alias_score = self._fuzzy_score(word_normalized, normalize_text(alias))
            
            if cmd_score > 0.3 or alias_score > 0.3:
                score = max(cmd_score, alias_score)
                display_text = f'[{alias}] {cmd}'

                completions.append((-score, Completion( 
                    cmd,
                    start_position=-len(word),
                    display=HTML(display_text),
                    display_meta=meta,
                    style='class:completion-menu.completion'
                )))

    # ------------------------ Adding Smart Tool Completions ------------------------ #
    def _add_smart_tool_completions(self, word: str, word_normalized: str, completions: List, limit: int = 15):
        matches = self._smart_match_tools(word_normalized)
        
        for i, (score, tool, category) in enumerate(matches[:limit]):
            priority = 1.0 - score 
            completions.append((priority, Completion(
                tool,
                start_position=-len(word),
                display=HTML(f'🔧 {tool}'),
                display_meta=f'Category: {category}' if category else '',
                style='class:completion-menu.tool-completion'
            )))

    # ------------------------ Adding Smart Category Completions ------------------------ #
    def _add_smart_category_completions(self, word: str, word_normalized: str, completions: List, limit: int = 10):
        matches = self._smart_match_categories(word_normalized)
        
        for score, category in matches[:limit]:
            priority = 1.0 - score
            tool_count = len(self.tools_by_category.get(category, []))
            completions.append((priority, Completion(
                category,
                start_position=-len(word),
                display=HTML(f'📂 {category}'),
                display_meta=f'{tool_count} tools',
                style='class:completion-menu.category-completion'
            )))

    # ------------------------ Adding Completions for Recent Items ------------------------ #
    def _add_smart_recent_completions(self, word: str, word_normalized: str, 
                                    items: List[str], icon: str, meta: str, completions: List):
        scored_items = []
        for item in items:
            item_norm = normalize_text(self._normalize_url(item) if 'URL' in meta else item)
            if item_norm:
                score = self._fuzzy_score(word_normalized, item_norm)
                if score > 0.3:
                    scored_items.append((score, item))
        
        for score, item in sorted(scored_items, key=lambda x: x[0], reverse=True)[:10]:
            priority = 1.0 - score
            completions.append((priority, Completion(
                item,
                start_position=-len(word),
                display=HTML(f'{icon} {item}'),
                display_meta=meta,
                style='class:completion-menu.tool-completion'
            )))

    # ------------------------ Generating Completions Based on Context ------------------------ #
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        word_normalized = normalize_text(word)
        
        if word_normalized is None or len(word_normalized) == 0:
            return

        cache_key = f"{text}:{word}"
        cached = self._get_cached_completions(cache_key)
        if cached:
            for completion in cached:
                yield completion
            return

        completions = []
        context = self._parse_command_context(text)
        is_command_arg = any(context.values())

        if not is_command_arg:
            self._add_internal_command_completions(word, word_normalized, completions)
            self._add_smart_category_completions(word, word_normalized, completions)
            self._add_smart_tool_completions(word, word_normalized, completions)
        elif context.get('is_refresh_arg') and word_normalized in normalize_text('config'):
            completions.append((0, Completion('config', start_position=-len(word),
                display=HTML('🔄 config'), display_meta='Reset configuration (IP and URL)',
                style='class:completion-menu.completion')))
        elif context.get('is_edit_arg'):
            self._add_smart_tool_completions(word, word_normalized, completions)
        elif context.get('is_setip_arg'):
            self._add_smart_recent_completions(word, word_normalized, self.recent_ips, 
                '🌐', 'Recent IP or domain', completions)
        elif context.get('is_seturl_arg'):
            self._add_smart_recent_completions(word, word_normalized, self.recent_urls, 
                '🌐', 'Recent URL', completions)

        seen = set()
        final_completions = []
        for priority, completion in sorted(completions, key=lambda x: x[0]):
            if completion.text not in seen:
                seen.add(completion.text)
                final_completions.append(completion)
                self.usage_stats[completion.text] += 1

        self._cache_completions(cache_key, final_completions)

        for completion in final_completions:
            yield completion