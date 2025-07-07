from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class DeliveryLocation:
    """Represents a delivery location with coordinates and metadata"""
    id: str
    address: str
    latitude: float
    longitude: float
    retailer_id: str
    delivery_time_window: Tuple[datetime, datetime]
    access_requirements: Dict[str, Any]

@dataclass
class SKUDeliveryInfo:
    """SKU information with delivery requirements"""
    sku_code: str
    product_name: str
    quantity: int
    weight_kg: Decimal
    volume_m3: Decimal
    temperature_requirement: Optional[str]
    fragile: bool
    delivery_locations: List[DeliveryLocation]
    retailer_orders: List[str]  # Order IDs

@dataclass
class TripRoute:
    """Optimized trip route with SKUs and delivery stops"""
    trip_id: str
    manufacturing_location_id: str
    route_stops: List[DeliveryLocation]
    sku_items: List[SKUDeliveryInfo]
    total_distance_km: float
    estimated_duration_hours: float
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    capacity_utilization: float

class TripRouteOptimizer:
    """Trip route optimization engine for SKU delivery planning"""
    
    def __init__(self):
        self.max_trip_duration = 8.0  # hours
        self.max_delivery_stops = 20
        self.sku_delivery_time_per_stop = 0.5  # hours
        self.target_sku_min = 90
        self.target_sku_max = 100
        self.max_trip_weight = 25000  # kg
        self.max_trip_volume = 100    # m3
        
    async def optimize_trip_route(self, trip_skus: List[SKUDeliveryInfo], 
                                manufacturing_location: Dict[str, Any]) -> TripRoute:
        """
        Optimize trip route for SKU deliveries
        
        Args:
            trip_skus: List of SKUs to be delivered in this trip
            manufacturing_location: Starting location information
            
        Returns:
            Optimized trip route
        """
        try:
            # Extract all delivery locations from SKUs
            delivery_stops = self._extract_delivery_stops(trip_skus)
            
            # Group SKUs by delivery location
            location_sku_map = self._group_skus_by_location(trip_skus)
            
            # Calculate optimal route through delivery locations
            optimized_route = await self._calculate_optimal_route(
                manufacturing_location, 
                delivery_stops,
                location_sku_map
            )
            
            # Calculate trip metrics
            trip_metrics = self._calculate_trip_metrics(optimized_route, trip_skus)
            
            return TripRoute(
                trip_id=f"TRIP-{datetime.now().strftime('%Y%m%d')}-{hash(str(trip_skus))%10000:04d}",
                manufacturing_location_id=manufacturing_location['id'],
                route_stops=optimized_route,
                sku_items=trip_skus,
                total_distance_km=trip_metrics['total_distance'],
                estimated_duration_hours=trip_metrics['estimated_duration'],
                total_weight_kg=trip_metrics['total_weight'],
                total_volume_m3=trip_metrics['total_volume'],
                capacity_utilization=trip_metrics['capacity_utilization']
            )
            
        except Exception as e:
            logger.error(f"Error optimizing trip route: {str(e)}")
            raise
    
    def _extract_delivery_stops(self, trip_skus: List[SKUDeliveryInfo]) -> List[DeliveryLocation]:
        """Extract unique delivery locations from SKUs"""
        delivery_stops = {}
        
        for sku in trip_skus:
            for location in sku.delivery_locations:
                if location.id not in delivery_stops:
                    delivery_stops[location.id] = location
        
        return list(delivery_stops.values())
    
    def _group_skus_by_location(self, trip_skus: List[SKUDeliveryInfo]) -> Dict[str, List[SKUDeliveryInfo]]:
        """Group SKUs by their delivery locations"""
        location_sku_map = {}
        
        for sku in trip_skus:
            for location in sku.delivery_locations:
                if location.id not in location_sku_map:
                    location_sku_map[location.id] = []
                location_sku_map[location.id].append(sku)
        
        return location_sku_map
    
    async def _calculate_optimal_route(self, origin: Dict[str, Any], 
                                     delivery_stops: List[DeliveryLocation],
                                     location_sku_map: Dict[str, List[SKUDeliveryInfo]]) -> List[DeliveryLocation]:
        """
        Calculate optimal route through delivery locations using enhanced TSP algorithm
        """
        if len(delivery_stops) <= 1:
            return delivery_stops
        
        # Create distance matrix
        distance_matrix = await self._create_distance_matrix(origin, delivery_stops)
        
        # Apply nearest neighbor algorithm with improvements
        route = self._nearest_neighbor_with_improvements(distance_matrix, delivery_stops, location_sku_map)
        
        # Apply 2-opt optimization
        optimized_route = self._two_opt_optimization(route, distance_matrix)
        
        return optimized_route
    
    async def _create_distance_matrix(self, origin: Dict[str, Any], 
                                    delivery_stops: List[DeliveryLocation]) -> List[List[float]]:
        """Create distance matrix between origin and all delivery stops"""
        locations = [origin] + [{'latitude': stop.latitude, 'longitude': stop.longitude} for stop in delivery_stops]
        matrix_size = len(locations)
        distance_matrix = [[0.0 for _ in range(matrix_size)] for _ in range(matrix_size)]
        
        for i in range(matrix_size):
            for j in range(matrix_size):
                if i != j:
                    distance = self._calculate_distance(
                        locations[i]['latitude'], locations[i]['longitude'],
                        locations[j]['latitude'], locations[j]['longitude']
                    )
                    distance_matrix[i][j] = distance
        
        return distance_matrix
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _nearest_neighbor_with_improvements(self, distance_matrix: List[List[float]], 
                                          delivery_stops: List[DeliveryLocation],
                                          location_sku_map: Dict[str, List[SKUDeliveryInfo]]) -> List[DeliveryLocation]:
        """Enhanced nearest neighbor algorithm considering SKU delivery efficiency"""
        if not delivery_stops:
            return []
        
        unvisited = set(range(len(delivery_stops)))
        route = []
        current_pos = 0  # Start from origin (index 0 in distance matrix)
        
        while unvisited:
            if not route:  # First stop
                # Choose first stop based on SKU delivery efficiency
                next_stop_idx = self._select_best_first_stop(delivery_stops, location_sku_map, distance_matrix)
            else:
                # Choose next stop based on distance and SKU compatibility
                next_stop_idx = self._select_next_stop(current_pos, unvisited, distance_matrix, 
                                                     delivery_stops, location_sku_map)
            
            route.append(delivery_stops[next_stop_idx])
            unvisited.remove(next_stop_idx)
            current_pos = next_stop_idx + 1  # +1 because origin is index 0
        
        return route
    
    def _select_best_first_stop(self, delivery_stops: List[DeliveryLocation],
                               location_sku_map: Dict[str, List[SKUDeliveryInfo]],
                               distance_matrix: List[List[float]]) -> int:
        """Select the best first delivery stop"""
        best_score = -1
        best_idx = 0
        
        for idx, stop in enumerate(delivery_stops):
            # Calculate score based on distance from origin and SKU value
            distance_score = 1 / (distance_matrix[0][idx + 1] + 1)  # +1 to avoid division by zero
            sku_score = len(location_sku_map.get(stop.id, []))
            
            total_score = distance_score * 0.6 + sku_score * 0.4
            
            if total_score > best_score:
                best_score = total_score
                best_idx = idx
        
        return best_idx
    
    def _select_next_stop(self, current_pos: int, unvisited: set, 
                         distance_matrix: List[List[float]],
                         delivery_stops: List[DeliveryLocation],
                         location_sku_map: Dict[str, List[SKUDeliveryInfo]]) -> int:
        """Select next delivery stop based on distance and SKU efficiency"""
        best_score = float('inf')
        best_idx = None
        
        for idx in unvisited:
            distance = distance_matrix[current_pos][idx + 1]  # +1 for origin offset
            sku_count = len(location_sku_map.get(delivery_stops[idx].id, []))
            
            # Lower distance is better, higher SKU count is better
            score = distance / (sku_count + 1)
            
            if score < best_score:
                best_score = score
                best_idx = idx
        
        return best_idx if best_idx is not None else list(unvisited)[0]
    
    def _two_opt_optimization(self, route: List[DeliveryLocation], 
                             distance_matrix: List[List[float]]) -> List[DeliveryLocation]:
        """Apply 2-opt optimization to improve route"""
        if len(route) < 4:
            return route
        
        improved = True
        current_route = route.copy()
        
        while improved:
            improved = False
            for i in range(len(current_route) - 1):
                for j in range(i + 2, len(current_route)):
                    if j == len(current_route) - 1 and i == 0:
                        continue  # Skip if it's the same edge
                    
                    # Calculate current distance
                    current_distance = self._calculate_route_segment_distance(
                        current_route, i, j, distance_matrix
                    )
                    
                    # Calculate distance after 2-opt swap
                    new_route = current_route.copy()
                    new_route[i+1:j+1] = reversed(new_route[i+1:j+1])
                    
                    new_distance = self._calculate_route_segment_distance(
                        new_route, i, j, distance_matrix
                    )
                    
                    if new_distance < current_distance:
                        current_route = new_route
                        improved = True
                        break
                
                if improved:
                    break
        
        return current_route
    
    def _calculate_route_segment_distance(self, route: List[DeliveryLocation], 
                                        start_idx: int, end_idx: int,
                                        distance_matrix: List[List[float]]) -> float:
        """Calculate distance for a route segment"""
        total_distance = 0.0
        
        # Add distance from start to start+1
        if start_idx < len(route) - 1:
            start_location_idx = self._get_location_index_in_matrix(route[start_idx])
            next_location_idx = self._get_location_index_in_matrix(route[start_idx + 1])
            total_distance += distance_matrix[start_location_idx][next_location_idx]
        
        # Add distance from end to end+1 (if exists)
        if end_idx < len(route) - 1:
            end_location_idx = self._get_location_index_in_matrix(route[end_idx])
            next_location_idx = self._get_location_index_in_matrix(route[end_idx + 1])
            total_distance += distance_matrix[end_location_idx][next_location_idx]
        
        return total_distance
    
    def _get_location_index_in_matrix(self, location: DeliveryLocation) -> int:
        """Get the index of a location in the distance matrix"""
        # This is a simplified implementation
        # In a real system, you'd maintain a mapping between locations and matrix indices
        return hash(location.id) % 1000  # Placeholder implementation
    
    def _calculate_trip_metrics(self, route: List[DeliveryLocation], 
                               trip_skus: List[SKUDeliveryInfo]) -> Dict[str, Any]:
        """Calculate trip metrics including distance, duration, and capacity"""
        total_distance = 0.0
        total_weight = Decimal('0')
        total_volume = Decimal('0')
        
        # Calculate total distance
        for i in range(len(route) - 1):
            distance = self._calculate_distance(
                route[i].latitude, route[i].longitude,
                route[i + 1].latitude, route[i + 1].longitude
            )
            total_distance += distance
        
        # Calculate total weight and volume
        for sku in trip_skus:
            total_weight += sku.weight_kg * sku.quantity
            total_volume += sku.volume_m3 * sku.quantity
        
        # Calculate estimated duration
        driving_time = total_distance / 60  # Assuming 60 km/h average speed
        delivery_time = len(route) * self.sku_delivery_time_per_stop
        estimated_duration = driving_time + delivery_time
        
        # Calculate capacity utilization
        weight_utilization = float(total_weight) / self.max_trip_weight
        volume_utilization = float(total_volume) / self.max_trip_volume
        capacity_utilization = max(weight_utilization, volume_utilization)
        
        return {
            'total_distance': total_distance,
            'estimated_duration': estimated_duration,
            'total_weight': total_weight,
            'total_volume': total_volume,
            'capacity_utilization': capacity_utilization
        }
    
    async def validate_trip_constraints(self, trip_route: TripRoute) -> Dict[str, Any]:
        """Validate trip against all constraints"""
        validation_results = {
            'is_valid': True,
            'violations': [],
            'warnings': []
        }
        
        # Check SKU count constraints
        sku_count = len(trip_route.sku_items)
        if sku_count < self.target_sku_min:
            validation_results['violations'].append(
                f"SKU count {sku_count} below minimum {self.target_sku_min}"
            )
            validation_results['is_valid'] = False
        elif sku_count > self.target_sku_max:
            validation_results['violations'].append(
                f"SKU count {sku_count} above maximum {self.target_sku_max}"
            )
            validation_results['is_valid'] = False
        
        # Check weight constraints
        if trip_route.total_weight_kg > self.max_trip_weight:
            validation_results['violations'].append(
                f"Weight {trip_route.total_weight_kg}kg exceeds maximum {self.max_trip_weight}kg"
            )
            validation_results['is_valid'] = False
        
        # Check volume constraints
        if trip_route.total_volume_m3 > self.max_trip_volume:
            validation_results['violations'].append(
                f"Volume {trip_route.total_volume_m3}m³ exceeds maximum {self.max_trip_volume}m³"
            )
            validation_results['is_valid'] = False
        
        # Check duration constraints
        if trip_route.estimated_duration_hours > self.max_trip_duration:
            validation_results['violations'].append(
                f"Duration {trip_route.estimated_duration_hours}h exceeds maximum {self.max_trip_duration}h"
            )
            validation_results['is_valid'] = False
        
        # Check delivery stops
        if len(trip_route.route_stops) > self.max_delivery_stops:
            validation_results['violations'].append(
                f"Delivery stops {len(trip_route.route_stops)} exceeds maximum {self.max_delivery_stops}"
            )
            validation_results['is_valid'] = False
        
        # Capacity utilization warnings
        if trip_route.capacity_utilization < 0.8:
            validation_results['warnings'].append(
                f"Low capacity utilization: {trip_route.capacity_utilization:.1%}"
            )
        elif trip_route.capacity_utilization > 0.95:
            validation_results['warnings'].append(
                f"High capacity utilization: {trip_route.capacity_utilization:.1%}"
            )
        
        return validation_results
