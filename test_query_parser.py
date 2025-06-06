import pytest
from agent.query_parser import QueryParser
from agent.models import RestaurantType


class TestQueryParser:
    """Test suite for QueryParser class"""
    
    @pytest.fixture
    def parser(self):
        """Create QueryParser instance for testing"""
        return QueryParser()
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes with correct keywords"""
        assert parser is not None
        assert len(parser.location_keywords) > 0
        assert len(parser.food_type_keywords) > 0
        assert len(parser.ranking_keywords) > 0
    
    def test_extract_food_type_none(self, parser):
        """Test when no food type is found"""
        query, food_type = parser._extract_food_type("restaurante en santiago")
        assert food_type is None
        assert query == "restaurante en santiago"

    def test_extract_food_type_hamburguesas(self, parser):
        """Test extraction of hamburguesas food type"""
        query, food_type = parser._extract_food_type("hamburguesas burger king")
        assert food_type == RestaurantType.HAMBURGUESAS
        assert "burger" in query.lower()
        assert "hamburguesas" not in query.lower()
        
    
    def test_extract_food_type_pizzas(self, parser):
        """Test extraction of pizzas food type"""        
        query, food_type = parser._extract_food_type("pizzas pizza hut")
        assert food_type == RestaurantType.PIZZAS
        assert "pizza" in query.lower()
        assert "pizzas" not in query.lower()
    
    def test_extract_food_type_completos(self, parser):
        """Test extraction of completos food type"""
        query, food_type = parser._extract_food_type("completos dominó")
        assert food_type == RestaurantType.COMPLETOS
        assert "completos" not in query.lower()

    def test_extract_location_en_la_comuna_de(self, parser):
        """Test location extraction with 'en la comuna de' pattern"""
        query, location = parser._extract_location("hamburguesas en la comuna de huechuraba")
        assert location == "Huechuraba"
        assert "hamburguesas" in query.lower()
        assert "en la comuna de" not in query.lower()
        assert "huechuraba" in query.lower()
    
    def test_extract_location_en_pattern(self, parser):
        """Test location extraction with 'en' pattern"""
        query, location = parser._extract_location("mcdonald's en huechuraba")
        assert location == "Huechuraba"
        assert "mcdonald's" in query.lower()
        assert "en" not in query.lower()
        assert "huechuraba" in query.lower()
    
    def test_extract_location_direct_match(self, parser):
        """Test direct location matching"""
        query, location = parser._extract_location("mcdonald's providencia")
        assert location == "Providencia"
        assert "mcdonald's" in query.lower()
        assert "providencia" in query.lower()
    
    def test_extract_location_none(self, parser):
        """Test when no location is found"""
        query, location = parser._extract_location("hamburguesas mcdonald's")
        assert location is None
        assert query == "hamburguesas mcdonald's"

        query, location = parser._extract_location("hamburguesas av irarrazabal")
        assert location is None
        assert query == "hamburguesas av irarrazabal"
    
    def test_normalize_location(self, parser):
        """Test location normalization"""
        # Test exact match
        assert parser._normalize_location("providencia") == "Providencia"
        assert parser._normalize_location("Providencia") == "Providencia"
        
        # Test alias matching
        assert parser._normalize_location("nunoa") == "Ñuñoa"
        assert parser._normalize_location("maipu") == "Maipú"
        assert parser._normalize_location("lascondes") == "Las Condes"
        
        # Test unknown location
        assert parser._normalize_location("Unknown Location") == "Unknown Location"
    
    def test_check_ranking_filter_best_only(self, parser):
        """Test ranking filter detection - best only"""
        assert parser._check_ranking_filter("mejores hamburguesas") == False
        assert parser._check_ranking_filter("best restaurants") == False
        assert parser._check_ranking_filter("buenos completos") == False
    
    def test_check_ranking_filter_worst_only(self, parser):
        """Test ranking filter detection - worst only"""
        assert parser._check_ranking_filter("peores hamburguesas") == False
        assert parser._check_ranking_filter("worst restaurants") == False
        assert parser._check_ranking_filter("malos completos") == False
    
    def test_check_ranking_filter_best_and_worst(self, parser):
        """Test ranking filter detection - best and worst (bonus feature)"""
        assert parser._check_ranking_filter("mejores y peores hamburguesas") == True
        assert parser._check_ranking_filter("best and worst restaurants") == True
        assert parser._check_ranking_filter("buenos y malos completos") == True
        assert parser._check_ranking_filter("mejores y peores") == True
    
    def test_check_ranking_filter_none(self, parser):
        """Test ranking filter detection - no ranking words"""
        assert parser._check_ranking_filter("hamburguesas en santiago") == False
        assert parser._check_ranking_filter("completos dominó") == False
    
    def test_parse_query_complete_example(self, parser):
        """Test complete query parsing"""
        query = "Hamburguesas McDonald's en Puente Alto"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        assert food_type == RestaurantType.HAMBURGUESAS
        assert location == "Puente Alto"
        assert best_worst == False
        assert "mcdonald's" in new_query.lower()
        assert "en Puente Alto" not in new_query.lower()
        assert "puente alto" in new_query.lower()
    
    def test_parse_query_bonus_example(self, parser):
        """Test complete query parsing - Bonus example"""
        query = "los mejores y peores Completos Dominó Fuente de Soda Mall Plaza Norte"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        assert food_type == RestaurantType.COMPLETOS
        assert location is None  # "Mall Plaza Norte" is not in location keywords
        assert best_worst == True  # Should detect best and worst
        assert "los mejores y peores" in new_query.lower()
        assert "completos" not in new_query.lower()
        assert "dominó fuente de soda mall plaza norte" in new_query.lower()
    
    def test_parse_query_complex_location(self, parser):
        """Test parsing with complex location patterns"""
        # Test with "en" pattern
        query = "hamburguesas en huechuraba"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        assert location == "Huechuraba"
        assert food_type == RestaurantType.HAMBURGUESAS
        
        # Test with "en la comuna de" pattern
        query = "pizzas en la comuna de maipú"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        assert location == "Maipú"
        assert food_type == RestaurantType.PIZZAS
    
    def test_parse_query_case_insensitive(self, parser):
        """Test that parsing is case insensitive"""
        query = "HAMBURGUESAS MCDONALD'S EN PUENTE ALTO"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        assert food_type == RestaurantType.HAMBURGUESAS
        assert location == "Puente Alto"
        assert "mcdonald's" in new_query.lower()
        assert "puente alto" in new_query.lower()
    
    def test_parse_query_multiple_food_types(self, parser):
        """Test parsing when multiple food type keywords are present"""
        query = "hamburguesas y pizzas en la florida"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        # Should match the first one found
        assert food_type in [RestaurantType.HAMBURGUESAS, RestaurantType.PIZZAS]
        assert location == "La Florida"  # "la florida" should be detected as location
    
    def test_parse_query_no_matches(self, parser):
        """Test parsing when no patterns match"""
        query = "restaurante genérico en lugar desconocido"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        assert food_type is None
        assert location == "Lugar Desconocido"  # Should extract multi-word location with title case
        assert best_worst == False
    
    def test_parse_query_special_characters(self, parser):
        """Test parsing with special characters and accents"""
        query = "completos en ñuñoa"
        new_query, food_type, location, best_worst = parser.parse_query(query)
        
        assert food_type == RestaurantType.COMPLETOS
        assert location == "Ñuñoa"

    def test_parse_query_special_location(self, parser):
        """Test parsing with special location names"""
        query = "hamburguesas en santiago"
        new_query, food_type, location, best_worst = parser.parse_query(query)

        assert location == "Santiago Centro"
        assert food_type == RestaurantType.HAMBURGUESAS
    
    def test_parse_query_brand_names(self, parser):
        """Test parsing with specific brand names"""
        queries = [
            "McDonald's en Las Condes",
            "Burger King Providencia", 
            "Wendy's Mall Plaza Norte",
            "Dominó Fuente de Soda Centro",
            "Pedro Juan & Diego Bellavista",
            "Papa Johns Santiago"
        ]
        
        for query in queries:
            new_query, food_type, location, best_worst = parser.parse_query(query)
            # Should parse without errors
            assert isinstance(new_query, str)
            assert best_worst == False


if __name__ == "__main__":
    pytest.main([__file__]) 