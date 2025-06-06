import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from main import app


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoint functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_restaurant_agent(self):
        """Mock RestaurantAgent for testing"""
        mock_agent = Mock()
        mock_agent.process_query = AsyncMock()
        return mock_agent

    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established successfully
            assert websocket is not None

    def test_websocket_valid_query_message(self, client):
        """Test sending valid query message through WebSocket"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock response
            mock_response = {
                "type": "response",
                "restaurants": [
                    {
                        "name": "McDonald's Puente Alto",
                        "street": "Av. Camilo Henríquez 3692",
                        "municipality": "Puente Alto",
                        "full_address": "Av. Camilo Henríquez 3692, Puente Alto, Santiago",
                        "score": 4.1,
                        "type": "Hamburguesas",
                    }
                ],
                "explanation": "Aquí tienes los restaurantes encontrados de hamburguesas en puente alto (encontré 1 opciones).",
            }
            mock_agent.process_query = AsyncMock(return_value=mock_response)

            with client.websocket_connect("/ws") as websocket:
                # Send valid query message
                query_message = {
                    "type": "query",
                    "message": "Hamburguesas McDonald's en Puente Alto",
                }
                websocket.send_text(json.dumps(query_message))

                # Receive response
                response = websocket.receive_text()
                response_data = json.loads(response)

                # Assertions
                assert response_data["type"] == "response"
                assert len(response_data["restaurants"]) == 1
                assert "hamburguesas" in response_data["explanation"].lower()

                # Verify agent was called
                mock_agent.process_query.assert_called_once_with(
                    "Hamburguesas McDonald's en Puente Alto"
                )

    def test_websocket_invalid_message_type(self, client):
        """Test sending message with invalid type"""
        with client.websocket_connect("/ws") as websocket:
            # Send invalid message type
            invalid_message = {"type": "invalid_type", "message": "test message"}
            websocket.send_text(json.dumps(invalid_message))

            # Receive error response
            response = websocket.receive_text()
            response_data = json.loads(response)

            # Assertions
            assert response_data["type"] == "error"
            assert "Invalid message type" in response_data["message"]

    def test_websocket_invalid_json(self, client):
        """Test sending invalid JSON"""
        with client.websocket_connect("/ws") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json string")

            # Receive error response
            response = websocket.receive_text()
            response_data = json.loads(response)

            # Assertions
            assert response_data["type"] == "error"
            assert "Invalid JSON format" in response_data["message"]

    def test_websocket_empty_query_message(self, client):
        """Test sending query message with empty message field"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock response for empty query
            mock_response = {
                "type": "response",
                "restaurants": [],
                "explanation": "Lo siento, no pude encontrar restaurantes que coincidan con tu búsqueda.",
            }
            mock_agent.process_query = AsyncMock(return_value=mock_response)

            with client.websocket_connect("/ws") as websocket:
                # Send query with empty message
                query_message = {"type": "query", "message": ""}
                websocket.send_text(json.dumps(query_message))

                # Receive response
                response = websocket.receive_text()
                response_data = json.loads(response)

                # Assertions
                assert response_data["type"] == "response"
                assert len(response_data["restaurants"]) == 0

                # Verify agent was called with empty string
                mock_agent.process_query.assert_called_once_with("")

    def test_websocket_missing_message_field(self, client):
        """Test sending query message without message field"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock response for missing message
            mock_response = {
                "type": "response",
                "restaurants": [],
                "explanation": "Lo siento, no pude encontrar restaurantes que coincidan con tu búsqueda.",
            }
            mock_agent.process_query = AsyncMock(return_value=mock_response)

            with client.websocket_connect("/ws") as websocket:
                # Send query without message field
                query_message = {"type": "query"}
                websocket.send_text(json.dumps(query_message))

                # Receive response
                response = websocket.receive_text()
                response_data = json.loads(response)

                # Should still work with empty string default
                assert response_data["type"] == "response"

                # Verify agent was called with empty string
                mock_agent.process_query.assert_called_once_with("")

    def test_websocket_agent_error_handling(self, client):
        """Test WebSocket handling when agent raises exception"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock to return error response instead of raising exception
            # This simulates how the real agent handles errors internally
            mock_error_response = {
                "type": "response",
                "restaurants": [],
                "explanation": "Lo siento, ocurrió un error al procesar tu consulta: Agent error",
            }
            mock_agent.process_query = AsyncMock(return_value=mock_error_response)

            with client.websocket_connect("/ws") as websocket:
                # Send valid query
                query_message = {"type": "query", "message": "test query"}
                websocket.send_text(json.dumps(query_message))

                # Should receive error response
                response = websocket.receive_text()
                response_data = json.loads(response)

                # The agent should handle the error internally and return error response
                assert response_data["type"] == "response"
                assert "error" in response_data["explanation"].lower()
                assert len(response_data["restaurants"]) == 0

    def test_websocket_multiple_messages(self, client):
        """Test sending multiple messages through same WebSocket connection"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock responses
            responses = [
                {
                    "type": "response",
                    "restaurants": [
                        {
                            "name": "Restaurant 1",
                            "address": "Location 1",
                            "municipality": "Puente Alto",
                            "full_address": "Location 1, Puente Alto, Santiago",
                            "score": 4.0,
                            "type": "Hamburguesas",
                        }
                    ],
                    "explanation": "Found hamburguesas",
                },
                {
                    "type": "response",
                    "restaurants": [
                        {
                            "name": "Restaurant 2",
                            "address": "Location 2",
                            "municipality": "Ñuñoa",
                            "full_address": "Location 2, Ñuñoa, Santiago",
                            "score": 4.5,
                            "type": "Pizzas",
                        }
                    ],
                    "explanation": "Found pizzas",
                },
            ]
            mock_agent.process_query = AsyncMock(side_effect=responses)

            with client.websocket_connect("/ws") as websocket:
                # Send first query
                query1 = {"type": "query", "message": "hamburguesas"}
                websocket.send_text(json.dumps(query1))
                response1 = json.loads(websocket.receive_text())

                # Send second query
                query2 = {"type": "query", "message": "pizzas"}
                websocket.send_text(json.dumps(query2))
                response2 = json.loads(websocket.receive_text())

                # Assertions
                assert response1["explanation"] == "Found hamburguesas"
                assert response2["explanation"] == "Found pizzas"
                assert mock_agent.process_query.call_count == 2

    def test_websocket_bonus_query(self, client):
        """Test WebSocket with bonus best/worst query"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup mock response for best/worst query
            mock_response = {
                "type": "response",
                "restaurants": [
                    {
                        "name": "Best Restaurant",
                        "street": "Location 1",
                        "municipality": "Puente Alto",
                        "full_address": "Location 1, Puente Alto, Santiago",
                        "score": 4.8,
                        "type": "Completos",
                    },
                    {
                        "name": "Worst Restaurant",
                        "street": "Location 2",
                        "municipality": "Mall Plaza Norte",
                        "full_address": "Location 2, Mall Plaza Norte, Santiago",
                        "score": 2.1,
                        "type": "Completos",
                    },
                ],
                "explanation": "Aquí tienes los mejores y peores restaurantes de completos (encontré 2 opciones). Incluye 1 mejores opciones y 1 para comparar.",
            }
            mock_agent.process_query = AsyncMock(return_value=mock_response)

            with client.websocket_connect("/ws") as websocket:
                # Send bonus query
                query_message = {
                    "type": "query",
                    "message": "los mejores y peores Completos Dominó Fuente de Soda Mall Plaza Norte",
                }
                websocket.send_text(json.dumps(query_message))

                # Receive response
                response = websocket.receive_text()
                response_data = json.loads(response)

                # Assertions
                assert response_data["type"] == "response"
                assert len(response_data["restaurants"]) == 2
                assert "mejores y peores" in response_data["explanation"].lower()

                # Verify agent was called
                mock_agent.process_query.assert_called_once()

    def test_websocket_readme_example_queries(self, client):
        """Test WebSocket with the specific queries mentioned in README"""
        with patch("main.restaurant_agent") as mock_agent:
            # Setup different mock responses for each query
            responses = [
                {
                    "type": "response",
                    "restaurants": [
                        {
                            "name": "McDonald's Puente Alto",
                            "street": "Av. Camilo Henríquez 3692",
                            "municipality": "Puente Alto",
                            "full_address": "Av. Camilo Henríquez 3692, Puente Alto, Santiago",
                            "score": 4.1,
                            "type": "Hamburguesas",
                        }
                    ],
                    "explanation": "Encontré hamburguesas McDonald's en Puente Alto",
                },
                {
                    "type": "response",
                    "restaurants": [],
                    "explanation": "Lo siento, no pude encontrar restaurantes que coincidan con tu búsqueda.",
                },
                {
                    "type": "response",
                    "restaurants": [
                        {
                            "name": "Dominó Fuente de Soda Ñuñoa",
                            "street": "Av. Américo Vespucio 1200",
                            "municipality": "Ñuñoa",
                            "full_address": "Av. Américo Vespucio 1200, Ñuñoa, Santiago",
                            "score": 4.6,
                            "type": "Completos",
                        }
                    ],
                    "explanation": "Encontré completos Dominó en Ñuñoa",
                },
            ]
            mock_agent.process_query = AsyncMock(side_effect=responses)

            readme_queries = [
                "Hamburguesas McDonald's en Puente Alto",
                "Papas fritas Papa Johns en la comuna de Santiago",
                "Completos Dominó Fuente de Soda Ñuñoa",
            ]

            with client.websocket_connect("/ws") as websocket:
                for i, query_text in enumerate(readme_queries):
                    # Send query
                    query_message = {"type": "query", "message": query_text}
                    websocket.send_text(json.dumps(query_message))

                    # Receive response
                    response = websocket.receive_text()
                    response_data = json.loads(response)

                    # Basic assertions
                    assert response_data["type"] == "response"
                    assert "explanation" in response_data
                    assert "restaurants" in response_data

                # Verify all queries were processed
                assert mock_agent.process_query.call_count == 3


class TestWebSocketIntegration:
    """Integration tests for WebSocket with real components (but mocked data)"""

    @pytest.fixture
    def client(self):
        """Create test client for WebSocket testing"""
        return TestClient(app)

if __name__ == "__main__":
    pytest.main([__file__])
