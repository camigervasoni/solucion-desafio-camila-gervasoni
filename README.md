# Challenge

### Description of the code

Este repositorio es la resolución del Challenge propuesto. Implementa una aplicación FastAPI para un chatbot de recomendación de restaurantes. El sistema utiliza LangGraph para definir un flujo de trabajo agentico que procesa consultas de usuario, busca restaurantes en una base de datos vectorial Milvus y genera respuestas amigables. El frontend es una interfaz de chat simple en HTML/JS que se comunica con el backend mediante WebSockets.

### Solution

La solución se completó abordando todos los TODOs en el código inicial y verificando su funcionamiento con las pruebas proporcionadas.

#### TODOs in ```milvus_client.py```:

Este código define el esquema para la colección de Milvus, especificando los campos y tipos de datos de cada restaurante. Seleccioné estos campos después de investigar sobre Milvus y revisar tanto la estructura de los datos crudos como el modelo Restaurant.
```python
# TODO✅: Add fields to schema
schema.add_field(field_name="name", datatype=DataType.VARCHAR, max_length=256)
schema.add_field(field_name="street", datatype=DataType.VARCHAR, max_length=512)
schema.add_field(field_name="municipality", datatype=DataType.VARCHAR, max_length=256)
schema.add_field(field_name="full_address", datatype=DataType.VARCHAR, max_length=512)
schema.add_field(field_name="score", datatype=DataType.FLOAT)
schema.add_field(field_name="type", datatype=DataType.VARCHAR, max_length=64)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.dimension)
```

Este código extrae los detalles de la dirección de los datos crudos, crea un objeto Restaurant para cada entrada y lo agrega a la lista.
```python
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
```

Este código formatea los datos de cada restaurante como un diccionario y los agrega a la lista para la inserción en las colecciones.
```python
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
```

Este código convierte cada resultado de búsqueda en un objeto Restaurant y lo agrega a la lista.
```python
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
```

#### TODOs in ```query_parser.py```:
 
Esta función retorna True si la consulta menciona tanto las keywords de mejores como de peores resultados.

```python
def _check_ranking_filter(self, query: str) -> bool:
    """Check if query asks for best and worst restaurants"""
    # TODO✅: Implement this
    query_lower = query.lower()
    has_best = any(keyword in query_lower for keyword in self.ranking_keywords['best'])
    has_worst = any(keyword in query_lower for keyword in self.ranking_keywords['worst'])
    return has_best and has_worst
```

#### TODOs in ```restaurant_agent.py```:

Este código añade cada paso del proceso como nodos en el flujo de trabajo de LangGraph y los ordena usando edges. Como no había usado LangGraph antes, lo investigue para entender cómo implementarlo.

```python 
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
```

Esta línea ejecuta el workflow desde el estado inicial y retorna el resultado final.
```python
# Run the workflow
# TODO✅: Invoke the workflow
final_state = self.workflow.invoke(initial_state)
```

Este código ordena los restaurantes por puntaje en orden descendente para mostrar primero las mejores opciones. Decidí retornar los 3 mejores y los 3 peores restaurantes (sin duplicados) cuando el filtro best_and_worst_filter está activo; de lo contrario, se mantienen todos los restaurantes ordenados por puntaje.

```python
# Apply best and worst filter (bonus feature)
# Order restaurants by score descending
sorted_restaurants = sorted(restaurants, key=lambda r: getattr(r, "score", 0) or 0, reverse=True)
            
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

```

### BONUS
- ¿Cuál es el impacto de usar un filtro en Milvus? ¿Qué cambios harías para mejorar los resultados considerando el rendimiento? \
El uso de filtros mejora la precisión de las búsquedas al limitar los resultados a condiciones específicas, en este caso la ubicación, pero puede afectar el rendimiento si se utilizan expresiones como ```like```, que no son optimizadas para grandes volúmenes de datos. Para mejorar los resultados, se recomienda normalizar los valores filtrados, para poder usar comparaciones exactas cuando sea posible y considerar incluir la ubicación dentro del texto vectorizado para aprovechar la búsqueda semántica.

- ¿Qué cambios harías en el esquema de la base de datos vectorial para que entregue resultados más precisos?\
Actualmente, en la base de datos se crea una colección por cada tipo de comida (Hamburguesas, Pizzas, Completos), lo que limita las búsquedas a una categoría a la vez y complica la escalabilidad. Para mejorar la precisión y flexibilidad, unificaría todas las entradas en una sola colección y usaría el campo type como filtro. Esto permitiría realizar búsquedas cruzadas entre distintos tipos de comida, agregar nuevos tipos y realizar consultas más complejas.

- Durante el proceso de embedding, ¿Cómo influye el largo del contenido a transformar en vector en la búsqueda vectorial? \
El largo del contenido impacta la calidad del embedding, en particular textos muy cortos pueden ser poco informativos y textos muy largos pueden contener ruido y generar confusión al modelo. Idealmente, se debe usar contenido conciso pero representativo para generar vectores más útiles en la búsqueda vectorial.

- Extiende el sistema para permitir al usuario preguntar por los mejores y peores restaurantes en una categoría específica (Prueba con "los mejores y peores Completos Dominó Fuente de Soda Mall Plaza Norte") (+0.5 puntos)
Está realizado el bonus en el último TO DO de la sección anterior.
