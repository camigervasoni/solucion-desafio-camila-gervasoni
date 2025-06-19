import logging
from langgraph.graph import StateGraph, END
from agent.models import AgentState
from agent.milvus_client import MilvusClient
from agent.query_parser import QueryParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantAgent:
    """Main restaurant agent using LangGraph for agentic workflow"""
    
    def __init__(self):
        self.milvus_client = MilvusClient()
        self.query_parser = QueryParser()
        
        # Initialize Milvus data
        self.milvus_client.load_restaurant_data()
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for restaurant search"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (steps in the workflow)
        # TODO✅: Add nodes to the workflow
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("search_restaurants", self._search_restaurants_node)
        workflow.add_node("filter_and_rank", self._filter_and_rank_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Define the workflow edges
        # TODO✅: Add edges to the workflow
        workflow.set_entry_point("parse_query")
        workflow.add_edge("parse_query", "search_restaurants")
        workflow.add_edge("search_restaurants", "filter_and_rank")
        workflow.add_edge("filter_and_rank", "generate_response")
        workflow.add_edge("generate_response", END) 
        
        return workflow.compile()
        
    def _parse_query_node(self, state: AgentState) -> AgentState:
        """Parse the user query to extract food type and location"""
        user_query = state.get("user_query", "")
        logger.info(f"Parsing original query: {user_query}")

        new_query, food_type, location, best_and_worst = self.query_parser.parse_query(user_query)

        state["user_query"] = new_query
        state["parsed_food_type"] = food_type
        state["parsed_location"] = location
        state["best_and_worst_filter"] = best_and_worst

        logger.info(f"Parsed - Query: {new_query}, Food type: {food_type}, Location: {location}, Best/Worst: {best_and_worst}")
        
        return state
        
    def _search_restaurants_node(self, state: AgentState) -> AgentState:
        """Search for restaurants using Milvus"""
        logger.info("Searching restaurants in Milvus")
        
        # Prepare search parameters
        query = state.get("user_query", "")
        food_type = state.get("parsed_food_type")
        food_type_value = food_type.value if food_type else None
        location = state.get("parsed_location")
        
        # Search restaurants
        restaurants = self.milvus_client.search_restaurants(
            query=query,
            food_type=food_type_value,
            location=location,
            limit=10
        )
        
        state["filtered_restaurants"] = restaurants
        logger.info(f"Found {len(restaurants)} restaurants")
        
        return state
        
    def _filter_and_rank_node(self, state: AgentState) -> AgentState:
        """Apply additional filtering and ranking logic"""
        logger.info("Applying filters and ranking")
        
        restaurants = state.get("filtered_restaurants", [])
        if not restaurants:
            return state
        
        # Order restaurants by score descending
        sorted_restaurants = sorted(restaurants, key=lambda r: getattr(r, "score", 0) or 0, reverse=True)
            
        # Apply best and worst filter (bonus feature)
        if state.get("best_and_worst_filter", False):
            # TODO✅: Implement this
            best = sorted_restaurants[:3]  # Top 3 best restaurants
            worst = sorted_restaurants[-3:] if len(sorted_restaurants) > 3 else [] # Top 3 worst restaurants
            # Join best and worst, ensuring no duplicates
            filtered = best + [r for r in worst if r not in best]
            state["filtered_restaurants"] = filtered
        else:
            # Keep all restaurants sorted by score
            state["filtered_restaurants"] = sorted_restaurants

        return state
        
    def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate the final response explanation"""
        logger.info("Generating response explanation")
        
        restaurants = state.get("filtered_restaurants", [])
        food_type = state.get("parsed_food_type")
        location = state.get("parsed_location")
        user_query = state.get("user_query", "")
        
        # Generate explanation based on the search results
        if not restaurants:
            state["response_explanation"] = "Lo siento, no pude encontrar restaurantes que coincidan con tu búsqueda."
        else:
            explanation_parts = []
            
            if state.get("best_and_worst_filter", False):
                explanation_parts.append("Aquí tienes los mejores y peores restaurantes")
            else:
                explanation_parts.append("Aquí tienes los restaurantes encontrados")
                
            if food_type:
                explanation_parts.append(f"de {food_type.value.lower()}")
                
            if location:
                explanation_parts.append(f"en {location}")
                
            explanation_parts.append(f"(encontré {len(restaurants)} opciones).")
            
            if state.get("best_and_worst_filter", False):
                best_count = min(3, len([r for r in restaurants if r.score >= 4.0]))
                worst_count = len(restaurants) - best_count
                explanation_parts.append(f" Incluye {best_count} mejores opciones y {worst_count} para comparar.")
            
            state["response_explanation"] = " ".join(explanation_parts)
        
        return state
        
    async def process_query(self, user_query: str) -> AgentState:
        """Process a user query through the LangGraph workflow"""
        try:
            # Create initial state as dictionary
            initial_state = {
                "user_query": user_query,
                "parsed_food_type": None,
                "parsed_location": None,
                "filtered_restaurants": [],
                "response_explanation": "",
                "best_and_worst_filter": False
            }
            
            # Run the workflow
            # TODO✅: Invoke the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Prepare response
            restaurants = final_state.get("filtered_restaurants", [])
            explanation = final_state.get("response_explanation", "No se pudo generar una explicación.")
            
            response = {
                "type": "response",
                "restaurants": [r.dict() if hasattr(r, 'dict') else r for r in restaurants],
                "explanation": explanation
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "response",
                "restaurants": [],
                "explanation": f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
            } 