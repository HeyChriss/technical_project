from typing import List, Dict
from src.models.vehicle import VehicleRequest
from src.models.listing import Listing, LocationResult
from src.services.listing_loader import ListingLoader
from src.services.bin_packing import BinPackingSolver


class SearchService:
    """Service to search for vehicle storage locations."""
    
    def __init__(self, listing_loader: ListingLoader):

        self.listing_loader = listing_loader
        self.bin_packing_solver = BinPackingSolver()
    
    def search_locations(
        self, 
        vehicle_requests: List[VehicleRequest]
    ) -> List[LocationResult]:
        # expand the vehicle requests to individual vehicles
        vehicles = self.bin_packing_solver.expand_vehicle_requests(vehicle_requests)
        
        # get listings in the location
        locations = self.listing_loader.get_listings_by_location()
        
        # find valid locations and their cheapest combinations
        results = []
        
        for location_id, listings in locations.items():
            # find cheapest combination for the location
            combination = self.bin_packing_solver.find_cheapest_combination(
                listings, vehicles
            )
            
            if combination:
                used_listings, total_cost = combination
                result = LocationResult(
                    location_id=location_id,
                    listing_ids=[listing.id for listing in used_listings],
                    total_price_in_cents=total_cost
                )
                results.append(result)
        
        # sort by price
        results.sort(key=lambda x: x.total_price_in_cents)
        
        return results

