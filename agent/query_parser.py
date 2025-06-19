import re
from typing import Tuple, Optional
from agent.models import RestaurantType

class QueryParser:
    """Parser for extracting food type and location from user queries"""
    
    def __init__(self):
        # Define municipality keywords and aliases
        self.location_keywords = {
            'Providencia': ['providencia'],
            'Las Condes': ['las condes', 'lascondes'],
            'Huechuraba': ['huechuraba'],
            'Ñuñoa': ['ñuñoa', 'nunoa'],
            'Maipú': ['maipu', 'maipú'],
            'Santiago Centro': ['santiago centro', 'centro', 'santiago'],
            'La Florida': ['la florida', 'laflorida'],
            'Estación Central': ['estacion central', 'estación central'],
            'Puente Alto': ['puente alto', 'puentealto'],
            'San Miguel': ['san miguel', 'sanmiguel'],
            'San Bernardo': ['san bernardo', 'sanbernardo'],
            'La Reina': ['la reina', 'lareina'],
            'Quilicura': ['quilicura'],
            'Peñalolén': ['peñalolen', 'peñalolén'],
            'Lo Espejo': ['lo espejo', 'loespejo']
        }
        
        # Define food type keywords
        self.food_type_keywords = {
            RestaurantType.HAMBURGUESAS: ['hamburguesas', 'hamburguesa'], # Don't add Burger to this list. otherwise Burger King will be detected as hamburguesa and removed from the query
            RestaurantType.PIZZAS: ['pizzas'], # Don't add Pizza to this list. otherwise Pizza Hut will be detected as pizzas and removed from the query
            RestaurantType.COMPLETOS: ['completos', 'completo', 'hot dogs', 'hotdogs', 'hot dog', 'hotdog']
        }
        
        # Define ranking keywords
        self.ranking_keywords = {
            'best': ['mejores', 'mejor', 'best', 'top', 'buenos', 'bueno', 'buenas', 'buena'],
            'worst': ['peores', 'peor', 'worst', 'malo', 'malos', 'malas', 'mala']
        }
        
    def parse_query(self, query: str) -> Tuple[str, Optional[RestaurantType], Optional[str], bool]:
        """
        Parse user query to extract food type, location, and ranking preference
        
        Returns:
            Tuple of (new_query, food_type, location, best_and_worst_filter)
        """
        query_lower = query.lower()
        
        # Extract food type
        new_query, food_type = self._extract_food_type(query_lower)
        
        # Extract location
        new_query,location = self._extract_location(new_query)
        
        # Check for best/worst filter
        best_and_worst = self._check_ranking_filter(new_query)

        return new_query, food_type, location, best_and_worst

    def _extract_food_type(self, query_lower: str) -> Tuple[str, Optional[RestaurantType]]:
        """
        Extract food type from query and clean the query
        Example: "hamburguesas mcdonald's" -> "mcdonald's", RestaurantType.HAMBURGUESAS
        Returns query, None if no food type is found
        """
        for food_type, keywords in self.food_type_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Remove the food type from the query
                    pattern = keyword
                    new_query = re.sub(pattern, '', query_lower).strip()
                    return new_query, food_type
        return query_lower, None
        
    def _extract_location(self, query_lower: str) -> Tuple[str, Optional[str]]:
        """
        Extract location from query and clean the query
        Example: "PizzaHut en la comuna de puente alto" -> "PizzaHut Puente Alto", "Puente Alto"
        Returns query, None if no location is found
        """
        # Look for "en la comuna de" pattern - capture everything after it
        comuna_pattern = r'en\s+la\s+comuna\s+de\s+(.+)'
        match = re.search(comuna_pattern, query_lower)
        if match:
            location = match.group(1).strip()
            # Remove "en la comuna de [location]" from the query
            new_query = re.sub(comuna_pattern, '', query_lower).strip()
            normalized_location = self._normalize_location(location)
            # Add the normalized location back to the query
            new_query = f"{new_query} {normalized_location}".strip()
            return new_query, normalized_location
            
        # Look for "en" pattern - capture everything after it
        en_pattern = r'en\s+(.+)'
        match = re.search(en_pattern, query_lower)
        if match:
            location = match.group(1).strip()
            # Remove "en [location]" from the query
            new_query = re.sub(en_pattern, '', query_lower).strip()
            normalized_location = self._normalize_location(location)
            # Add the normalized location back to the query
            new_query = f"{new_query} {normalized_location}".strip()
            return new_query, normalized_location
            
        # Direct location matching
        for location, aliases in self.location_keywords.items():
            for alias in aliases:
                if alias in query_lower:
                    return query_lower, location
                    
        return query_lower, None
        
    def _normalize_location(self, location: str) -> str:
        """
        Normalize location name to match our standard format
        Example: "puentealto" -> "Puente Alto"
        Returns the same location title cased if it's not found in our standard format
        """
        location_lower = location.lower().strip()
        
        # Check if it matches any of our known locations
        for standard_location, aliases in self.location_keywords.items():
            if location_lower in aliases or location_lower == standard_location:
                return standard_location
        
        # For unknown locations, title case it
        return " ".join(word.title() for word in location.split())
    
    def _check_ranking_filter(self, query: str) -> bool:
        """Check if query asks for best and worst restaurants"""
        # TODO✅: Implement this
        query_lower = query.lower()
        has_best = any(keyword in query_lower for keyword in self.ranking_keywords['best'])
        has_worst = any(keyword in query_lower for keyword in self.ranking_keywords['worst'])
        return has_best and has_worst