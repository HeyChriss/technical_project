from typing import List, Tuple
from itertools import combinations_with_replacement
from src.models.vehicle import Vehicle, VehicleRequest
from src.models.listing import Listing


class BinPackingSolver:
    
    def can_fit_vehicles_in_listing(self, listing: Listing, vehicles: List[Vehicle]) -> bool:
        if not vehicles:
            return True
        
        total_length_1 = sum(v.length for v in vehicles)
        max_width_1 = max(v.width for v in vehicles)
        fits_orientation_1 = (total_length_1 <= listing.length and 
                             max_width_1 <= listing.width)
        
        total_length_2 = sum(v.width for v in vehicles)
        max_width_2 = max(v.length for v in vehicles)
        fits_orientation_2 = (total_length_2 <= listing.length and 
                             max_width_2 <= listing.width)
        
        return fits_orientation_1 or fits_orientation_2
    
    def expand_vehicle_requests(self, requests: List[VehicleRequest]) -> List[Vehicle]:
        vehicles = []
        for request in requests:
            for _ in range(request.quantity):
                vehicles.append(Vehicle(length=request.length))
        return vehicles
    
    def find_cheapest_combination(
        self,
        listings: List[Listing], 
        vehicles: List[Vehicle]
    ) -> Tuple[List[Listing], int] | None:
        if not vehicles:
            return ([], 0)
        
        num_vehicles = len(vehicles)
        sorted_listings = sorted(listings, key=lambda x: x.price_in_cents)
        best_combination = None
        best_cost = float('inf')
        
        for num_listings in range(1, min(num_vehicles + 1, len(sorted_listings) + 1)):
            for listing_combo in combinations_with_replacement(
                range(len(sorted_listings)), num_listings
            ):
                selected_listings = [sorted_listings[i] for i in listing_combo]
                assignment = self._try_assign_vehicles(selected_listings, vehicles)
                
                if assignment:
                    used_listings, total_cost = assignment
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_combination = (used_listings, total_cost)
                        if num_listings == 1 or len(used_listings) <= num_listings:
                            return best_combination
        
        return best_combination
    
    def _try_assign_vehicles(
        self,
        listings: List[Listing], 
        vehicles: List[Vehicle]
    ) -> Tuple[List[Listing], int] | None:
        listings_dict = {listing.id: listing for listing in listings}
        vehicle_groups = {}
        for vehicle in vehicles:
            key = (vehicle.length, vehicle.width)
            if key not in vehicle_groups:
                vehicle_groups[key] = []
            vehicle_groups[key].append(vehicle)
        
        used_listings_map = {}
        
        for group_key, group_vehicles in vehicle_groups.items():
            for vehicle in group_vehicles:
                assigned = False
                
                for listing_id, assigned_vehicles in used_listings_map.items():
                    listing = listings_dict[listing_id]
                    test_vehicles = assigned_vehicles + [vehicle]
                    
                    if self.can_fit_vehicles_in_listing(listing, test_vehicles):
                        assigned_vehicles.append(vehicle)
                        assigned = True
                        break
                
                if not assigned:
                    for listing in listings:
                        if listing.id not in used_listings_map:
                            if self.can_fit_vehicles_in_listing(listing, [vehicle]):
                                used_listings_map[listing.id] = [vehicle]
                                assigned = True
                                break
                
                if not assigned:
                    return None
        
        used_listings = [listings_dict[lid] for lid in used_listings_map.keys()]
        total_cost = sum(l.price_in_cents for l in used_listings)
        
        return (used_listings, total_cost)

