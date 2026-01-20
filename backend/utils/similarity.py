"""
Utility functions for calculating incident similarity.

This module provides functions to compare incidents based on their
attributes (title, description, affected services) to find related
historical incidents.
"""

from typing import Dict, Any, List, Set
import re


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by lowercasing and removing special chars.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    # Remove special characters but keep spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(text: str) -> Set[str]:
    """
    Extract keywords from text by removing common stopwords.
    
    Args:
        text: Input text
        
    Returns:
        Set of keywords
    """
    # Common stopwords to ignore
    stopwords = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had',
        'what', 'when', 'where', 'who', 'which', 'why', 'how'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    # Filter out stopwords and short words
    keywords = {word for word in words if word not in stopwords and len(word) > 2}
    return keywords


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings using keyword overlap.
    
    Uses Jaccard similarity coefficient: |A ∩ B| / |A ∪ B|
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def calculate_service_similarity(services1: List[str], services2: List[str]) -> float:
    """
    Calculate similarity between two lists of affected services.
    
    Uses Jaccard similarity coefficient: |A ∩ B| / |A ∪ B|
    
    Args:
        services1: First list of services
        services2: Second list of services
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not services1 or not services2:
        return 0.0
    
    set1 = set(services1)
    set2 = set(services2)
    
    intersection = set1 & set2
    union = set1 | set2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def calculate_incident_similarity(incident1: Dict[str, Any], incident2: Dict[str, Any]) -> float:
    """
    Calculate overall similarity between two incidents.
    
    Combines similarity scores from:
    - Title (weight: 0.4)
    - Description (weight: 0.4)
    - Affected services (weight: 0.2)
    
    Args:
        incident1: First incident dictionary
        incident2: Second incident dictionary
        
    Returns:
        Overall similarity score between 0.0 and 1.0
    """
    # Calculate component similarities
    title_sim = calculate_text_similarity(
        incident1.get('title', ''),
        incident2.get('title', '')
    )
    
    desc_sim = calculate_text_similarity(
        incident1.get('description', ''),
        incident2.get('description', '')
    )
    
    service_sim = calculate_service_similarity(
        incident1.get('affected_services', []),
        incident2.get('affected_services', [])
    )
    
    # Weighted average
    # Title and description are more important than services
    weights = {
        'title': 0.4,
        'description': 0.4,
        'services': 0.2
    }
    
    overall_similarity = (
        title_sim * weights['title'] +
        desc_sim * weights['description'] +
        service_sim * weights['services']
    )
    
    return overall_similarity


def find_similar_incidents(
    target_incident: Dict[str, Any],
    historical_incidents: List[Dict[str, Any]],
    similarity_threshold: float = 0.3,
    max_results: int = 5
) -> List[tuple[Dict[str, Any], float]]:
    """
    Find similar incidents from historical data.
    
    Args:
        target_incident: The incident to find matches for
        historical_incidents: List of historical incidents to search
        similarity_threshold: Minimum similarity score to include (0.0 to 1.0)
        max_results: Maximum number of results to return
        
    Returns:
        List of tuples (incident, similarity_score) sorted by similarity descending
    """
    target_id = target_incident.get('id')
    
    similarities = []
    for incident in historical_incidents:
        # Don't compare incident to itself
        if incident.get('id') == target_id:
            continue
        
        # Only consider resolved incidents as historical references
        if incident.get('status') != 'resolved':
            continue
        
        similarity = calculate_incident_similarity(target_incident, incident)
        
        if similarity >= similarity_threshold:
            similarities.append((incident, similarity))
    
    # Sort by similarity score descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N results
    return similarities[:max_results]
