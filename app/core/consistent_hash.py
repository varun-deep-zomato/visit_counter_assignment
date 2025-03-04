import hashlib
from typing import List, Dict, Any
from bisect import bisect

class ConsistentHash:
    def __init__(self, nodes: List[str], virtual_nodes: int = 100):
        """
        Initialize the consistent hash ring
        
        Args:
            nodes: List of node identifiers (parsed from comma-separated string)
            virtual_nodes: Number of virtual nodes per physical node
        """
        self.virtual_nodes = virtual_nodes
        self.hash_ring = {}
        self.sorted_keys = []
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: str) -> None:
        """
        Add a new node to the hash ring
        
        Args:
            node: Node identifier to add
        """
        for i in range(self.virtual_nodes):
            virtual_node = f"{node}:{i}"
            key = self.hash(virtual_node)
            self.hash_ring[key] = node
            self.sorted_keys.append(key)
        self.sorted_keys.sort()

    def remove_node(self, node: str) -> None:
        """
        Remove a node from the hash ring
        
        Args:
            node: Node identifier to remove
        """
        for i in range(self.virtual_nodes):
            virtual_node = f"{node}:{i}"
            key = self.hash(virtual_node)
            if key in self.hash_ring:
                del self.hash_ring[key]
                self.sorted_keys.remove(key)

    def get_node(self, key: str) -> str:
        """
        Get the node responsible for the given key
        
        Args:
            key: The key to look up
            
        Returns:
            The node responsible for the key
        """
        if not self.hash_ring:
            raise Exception("Hash ring is empty")
        hash_key = self.hash(key)
        low = 0
        high = len(self.sorted_keys) - 1

        while low <= high:
            mid = (low + high) // 2
            if self.sorted_keys[mid] < hash_key:
                low = mid + 1
            else:
                high = mid - 1
    
        if low == len(self.sorted_keys):
            low = 0
        return self.hash_ring[self.sorted_keys[low]]
    
    def hash(self, key: str) -> int:
        """
        Hash function for keys
        
        Args:
            key: The key to hash
            
        Returns:
            Integer hash value
        """
        return int(hashlib.md5(key.encode()).hexdigest(), 16)