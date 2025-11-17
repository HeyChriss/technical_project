import json
from typing import List, Dict
from pathlib import Path
from src.models.listing import Listing


class ListingLoader:
    """Service to load and manage listings."""
    
    def __init__(self, listings_path: str = "listings.json"):
        self.listings_path = listings_path
        self._listings_cache: List[Listing] = []
        self._locations_cache: Dict[str, List[Listing]] = {}
    
    def load_listings(self) -> List[Listing]:
        if self._listings_cache:
            return self._listings_cache
        
        path = Path(self.listings_path)
        if not path.exists():
            raise FileNotFoundError(f"Listings file not found: {self.listings_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        self._listings_cache = [Listing(**listing) for listing in data]
        return self._listings_cache
    
    def get_listings_by_location(self) -> Dict[str, List[Listing]]:
        if self._locations_cache:
            return self._locations_cache
        
        listings = self.load_listings()
        
        for listing in listings:
            if listing.location_id not in self._locations_cache:
                self._locations_cache[listing.location_id] = []
            self._locations_cache[listing.location_id].append(listing)
        
        return self._locations_cache

