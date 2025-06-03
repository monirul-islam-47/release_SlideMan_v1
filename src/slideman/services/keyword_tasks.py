# src/slideman/services/keyword_tasks.py

import logging
from typing import List, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool

from rapidfuzz import process, fuzz

from ..models.keyword import Keyword, KeywordKind
from .database import Database

logger = logging.getLogger(__name__)

class FindSimilarKeywordsSignals(QObject):
    """
    Signals for the FindSimilarKeywordsWorker.
    """
    resultsReady = Signal(list)  # List of suggestion dicts
    error = Signal(str)          # Error message

class FindSimilarKeywordsWorker(QRunnable):
    """
    Worker to find similar keywords for potential merging.
    Runs in a background thread using QThreadPool.
    """
    
    def __init__(self, db_service: Database, similarity_threshold: int = 80):
        """
        Initialize the worker.
        
        Args:
            db_service: Database service instance
            similarity_threshold: Threshold for similarity (0-100, higher means more similar)
        """
        super().__init__()
        self.db = db_service
        self.similarity_threshold = similarity_threshold
        self.signals = FindSimilarKeywordsSignals()
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """
        Find similar keywords and emit results.
        """
        try:
            self.logger.info("Starting to find similar keywords")
            
            # Get all keywords from database
            all_keywords = self.db.get_all_keyword_objects()
            if not all_keywords:
                self.signals.resultsReady.emit([])
                return
                
            self.logger.debug(f"Retrieved {len(all_keywords)} keywords")
            
            # Group keywords by kind
            keywords_by_kind = {}
            for keyword in all_keywords:
                if keyword.kind not in keywords_by_kind:
                    keywords_by_kind[keyword.kind] = []
                keywords_by_kind[keyword.kind].append(keyword)
                
            # Find similar keywords for each kind
            suggestions = []
            
            for kind, keywords in keywords_by_kind.items():
                self.logger.debug(f"Finding similar keywords for kind: {kind}")
                
                # Skip if less than 2 keywords
                if len(keywords) < 2:
                    continue
                    
                # Extract keyword texts
                keyword_texts = [kw.keyword for kw in keywords]
                
                # Use rapidfuzz to find similar keywords
                for i, keyword in enumerate(keywords):
                    query = keyword.keyword
                    # Extract top matches, excluding exact matches
                    matches = process.extract(
                        query, 
                        keyword_texts, 
                        scorer=fuzz.WRatio, 
                        score_cutoff=self.similarity_threshold,
                        limit=5
                    )
                    
                    # Process matches, excluding the exact match (itself)
                    for match in matches:
                        # Extract match components - rapidfuzz can return (match_text, score) or (match_text, score, index)
                        match_text = match[0]
                        score = match[1]
                        
                        if match_text == query:
                            continue  # Skip self-match
                            
                        # Find matching keyword object
                        to_keyword = next((kw for kw in keywords if kw.keyword == match_text), None)
                        if to_keyword and keyword.id != to_keyword.id:
                            # Add suggestion with both directions (user can choose direction)
                            # Lower ID to higher ID is often preferred (keeps older keywords)
                            if keyword.id < to_keyword.id:
                                suggestions.append({
                                    'from': to_keyword,  # Newer keyword to merge
                                    'to': keyword,       # Older keyword to keep
                                    'score': score,
                                    'kind': kind
                                })
                            else:
                                suggestions.append({
                                    'from': keyword,     # Newer keyword to merge
                                    'to': to_keyword,    # Older keyword to keep
                                    'score': score,
                                    'kind': kind
                                })
            
            # Deduplicate suggestions
            # Convert to a unique representation and back
            unique_suggestions = {}
            for suggestion in suggestions:
                key = (suggestion['from'].id, suggestion['to'].id)
                # Keep the higher score if duplicates exist
                if key not in unique_suggestions or suggestion['score'] > unique_suggestions[key]['score']:
                    unique_suggestions[key] = suggestion
            
            result = list(unique_suggestions.values())
            
            # Sort by score (descending) and then by kind
            result.sort(key=lambda x: (-x['score'], x['kind']))
            
            self.logger.info(f"Found {len(result)} unique suggestions for keyword merging")
            self.signals.resultsReady.emit(result)
            
        except Exception as e:
            self.logger.error(f"Error finding similar keywords: {str(e)}", exc_info=True)
            self.signals.error.emit(f"Error finding similar keywords: {str(e)}")
