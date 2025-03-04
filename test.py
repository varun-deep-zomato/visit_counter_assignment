import asyncio
import httpx
import pytest
from collections import defaultdict

# Test configuration
BASE_URL = "http://localhost:8000/api/v1/counter"
TEST_URLS = [
    "example.com",
    "test.com",
    "sample.org",
    "demo.net"
]
CONCURRENT_REQUESTS = 50

@pytest.mark.asyncio
async def test_visit_counter_distribution():
    """Test the distribution of visits across Redis nodes"""
    async with httpx.AsyncClient() as client:
        # Track which Redis node handles each URL
        url_distribution = defaultdict(set)
        
        # Make concurrent requests for each test URL
        for url in TEST_URLS:
            tasks = []
            for _ in range(CONCURRENT_REQUESTS):
                tasks.append(
                    client.post(
                        f"{BASE_URL}/visit/{url}"
                    )
                )
            
            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)
            
            # Verify responses and track distribution
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "visits" in data
                assert isinstance(data["visits"], int)
                assert data["visits"] > 0
                
                # Track which Redis node handled this URL
                if "redis_node" in data:
                    url_distribution[url].add(data["redis_node"])
        
        # Verify consistent hashing - each URL should always use the same Redis node
        for url, nodes in url_distribution.items():
            assert len(nodes) == 1, f"URL {url} was handled by multiple nodes: {nodes}"
        
        # Verify distribution across nodes
        all_nodes = set()
        for nodes in url_distribution.values():
            all_nodes.update(nodes)
        
        # We should be using both Redis nodes
        assert len(all_nodes) > 1, "All URLs are being handled by a single Redis node"
