import json
import logging
from typing import Dict, List
from pymilvus import (
    MilvusClient as pyMilvusClient, 
    model,
    DataType
)
from pymilvus.client.types import LoadState
from agent.models import Restaurant, RestaurantType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MilvusClient:
    def __init__(self):
        self.client = None
        self.encoder = model.DefaultEmbeddingFunction()
        self.dimension = 768  # Dimension for the embedding vectors (matches DefaultEmbeddingFunction output)

    def _initialize_client(self):
        if self.client is None:
            try:
                # Connect to Milvus server using the service name
                self.client = pyMilvusClient(
                    "./milvus.db"
                )
                logger.info("Successfully connected to Milvus server")
            except Exception as e:
                logger.error(f"Failed to connect to Milvus server: {str(e)}")
                raise
            
    def _initialize_collection(self, collection_name):
        """Initialize the restaurant collection schema"""
        if self.client is None:
            self._initialize_client()

        try:
            # Check if collection exists using MilvusClient
            if self.client.has_collection(collection_name):
                logger.info(f"Collection {collection_name} already exists. Skipping collection creation.")
                return
            
            # Create schema
            schema = pyMilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False
            )
                
            # Define collection schema
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            # TODO✅: Add fields to schema
            schema.add_field(field_name="name", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="street", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="municipality", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="full_address", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="score", datatype=DataType.FLOAT)
            schema.add_field(field_name="type", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.dimension)

            # Prepare index parameters
            # Creating a collection with index parameters 
            # loads the collection upon its creation
            index_params = self.client.prepare_index_params()

            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",
                index_name="embedding",
                nlist=1024,
                metric_type="L2"
            )

            # Create collection using MilvusClient
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params,
            )

            logger.info(f"Created new collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise RuntimeError(f"Failed to initialize collection {collection_name}: {e}") from e

    def _load_collection_in_memory(self, collection_name):
        if self.client is None:
            self._initialize_client()

        load_state = self.client.get_load_state(
            collection_name=collection_name
        )
        
        if load_state["state"] != LoadState.Loaded:
            self.client.load_collection(collection_name)
            logger.info(f"Loaded collection {collection_name} in memory")
        else:
            logger.info(f"Collection {collection_name} is already loaded in memory") 
            
    def load_restaurant_data(self):
        """Load restaurant data from JSON files into their corresponding Milvus collections"""
        try:    
            # Initialize client if not already done
            if self.client is None:
                self._initialize_client()
            
            # Mapping of JSON files to their corresponding collections
            files_and_collections = [
                ("hamburguesas.json", RestaurantType.HAMBURGUESAS),
                ("pizzas.json", RestaurantType.PIZZAS),
                ("completos.json", RestaurantType.COMPLETOS)
            ]
            
            total_loaded = 0
            
            for filename, restaurant_type in files_and_collections:
                try:
                    # Initialize the collection
                    self._initialize_collection(restaurant_type.value)
                    self._load_collection_in_memory(restaurant_type.value)

                    # Skip loading if collection has entities already
                    if self.client.get_collection_stats(restaurant_type.value)["row_count"] > 0:
                        logger.info(f"Collection {restaurant_type.value} already has entities. Skipping loading from {filename}.")
                        continue
                    
                    # Load restaurant data from JSON file
                    restaurants: List[Restaurant] = []
                    with open(filename, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        for item in data:
                            # TODO✅: Add restaurants to the list
                            # Extract street and municipality from full address
                            full_address = item.get("address")
                            street = full_address.split(",")[0] if full_address else ""
                            municipality = full_address.split(",")[1].strip() if full_address else ""
                            # Create Restaurant object
                            restaurant = Restaurant(
                                name=item.get("name"),
                                street=street,
                                municipality=municipality,
                                full_address=full_address,
                                score=item.get("score"),
                                type=restaurant_type,
                            )
                            restaurants.append(restaurant)
                    
                    if not restaurants:
                        logger.warning(f"No restaurant data found in {filename}")
                        continue
                        
                    # Prepare data for insertion into this specific collection
                    entities: List[Dict] = []
                    for restaurant in restaurants:
                        # Create embedding from name and address
                        text = f"{restaurant.name} {restaurant.full_address}"
                        embedding = self.encoder.encode_queries([text])[0]
                        
                        # TODO✅: Add entity to entities list
                        entity = {
                            "name": restaurant.name,
                            "street": restaurant.street,
                            "municipality": restaurant.municipality,
                            "full_address": restaurant.full_address,
                            "score": restaurant.score,
                            "type": restaurant.type.value,
                            "embedding": embedding
                        }
                        entities.append(entity)
                    
                    # Insert data into the specific collection
                    res = self.client.insert(
                        collection_name=restaurant_type.value,
                        data=entities
                    )
                    
                    logger.info(f"Loaded {len(restaurants)} restaurants from {filename} into collection {restaurant_type.value}")
                    total_loaded += len(restaurants)
                    
                except FileNotFoundError:
                    logger.warning(f"Could not find {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename} into collection {restaurant_type.value}: {e}")
                    # Raise exception for critical database errors
                    raise RuntimeError(f"Failed to load restaurant data from {filename}: {e}") from e
                    
            if total_loaded > 0:
                logger.info(f"Successfully loaded {total_loaded} restaurants in total across all collections")
            else:
                logger.warning("No restaurant data was loaded")
            
        except Exception as e:
            logger.error(f"Error loading restaurant data: {e}")
            raise
            
    def search_restaurants(self, query: str, food_type: str = None, location: str = None, limit: int = 10) -> List[Restaurant]:
        """Search restaurants using vector similarity and filters"""
        try:
            if food_type is None:
                return []
            
            logger.info(f"Searching for {query}")
            # Create query embedding
            query_embedding = self.encoder.encode_queries([query])
            
            # Build filter expression
            filter_expr = ""
            if location:
                location_filter = f'municipality like "%{location}%"'
                if filter_expr:
                    filter_expr += f" and {location_filter}"
                else:
                    filter_expr = location_filter

            logger.info(f"Filter expression: {filter_expr}")
                    
            # Search parameters
            search_params = {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nprobe": 10}}
            
            # Load collection
            self._load_collection_in_memory(food_type)
            
            # Perform search
            results = self.client.search(
                collection_name=food_type,
                data=query_embedding,
                filter=filter_expr if filter_expr else None,
                limit=limit,
                output_fields=["name", "street", "municipality", "full_address", "score"],            
                search_params=search_params,
                anns_field="embedding",
            )
            
            restaurants: List[Restaurant] = []
            # Determine restaurant type from collection name
            restaurant_type = RestaurantType(food_type)
            
            for hit in results[0]:
                # TODO✅: Add restaurants to the list
                restaurant = Restaurant(
                    name=hit.get("name"),
                    street=hit.get("street"),
                    municipality=hit.get("municipality"),
                    full_address=hit.get("full_address"),
                    score=hit.get("score"),
                    type=restaurant_type,
                )
                restaurants.append(restaurant)
                
            return restaurants
            
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            raise RuntimeError(f"Vector database search failed: {e}") from e
            