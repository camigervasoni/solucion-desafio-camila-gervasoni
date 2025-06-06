import asyncio
import json
from agent.restaurant_agent import RestaurantAgent


class QueryTester:
    """Test specific queries and analyze results"""
    
    def __init__(self):
        self.agent = None
        self.results = []
    
    async def initialize(self):
        """
        Initialize the restaurant agent
        You will need working Milvus integration and LangGraph workflow to pass this test.
        """
        print("🔧 Initializing RestaurantAgent...")
        try:
            self.agent = RestaurantAgent()
            print("✅ Agent initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False

    async def test_query(self, query, description="", validator=None):
        """Test a single query and store results with optional custom validation"""
        print(f"\n{'='*60}")
        print(f"🔍 TESTING: {description if description else query}")
        print(f"{'='*60}")
        print(f"Query: {query}")
        
        try:
            response = await self.agent.process_query(query)
            
            # Apply custom validation if provided
            if validator:
                expected_success, validation_passed, validation_details = validator(response)
            else:
                # Default validation - just that it executed
                expected_success = True
                validation_passed = True
                validation_details = ["Basic validation - query executed successfully"]
            
            result = {
                "query": query,
                "description": description,
                "success": True,  # Query executed without error
                "expected_success": expected_success,
                "validation_passed": validation_passed,
                "validation_details": validation_details,
                "response": response,
                "restaurant_count": len(response['restaurants']),
                "explanation": response['explanation']
            }
            
            print(f"📊 Restaurants found: {result['restaurant_count']}")
            print(f"💬 Explanation: {result['explanation']}")
            print(f"🎯 Expected behavior: {'SUCCESS' if expected_success else 'NO RESULTS'}")
            print(f"✅ Validation: {'PASS' if validation_passed else 'FAIL'}")
            
            if validation_details:
                print(f"📋 Validation Details:")
                for detail in validation_details:
                    print(f"   • {detail}")
            
            if response['restaurants']:
                print(f"\n📋 Restaurant Details:")
                for i, restaurant in enumerate(response['restaurants'][:3], 1):  # Show top 3
                    print(f"  {i}. {restaurant['name']}")
                    print(f"     Full Address: {restaurant['full_address']}")
                    print(f"     Score: {restaurant.get('score', 'N/A')}")
                    print(f"     Type: {restaurant.get('type', 'N/A')}")
                
                if len(response['restaurants']) > 3:
                    print(f"     ... and {len(response['restaurants']) - 3} more")
            else:
                print("📋 No restaurants found")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Status: ERROR - {e}")
            result = {
                "query": query,
                "description": description,
                "success": False,
                "expected_success": False,
                "validation_passed": False,
                "validation_details": [f"Query execution failed: {e}"],
                "error": str(e),
                "restaurant_count": 0,
                "explanation": f"Error: {e}"
            }
            self.results.append(result)
            return result

    async def test_mcdonalds_puente_alto(self):
        """Test Query 1: Should find McDonald's in Puente Alto"""
        query = "Hamburguesas McDonald's en Puente Alto"
        description = "Query 1 - Should find McDonald's Puente Alto"
        
        def validate_mcdonalds_puente_alto(response):
            restaurants = response.get('restaurants', [])
            restaurant_count = len(restaurants)
            expected_success = restaurant_count > 0
            validation_details = []
            
            if restaurant_count > 0:
                # Check if any restaurant contains McDonald's and Puente Alto
                mcdonalds_found = any(
                    'mcdonald' in restaurant.get('name', '').lower() or 
                    'mcdonald' in restaurant.get('full_address', '').lower()
                    for restaurant in restaurants
                )
                puente_alto_found = any(
                    'puente alto' in restaurant.get('full_address', '').lower()
                    for restaurant in restaurants
                )
                
                validation_details.append(f"McDonald's found: {mcdonalds_found}")
                validation_details.append(f"Puente Alto location found: {puente_alto_found}")
                validation_passed = mcdonalds_found and puente_alto_found
            else:
                validation_details.append("No restaurants found - expected to find McDonald's in Puente Alto")
                validation_passed = False
            
            return expected_success, validation_passed, validation_details
        
        return await self.test_query(query, description, validate_mcdonalds_puente_alto)

    async def test_papas_fritas_invalid(self):
        """Test Query 2: Should find no results (papas fritas isn't a valid food type)"""
        query = "Papas fritas Papa Johns en la comuna de Santiago"
        description = "Query 2 - Should find no results (papas fritas isn't a valid food type)"
        
        def validate_no_papas_fritas(response):
            restaurants = response.get('restaurants', [])
            restaurant_count = len(restaurants)
            expected_success = restaurant_count == 0
            validation_passed = restaurant_count == 0
            validation_details = [
                f"Expected: 0 results (papas fritas not valid food type)",
                f"Actual: {restaurant_count} results",
                f"Validation: {'PASS' if validation_passed else 'FAIL'}"
            ]
            
            return expected_success, validation_passed, validation_details
        
        return await self.test_query(query, description, validate_no_papas_fritas)

    async def test_domino_nunoa(self):
        """Test Query 3: Should find Dominó Fuente de Soda in Ñuñoa"""
        query = "Completos Dominó Fuente de Soda Ñuñoa"
        description = "Query 3 - Should find Dominó Fuente de Soda Ñuñoa"
        
        def validate_domino_nunoa(response):
            restaurants = response.get('restaurants', [])
            restaurant_count = len(restaurants)
            expected_success = restaurant_count > 0
            validation_details = []
            
            if restaurant_count > 0:
                # Check if any restaurant contains Dominó Fuente de Soda and Ñuñoa
                domino_found = any(
                    'dominó' in restaurant.get('name', '').lower() or
                    'domino' in restaurant.get('name', '').lower() or
                    'fuente de soda' in restaurant.get('name', '').lower()
                    for restaurant in restaurants
                )
                nunoa_found = any(
                    'ñuñoa' in restaurant.get('full_address', '').lower() or
                    'nunoa' in restaurant.get('full_address', '').lower()
                    for restaurant in restaurants
                )
                
                validation_details.append(f"Dominó Fuente de Soda found: {domino_found}")
                validation_details.append(f"Ñuñoa location found: {nunoa_found}")
                validation_passed = domino_found and nunoa_found
            else:
                validation_details.append("No restaurants found - expected to find Dominó Fuente de Soda in Ñuñoa")
                validation_passed = False
            
            return expected_success, validation_passed, validation_details
        
        return await self.test_query(query, description, validate_domino_nunoa)

    async def test_best_worst_completos(self):
        """Test Bonus Query: Should find both best and worst completos"""
        query = "los mejores y peores Completos Dominó Fuente de Soda Mall Plaza Norte"
        description = "BONUS - Best and worst completos"
        
        def validate_best_worst_completos(response):
            restaurants = response.get('restaurants', [])
            restaurant_count = len(restaurants)
            expected_success = restaurant_count > 0
            validation_details = []
            
            # Check if explanation contains expected text
            explanation = response.get('explanation', '')
            expected_explanation = "Aquí tienes los mejores y peores restaurantes de completos"
            explanation_valid = expected_explanation in explanation
            validation_details.append(f"Expected explanation found: {explanation_valid}")
            if not explanation_valid:
                validation_details.append(f"Expected: '{expected_explanation}'")
                validation_details.append(f"Actual explanation: '{explanation}'")
            
            validation_passed = explanation_valid
            
            if restaurant_count > 0:
                # Check if results include both high and low scored items
                scores = [r.get('score', 0) for r in restaurants if 'score' in r]
                if scores:
                    min_score = min(scores)
                    max_score = max(scores)
                    score_range = max_score - min_score
                    
                    validation_details.append(f"Score range: {min_score:.2f} to {max_score:.2f}")
                    validation_details.append(f"Score spread: {score_range:.2f}")
                    
                    # For best/worst query, we expect a reasonable spread in scores
                    score_validation = score_range > 0.5 or restaurant_count >= 2
                    validation_details.append(f"Score spread validation: {score_validation}")
                    validation_passed = validation_passed and score_validation
                else:
                    validation_details.append("No scores found in results")
                    validation_passed = False
                
                # Check if completos are found
                completos_found = any(
                    'completo' in restaurant.get('name', '').lower() or
                    'completo' in restaurant.get('type', '').lower()
                    for restaurant in restaurants
                )
                validation_details.append(f"Completos found: {completos_found}")
                
                # Update validation based on completos found too
                if not completos_found:
                    validation_passed = False
            else:
                validation_details.append("No restaurants found - expected to find best and worst completos")
                validation_passed = False
            
            return expected_success, validation_passed, validation_details
        
        return await self.test_query(query, description, validate_best_worst_completos)

    async def run_main_queries(self):
        """Test specific queries"""
        print("\n🎯 TESTING MAIN QUERIES")
        print("Testing three main queries...")
        
        await self.test_mcdonalds_puente_alto()
        await self.test_papas_fritas_invalid()
        await self.test_domino_nunoa()
    
    async def run_bonus_query(self):
        """Test the bonus best/worst query"""
        print("\n🌟 TESTING BONUS QUERY")
        
        await self.test_best_worst_completos()
    
    async def run_additional_tests(self):
        """Run additional test queries to understand the system better"""
        print("\n🔬 ADDITIONAL ANALYSIS QUERIES")
        
        additional_queries = [
            ("completos", "Test generic completos search"),
            ("hamburguesas", "Test generic hamburguesas search"),
            ("pizzas", "Test generic pizzas search"),
            ("McDonald's", "Test brand-specific search"),
            ("restaurantes en Santiago", "Test location-only search"),
            ("mejores hamburguesas", "Test 'best' only (not best AND worst)"),
            ("peores completos", "Test 'worst' only (not best AND worst)"),
        ]
        
        for query, description in additional_queries:
            await self.test_query(query, description)
    
    def analyze_results(self):
        """Analyze the test results and provide insights for bonus questions"""
        print(f"\n{'='*80}")
        print("📊 RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        # Basic statistics
        total_queries = len(self.results)
        successful_queries = sum(1 for r in self.results if r['success'])
        queries_with_results = sum(1 for r in self.results if r['success'] and r['restaurant_count'] > 0)
        validated_queries = sum(1 for r in self.results if r.get('validation_passed', False))
        
        print(f"📈 Statistics:")
        print(f"  Total queries tested: {total_queries}")
        print(f"  Successful queries (no errors): {successful_queries}")
        print(f"  Queries with results: {queries_with_results}")
        print(f"  Queries that passed validation: {validated_queries}")
        print(f"  Execution success rate: {successful_queries/total_queries*100:.1f}%")
        print(f"  Validation success rate: {validated_queries/total_queries*100:.1f}%")
        
        # Analyze main queries with detailed validation
        print(f"\n🎯 Main Query Analysis:")
        main_results = [r for r in self.results if "Query" in r.get('description', '')]
        
        for result in main_results:
            print(f"\n  {result['description']}:")
            print(f"    Query: {result['query']}")
            print(f"    Results: {result['restaurant_count']} restaurants")
            print(f"    Execution: {'✅ SUCCESS' if result['success'] else '❌ ERROR'}")
            print(f"    Validation: {'✅ PASS' if result.get('validation_passed', False) else '❌ FAIL'}")
            
            if result.get('validation_details'):
                print(f"    Details:")
                for detail in result['validation_details']:
                    print(f"      • {detail}")
        
        # Analyze bonus query
        bonus_results = [r for r in self.results if "BONUS" in r.get('description', '')]
        if bonus_results:
            print(f"\n🌟 Bonus Query Analysis:")
            for result in bonus_results:
                print(f"  {result['description']}:")
                print(f"    Query: {result['query']}")
                print(f"    Results: {result['restaurant_count']} restaurants")
                print(f"    Execution: {'✅ SUCCESS' if result['success'] else '❌ ERROR'}")
                print(f"    Validation: {'✅ PASS' if result.get('validation_passed', False) else '❌ FAIL'}")
                
                if result.get('validation_details'):
                    print(f"    Details:")
                    for detail in result['validation_details']:
                        print(f"      • {detail}")

async def main():
    """Main test runner"""
    print("🚀 RESTAURANT AGENT QUERY TESTER")
    print("Testing main queries and analyzing bonus questions...")
    
    tester = QueryTester()
    
    # Initialize
    if not await tester.initialize():
        return 1
    
    # Run all tests
    await tester.run_main_queries()
    await tester.run_bonus_query()
    await tester.run_additional_tests()
    
    # Analyze results
    tester.analyze_results()
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main())) 