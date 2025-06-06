from pydantic import BaseModel
from typing import List, Optional, TypedDict
from enum import Enum

class RestaurantType(str, Enum):
    HAMBURGUESAS = "Hamburguesas"
    COMPLETOS = "Completos"
    PIZZAS = "Pizzas"

class Restaurant(BaseModel):
    name: str
    street: str
    municipality: str
    full_address: str
    score: float
    type: RestaurantType

class QueryMessage(BaseModel):
    type: str
    message: str

class RestaurantResponse(BaseModel):
    type: str = "response"
    restaurants: List[Restaurant]
    explanation: str

class AgentState(TypedDict):
    """State model for the LangGraph agent"""
    user_query: str
    parsed_food_type: Optional[RestaurantType]
    parsed_location: Optional[str]
    filtered_restaurants: List[Restaurant]
    response_explanation: str
    best_and_worst_filter: bool 