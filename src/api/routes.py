from typing import List
from fastapi import APIRouter, HTTPException, Depends
from src.models.vehicle import VehicleRequest
from src.models.listing import LocationResult
from src.services.listing_loader import ListingLoader
from src.services.search_service import SearchService


router = APIRouter()


def get_search_service() -> SearchService:
    listing_loader = ListingLoader()
    return SearchService(listing_loader)


@router.post("/", response_model=List[LocationResult])
async def search_vehicle_storage(
    vehicle_requests: List[VehicleRequest],
    search_service: SearchService = Depends(get_search_service)
) -> List[LocationResult]:
    if not vehicle_requests:
        raise HTTPException(
            status_code=400,
            detail="At least one vehicle request is required"
        )
    
    total_quantity = sum(req.quantity for req in vehicle_requests)
    if total_quantity > 5:
        raise HTTPException(
            status_code=400,
            detail=f"Total quantity ({total_quantity}) exceeds maximum of 5 vehicles"
        )
    
    try:
        results = search_service.search_locations(vehicle_requests)
        return results
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during search: {str(e)}"
        )

