import pytest
import json
from pathlib import Path
from pydantic import ValidationError
from src.models.vehicle import VehicleRequest, Vehicle
from src.models.listing import Listing, LocationResult
from src.services.bin_packing import BinPackingSolver
from src.services.listing_loader import ListingLoader
from src.services.search_service import SearchService

from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestVehicleRequest:
    def test_valid_vehicle_request(self):
        request = VehicleRequest(length=20, quantity=2)
        assert request.length == 20
        assert request.quantity == 2
    
    def test_vehicle_request_invalid_length(self):
        with pytest.raises(ValidationError):
            VehicleRequest(length=0, quantity=1)
        with pytest.raises(ValidationError):
            VehicleRequest(length=-10, quantity=1)
    
    def test_vehicle_request_invalid_quantity(self):
        with pytest.raises(ValidationError):
            VehicleRequest(length=10, quantity=0)
        with pytest.raises(ValidationError):
            VehicleRequest(length=10, quantity=-1)


class TestVehicle:
    def test_valid_vehicle(self):
        vehicle = Vehicle(length=25)
        assert vehicle.length == 25
        assert vehicle.width == 10
    
    def test_vehicle_with_custom_width(self):
        vehicle = Vehicle(length=20, width=15)
        assert vehicle.length == 20
        assert vehicle.width == 15


class TestListing:
    def test_valid_listing(self):
        listing = Listing(
            id="abc123",
            length=30,
            width=20,
            location_id="loc456",
            price_in_cents=1500
        )
        assert listing.id == "abc123"
        assert listing.length == 30
        assert listing.width == 20
        assert listing.location_id == "loc456"
        assert listing.price_in_cents == 1500
    
    def test_listing_invalid_dimensions(self):
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=0,
                width=20,
                location_id="loc",
                price_in_cents=100
            )
    
    def test_listing_negative_price(self):
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=10,
                width=20,
                location_id="loc",
                price_in_cents=-100
            )
    
    def test_listing_not_multiple_of_10(self):
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=15,
                width=20,
                location_id="loc",
                price_in_cents=100
            )
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=10,
                width=25,
                location_id="loc",
                price_in_cents=100
            )
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=13,
                width=20,
                location_id="loc",
                price_in_cents=100
            )
        with pytest.raises(ValidationError):
            Listing(
                id="abc",
                length=10,
                width=17,
                location_id="loc",
                price_in_cents=100
            )


class TestLocationResult:
    def test_valid_location_result(self):
        result = LocationResult(
            location_id="loc123",
            listing_ids=["list1", "list2"],
            total_price_in_cents=3000
        )
        assert result.location_id == "loc123"
        assert result.listing_ids == ["list1", "list2"]
        assert result.total_price_in_cents == 3000
    
    def test_empty_listing_ids(self):
        result = LocationResult(
            location_id="loc123",
            listing_ids=[],
            total_price_in_cents=0
        )
        assert result.listing_ids == []


class TestBinPackingSolver:
    def setup_method(self):
        self.solver = BinPackingSolver()
    
    def test_can_fit_vehicles_in_listing_single_vehicle(self):
        listing = Listing(
            id="1", length=30, width=20,
            location_id="loc1", price_in_cents=1000
        )
        vehicles = [Vehicle(length=20, width=10)]
        assert self.solver.can_fit_vehicles_in_listing(listing, vehicles) is True
    
    def test_can_fit_vehicles_in_listing_multiple_vehicles(self):
        listing = Listing(
            id="1", length=50, width=20,
            location_id="loc1", price_in_cents=2000
        )
        vehicles = [
            Vehicle(length=20, width=10),
            Vehicle(length=20, width=10)
        ]
        assert self.solver.can_fit_vehicles_in_listing(listing, vehicles) is True
    
    def test_cannot_fit_vehicles_in_listing(self):
        listing = Listing(
            id="1", length=30, width=10,
            location_id="loc1", price_in_cents=1000
        )
        vehicles = [
            Vehicle(length=20, width=10),
            Vehicle(length=20, width=10)
        ]
        assert self.solver.can_fit_vehicles_in_listing(listing, vehicles) is False
    
    def test_expand_vehicle_requests(self):
        requests = [
            VehicleRequest(length=10, quantity=1),
            VehicleRequest(length=20, quantity=2)
        ]
        vehicles = self.solver.expand_vehicle_requests(requests)
        assert len(vehicles) == 3
        assert vehicles[0].length == 10
        assert vehicles[1].length == 20
        assert vehicles[2].length == 20
        assert all(v.width == 10 for v in vehicles)
    
    def test_find_cheapest_combination_single_listing(self):
        listings = [
            Listing(
                id="1", length=50, width=20,
                location_id="loc1", price_in_cents=1000
            ),
            Listing(
                id="2", length=60, width=30,
                location_id="loc1", price_in_cents=1500
            )
        ]
        vehicles = [Vehicle(length=20, width=10)]
        result = self.solver.find_cheapest_combination(listings, vehicles)
        assert result is not None
        used_listings, total_cost = result
        assert len(used_listings) == 1
        assert used_listings[0].id == "1"
        assert total_cost == 1000
    
    def test_find_cheapest_combination_multiple_listings(self):
        listings = [
            Listing(
                id="1", length=30, width=20,
                location_id="loc1", price_in_cents=500
            ),
            Listing(
                id="2", length=30, width=20,
                location_id="loc1", price_in_cents=600
            ),
            Listing(
                id="3", length=60, width=20,
                location_id="loc1", price_in_cents=2000
            )
        ]
        vehicles = [
            Vehicle(length=20, width=10),
            Vehicle(length=20, width=10)
        ]
        result = self.solver.find_cheapest_combination(listings, vehicles)
        assert result is not None
        used_listings, total_cost = result
        assert total_cost <= 2000
    
    def test_find_cheapest_combination_impossible(self):
        listings = [
            Listing(
                id="1", length=10, width=10,
                location_id="loc1", price_in_cents=500
            )
        ]
        vehicles = [Vehicle(length=20, width=10)]
        result = self.solver.find_cheapest_combination(listings, vehicles)
        assert result is None
    
    def test_find_cheapest_combination_empty_vehicles(self):
        listings = [
            Listing(
                id="1", length=30, width=20,
                location_id="loc1", price_in_cents=1000
            )
        ]
        vehicles = []
        result = self.solver.find_cheapest_combination(listings, vehicles)
        assert result is not None
        used_listings, total_cost = result
        assert len(used_listings) == 0
        assert total_cost == 0


class TestListingLoader:
    def test_load_listings_success(self, tmp_path):
        listings_data = [
            {
                "id": "1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            },
            {
                "id": "2",
                "length": 40,
                "width": 30,
                "location_id": "loc2",
                "price_in_cents": 1500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        listings = loader.load_listings()
        assert len(listings) == 2
        assert all(isinstance(l, Listing) for l in listings)
        assert listings[0].id == "1"
        assert listings[1].id == "2"
    
    def test_load_listings_file_not_found(self):
        loader = ListingLoader("nonexistent.json")
        with pytest.raises(FileNotFoundError):
            loader.load_listings()
    
    def test_load_listings_caching(self, tmp_path):
        listings_data = [
            {
                "id": "1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        listings1 = loader.load_listings()
        listings2 = loader.load_listings()
        assert listings1 is listings2
    
    def test_get_listings_by_location(self, tmp_path):
        listings_data = [
            {
                "id": "1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            },
            {
                "id": "2",
                "length": 40,
                "width": 30,
                "location_id": "loc1",
                "price_in_cents": 1500
            },
            {
                "id": "3",
                "length": 30,
                "width": 20,
                "location_id": "loc2",
                "price_in_cents": 1200
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        locations = loader.get_listings_by_location()
        assert len(locations) == 2
        assert "loc1" in locations
        assert "loc2" in locations
        assert len(locations["loc1"]) == 2
        assert len(locations["loc2"]) == 1
    
    def test_get_listings_by_location_caching(self, tmp_path):
        listings_data = [
            {
                "id": "1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        locations1 = loader.get_listings_by_location()
        locations2 = loader.get_listings_by_location()
        assert locations1 is locations2
    
    def test_load_listings_not_multiple_of_10(self, tmp_path):
        listings_data = [
            {
                "id": "1",
                "length": 15,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        with pytest.raises(ValidationError):
            loader.load_listings()


class TestSearchService:
    def test_search_locations_single_vehicle(self, tmp_path):
        listings_data = [
            {
                "id": "list1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            },
            {
                "id": "list2",
                "length": 40,
                "width": 30,
                "location_id": "loc2",
                "price_in_cents": 1500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        service = SearchService(loader)
        requests = [VehicleRequest(length=10, quantity=1)]
        results = service.search_locations(requests)
        assert len(results) > 0
        for i in range(len(results) - 1):
            assert results[i].total_price_in_cents <= results[i + 1].total_price_in_cents
    
    def test_search_locations_multiple_vehicles(self, tmp_path):
        listings_data = [
            {
                "id": "list1",
                "length": 60,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 2000
            },
            {
                "id": "list2",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 800
            },
            {
                "id": "list3",
                "length": 50,
                "width": 20,
                "location_id": "loc2",
                "price_in_cents": 2500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        service = SearchService(loader)
        requests = [
            VehicleRequest(length=10, quantity=1),
            VehicleRequest(length=20, quantity=1)
        ]
        results = service.search_locations(requests)
        assert len(results) > 0
        for result in results:
            assert result.location_id
            assert len(result.listing_ids) > 0
            assert result.total_price_in_cents > 0
    
    def test_search_locations_no_matches(self, tmp_path):
        listings_data = [
            {
                "id": "list1",
                "length": 10,
                "width": 10,
                "location_id": "loc1",
                "price_in_cents": 500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        service = SearchService(loader)
        requests = [VehicleRequest(length=50, quantity=1)]
        results = service.search_locations(requests)
        assert len(results) == 0
    
    def test_search_locations_one_result_per_location(self, tmp_path):
        listings_data = [
            {
                "id": "list1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 1000
            },
            {
                "id": "list2",
                "length": 40,
                "width": 30,
                "location_id": "loc1",
                "price_in_cents": 1500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        service = SearchService(loader)
        requests = [VehicleRequest(length=10, quantity=1)]
        results = service.search_locations(requests)
        location_ids = [r.location_id for r in results]
        assert len(location_ids) == len(set(location_ids))
    
    def test_search_locations_sorted_by_price(self, tmp_path):
        listings_data = [
            {
                "id": "list1",
                "length": 30,
                "width": 20,
                "location_id": "loc1",
                "price_in_cents": 2000
            },
            {
                "id": "list2",
                "length": 30,
                "width": 20,
                "location_id": "loc2",
                "price_in_cents": 1000
            },
            {
                "id": "list3",
                "length": 30,
                "width": 20,
                "location_id": "loc3",
                "price_in_cents": 1500
            }
        ]
        listings_file = tmp_path / "listings.json"
        with open(listings_file, 'w') as f:
            json.dump(listings_data, f)
        loader = ListingLoader(str(listings_file))
        service = SearchService(loader)
        requests = [VehicleRequest(length=10, quantity=1)]
        results = service.search_locations(requests)
        prices = [r.total_price_in_cents for r in results]
        assert prices == sorted(prices)


class TestAPI:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_search_valid_request(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 1
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            result = data[0]
            assert "location_id" in result
            assert "listing_ids" in result
            assert "total_price_in_cents" in result
    
    def test_search_multiple_vehicles(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 1
            },
            {
                "length": 20,
                "quantity": 2
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_exceeds_max_quantity(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 6
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]
    
    def test_search_total_quantity_exceeds_5(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 3
            },
            {
                "length": 20,
                "quantity": 3
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]
    
    def test_search_quantity_equals_5(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 5
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
    
    def test_search_empty_request(self, client):
        response = client.post("/", json=[])
        assert response.status_code == 400
        assert "At least one vehicle" in response.json()["detail"]
    
    def test_search_invalid_length(self, client):
        request_data = [
            {
                "length": 0,
                "quantity": 1
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 422
    
    def test_search_invalid_quantity(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 0
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 422
    
    def test_search_missing_fields(self, client):
        request_data = [
            {
                "length": 10
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 422
    
    def test_search_results_sorted_by_price(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 1
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 1:
            prices = [item["total_price_in_cents"] for item in data]
            assert prices == sorted(prices)
    
    def test_search_returns_listing_ids(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 1
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            result = data[0]
            assert isinstance(result["listing_ids"], list)
            assert len(result["listing_ids"]) > 0
    
    def test_search_with_real_listings(self, client):
        request_data = [
            {
                "length": 10,
                "quantity": 1
            }
        ]
        response = client.post("/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 365, f"Expected at least 365 results, got {len(data)}"
        
        # Verify the structure of each result
        for result in data:
            assert "location_id" in result
            assert "listing_ids" in result
            assert "total_price_in_cents" in result
            assert isinstance(result["location_id"], str)
            assert isinstance(result["listing_ids"], list)
            assert isinstance(result["total_price_in_cents"], int)
            assert len(result["listing_ids"]) > 0
        
        # Verify results are sorted by price (ascending)
        prices = [item["total_price_in_cents"] for item in data]
        assert prices == sorted(prices), "Results should be sorted by price in ascending order"
        
        # Verify the first result matches the expected structure from the example
        first_result = data[0]
        assert first_result["location_id"] == "42b8f068-2d13-4ed1-8eec-c98f1eef0850"
        assert first_result["listing_ids"] == ["b9bbe25f-5679-4917-bd7b-1e19c464f3a8"]
        assert first_result["total_price_in_cents"] == 1005
        
        # Verify the second result matches the expected structure from the example
        second_result = data[1]
        assert second_result["location_id"] == "507628b8-163e-4e22-a6a3-6a16f8188928"
        assert second_result["listing_ids"] == ["e7d59481-b804-4565-b49b-d5beb7aec350"]
        assert second_result["total_price_in_cents"] == 1088
        
        # Verify the last result matches the expected structure from the example
        last_result = data[-1]
        assert last_result["location_id"] == "22ad1ab7-d49b-49d6-8c30-531599934639"
        assert last_result["listing_ids"] == ["20cf6f5e-eb47-4104-b1f9-62527760a4c0"]
        assert last_result["total_price_in_cents"] == 99303

    def test_search_benchmark(self, client, benchmark):
        request_data = [{"length": 10, "quantity": 5}]
    
        response = benchmark(client.post, "/", json=request_data)
        assert response.status_code == 200
        
        mean_time_ms = benchmark.stats.stats.mean
        assert mean_time_ms < 300, f"Mean response time {mean_time_ms:.2f}ms exceeds 300ms threshold"

