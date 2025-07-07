from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.services.trip_route_optimizer import SKUDeliveryInfo, DeliveryLocation

logger = logging.getLogger(__name__)

@dataclass
class ConsolidatedSKU:
    """Consolidated SKU information across multiple retailer orders"""
    sku_code: str
    product_name: str
    category: str
    brand: str
    total_quantity: int
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    temperature_requirement: Optional[str]
    fragile: bool
    retailer_orders: List[str]  # Order IDs
    delivery_locations: List[DeliveryLocation]
    consolidation_efficiency: float

@dataclass
class TripSKUGroup:
    """Group of SKUs optimized for a single trip"""
    group_id: str
    skus: List[ConsolidatedSKU]
    total_sku_count: int
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    geographic_center: Tuple[float, float]  # lat, lon
    delivery_efficiency: float

class SKUConsolidationEngine:
    """Engine for consolidating SKUs across retailer orders and optimizing for trips"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.target_sku_min = 90
        self.target_sku_max = 100
        self.max_trip_weight = 25000  # kg
        self.max_trip_volume = 100    # m3
        self.max_geographic_spread = 200  # km radius
    
    async def consolidate_manufacturer_orders(self, manufacturing_location_id: str, 
                                            time_window_hours: int = 24) -> List[ConsolidatedSKU]:
        """
        Consolidate all retailer orders for a manufacturer within a time window
        
        Args:
            manufacturing_location_id: ID of the manufacturing location
            time_window_hours: Time window for order consolidation
            
        Returns:
            List of consolidated SKUs ready for trip planning
        """
        try:
            # Get all active orders within time window
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            
            orders_result = await self.db.execute(
                select(Order).where(
                    Order.status.in_(['VALIDATED', 'TRIP_QUEUED']),
                    Order.created_at >= cutoff_time
                )
            )
            orders = orders_result.scalars().all()
            
            if not orders:
                return []
            
            # Get all SKU items for these orders
            order_ids = [str(order.id) for order in orders]
            skus_result = await self.db.execute(
                select(OrderSKUItem).where(
                    OrderSKUItem.order_id.in_(order_ids)
                )
            )
            sku_items = skus_result.scalars().all()
            
            # Group SKUs by SKU code
            sku_groups = self._group_skus_by_code(sku_items, orders)
            
            # Create consolidated SKUs
            consolidated_skus = []
            for sku_code, sku_data in sku_groups.items():
                consolidated_sku = await self._create_consolidated_sku(sku_code, sku_data)
                if consolidated_sku:
                    consolidated_skus.append(consolidated_sku)
            
            return consolidated_skus
            
        except Exception as e:
            logger.error(f"Error consolidating manufacturer orders: {str(e)}")
            raise
    
    async def consolidate_skus_by_manufacturer(self, order_ids: List[str], 
                                             manufacturing_location_id: str) -> List[ConsolidatedSKU]:
        """
        Consolidate SKUs across multiple orders for a specific manufacturer
        
        Args:
            order_ids: List of order IDs to consolidate
            manufacturing_location_id: Manufacturing location ID
            
        Returns:
            List of consolidated SKUs optimized for trip planning
        """
        try:
            # Get orders
            orders_result = await self.db.execute(
                select(Order).where(Order.id.in_(order_ids))
            )
            orders = orders_result.scalars().all()
            
            if not orders:
                return []
            
            # Get SKU items for these orders
            skus_result = await self.db.execute(
                select(OrderSKUItem).where(
                    OrderSKUItem.order_id.in_(order_ids)
                )
            )
            sku_items = skus_result.scalars().all()
            
            # Group SKUs by SKU code
            sku_groups = self._group_skus_by_code(sku_items, orders)
            
            # Create consolidated SKUs
            consolidated_skus = []
            for sku_code, sku_data in sku_groups.items():
                consolidated_sku = await self._create_consolidated_sku(sku_code, sku_data)
                if consolidated_sku:
                    consolidated_skus.append(consolidated_sku)
            
            # Sort by consolidation efficiency
            consolidated_skus.sort(key=lambda x: x.consolidation_efficiency, reverse=True)
            
            return consolidated_skus
            
        except Exception as e:
            logger.error(f"Error consolidating SKUs by manufacturer: {str(e)}")
            raise
    
    async def create_trip_groups(self, consolidated_skus: List[ConsolidatedSKU], 
                                manufacturing_location_id: str) -> List[TripSKUGroup]:
        """
        Create optimal trip groups from consolidated SKUs
        
        Args:
            consolidated_skus: List of consolidated SKUs
            manufacturing_location_id: Manufacturing location ID
            
        Returns:
            List of trip groups optimized for delivery efficiency
        """
        try:
            if not consolidated_skus:
                return []
            
            # Initialize trip groups
            trip_groups = []
            remaining_skus = consolidated_skus.copy()
            group_counter = 1
            
            while remaining_skus:
                # Create new trip group
                current_group = TripSKUGroup(
                    group_id=f"TRIP-GROUP-{group_counter:03d}",
                    skus=[],
                    total_sku_count=0,
                    total_weight_kg=Decimal('0'),
                    total_volume_m3=Decimal('0'),
                    geographic_center=(0.0, 0.0),
                    delivery_efficiency=0.0
                )
                
                # Add SKUs to current group using greedy algorithm
                skus_to_remove = []
                for sku in remaining_skus:
                    if self._can_add_sku_to_group(current_group, sku):
                        current_group.skus.append(sku)
                        current_group.total_sku_count += sku.total_quantity
                        current_group.total_weight_kg += sku.total_weight_kg
                        current_group.total_volume_m3 += sku.total_volume_m3
                        skus_to_remove.append(sku)
                        
                        # Check if group is full
                        if len(current_group.skus) >= self.target_sku_max:
                            break
                
                # Remove added SKUs from remaining
                for sku in skus_to_remove:
                    remaining_skus.remove(sku)
                
                # Calculate group metrics
                if current_group.skus:
                    current_group.geographic_center = self._calculate_geographic_center(current_group.skus)
                    current_group.delivery_efficiency = self._calculate_delivery_efficiency(current_group.skus)
                    trip_groups.append(current_group)
                
                group_counter += 1
                
                # Safety check to prevent infinite loop
                if group_counter > 100:
                    logger.warning("Maximum trip groups reached, stopping consolidation")
                    break
            
            return trip_groups
            
        except Exception as e:
            logger.error(f"Error creating trip groups: {str(e)}")
            raise
    
    def _can_add_sku_to_group(self, group: TripSKUGroup, sku: ConsolidatedSKU) -> bool:
        """Check if SKU can be added to trip group without violating constraints"""
        # Check weight constraint
        if group.total_weight_kg + sku.total_weight_kg > self.max_trip_weight:
            return False
        
        # Check volume constraint  
        if group.total_volume_m3 + sku.total_volume_m3 > self.max_trip_volume:
            return False
        
        # Check SKU count constraint
        if len(group.skus) + 1 > self.target_sku_max:
            return False
        
        # Check geographic spread constraint
        if group.skus:
            group_center = self._calculate_geographic_center(group.skus)
            sku_center = self._calculate_sku_geographic_center(sku)
            distance = self._calculate_distance(
                group_center[0], group_center[1],
                sku_center[0], sku_center[1]
            )
            if distance > self.max_geographic_spread:
                return False
        
        return True
    
    def _calculate_geographic_center(self, skus: List[ConsolidatedSKU]) -> Tuple[float, float]:
        """Calculate geographic center of a list of SKUs"""
        if not skus:
            return (0.0, 0.0)
        
        total_lat = 0.0
        total_lon = 0.0
        total_locations = 0
        
        for sku in skus:
            for location in sku.delivery_locations:
                total_lat += location.latitude
                total_lon += location.longitude
                total_locations += 1
        
        if total_locations == 0:
            return (0.0, 0.0)
        
        return (total_lat / total_locations, total_lon / total_locations)
    
    def _calculate_sku_geographic_center(self, sku: ConsolidatedSKU) -> Tuple[float, float]:
        """Calculate geographic center of a single SKU's delivery locations"""
        if not sku.delivery_locations:
            return (0.0, 0.0)
        
        total_lat = sum(loc.latitude for loc in sku.delivery_locations)
        total_lon = sum(loc.longitude for loc in sku.delivery_locations)
        
        return (total_lat / len(sku.delivery_locations), total_lon / len(sku.delivery_locations))
    
    def _calculate_delivery_efficiency(self, skus: List[ConsolidatedSKU]) -> float:
        """Calculate delivery efficiency score for a group of SKUs"""
        if not skus:
            return 0.0
        
        # Calculate based on consolidation ratio and geographic efficiency
        total_orders = sum(len(sku.retailer_orders) for sku in skus)
        total_locations = sum(len(sku.delivery_locations) for sku in skus)
        
        # Consolidation efficiency: higher is better
        consolidation_efficiency = total_orders / len(skus) if skus else 0
        
        # Geographic efficiency: lower spread is better
        geographic_spread = self._calculate_geographic_spread(skus)
        geographic_efficiency = 1.0 / (1.0 + geographic_spread / 100)  # Normalize to 0-1
        
        # Combined efficiency score
        return (consolidation_efficiency * 0.6) + (geographic_efficiency * 0.4)
    
    def _calculate_geographic_spread(self, skus: List[ConsolidatedSKU]) -> float:
        """Calculate geographic spread of SKUs in kilometers"""
        if not skus:
            return 0.0
        
        all_locations = []
        for sku in skus:
            all_locations.extend(sku.delivery_locations)
        
        if len(all_locations) < 2:
            return 0.0
        
        # Calculate maximum distance between any two locations
        max_distance = 0.0
        for i in range(len(all_locations)):
            for j in range(i + 1, len(all_locations)):
                distance = self._calculate_distance(
                    all_locations[i].latitude, all_locations[i].longitude,
                    all_locations[j].latitude, all_locations[j].longitude
                )
                max_distance = max(max_distance, distance)
        
        return max_distance
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    async def optimize_sku_groups_for_trips(self, consolidated_skus: List[ConsolidatedSKU]) -> List[TripSKUGroup]:
        """
        Optimize consolidated SKUs into trip groups of 90-100 SKUs each
        
        Args:
            consolidated_skus: List of consolidated SKUs
            
        Returns:
            List of optimized trip SKU groups
        """
        try:
            if not consolidated_skus:
                return []
            
            # Sort SKUs by consolidation efficiency (higher first)
            sorted_skus = sorted(consolidated_skus, 
                               key=lambda x: x.consolidation_efficiency, 
                               reverse=True)
            
            trip_groups = []
            current_group_skus = []
            current_weight = Decimal('0')
            current_volume = Decimal('0')
            
            for sku in sorted_skus:
                # Check if adding this SKU would exceed constraints
                new_weight = current_weight + sku.total_weight_kg
                new_volume = current_volume + sku.total_volume_m3
                new_sku_count = len(current_group_skus) + 1
                
                # Check if we can add this SKU to current group
                if (new_sku_count <= self.target_sku_max and
                    new_weight <= self.max_trip_weight and
                    new_volume <= self.max_trip_volume and
                    self._check_geographic_compatibility(current_group_skus + [sku])):
                    
                    current_group_skus.append(sku)
                    current_weight = new_weight
                    current_volume = new_volume
                else:
                    # Finalize current group if it meets minimum requirements
                    if len(current_group_skus) >= self.target_sku_min:
                        trip_group = self._create_trip_sku_group(current_group_skus)
                        if trip_group:
                            trip_groups.append(trip_group)
                    
                    # Start new group
                    current_group_skus = [sku]
                    current_weight = sku.total_weight_kg
                    current_volume = sku.total_volume_m3
            
            # Handle remaining SKUs
            if len(current_group_skus) >= self.target_sku_min:
                trip_group = self._create_trip_sku_group(current_group_skus)
                if trip_group:
                    trip_groups.append(trip_group)
            
            return trip_groups
            
        except Exception as e:
            logger.error(f"Error optimizing SKU groups for trips: {str(e)}")
            raise
    
    def _check_geographic_compatibility(self, skus: List[ConsolidatedSKU]) -> bool:
        """Check if SKUs are geographically compatible for a single trip"""
        try:
            all_locations = []
            for sku in skus:
                all_locations.extend(sku.delivery_locations)
            
            if not all_locations:
                return True
            
            # Calculate geographic spread
            spread = self._calculate_geographic_spread(all_locations)
            
            return spread <= self.max_geographic_spread
            
        except Exception:
            return False
    
    def _create_trip_sku_group(self, skus: List[ConsolidatedSKU]) -> Optional[TripSKUGroup]:
        """Create a trip SKU group from a list of SKUs"""
        try:
            if not skus:
                return None
            
            total_weight = sum(sku.total_weight_kg for sku in skus)
            total_volume = sum(sku.total_volume_m3 for sku in skus)
            
            # Calculate geographic center
            all_locations = []
            for sku in skus:
                all_locations.extend(sku.delivery_locations)
            
            if all_locations:
                center_lat = sum(loc.latitude for loc in all_locations) / len(all_locations)
                center_lon = sum(loc.longitude for loc in all_locations) / len(all_locations)
                geographic_center = (center_lat, center_lon)
            else:
                geographic_center = (0.0, 0.0)
            
            # Calculate delivery efficiency
            delivery_efficiency = sum(sku.consolidation_efficiency for sku in skus) / len(skus)
            
            group_id = f"TRIP_GROUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(skus))%10000:04d}"
            
            return TripSKUGroup(
                group_id=group_id,
                skus=skus,
                total_sku_count=len(skus),
                total_weight_kg=total_weight,
                total_volume_m3=total_volume,
                geographic_center=geographic_center,
                delivery_efficiency=delivery_efficiency
            )
            
        except Exception as e:
            logger.error(f"Error creating trip SKU group: {str(e)}")
            return None
    
    async def validate_sku_consolidation(self, trip_group: TripSKUGroup) -> Dict[str, Any]:
        """Validate SKU consolidation against business rules"""
        validation_result = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'metrics': {}
        }
        
        try:
            # Check SKU count constraints
            if trip_group.total_sku_count < self.target_sku_min:
                validation_result['violations'].append(
                    f"SKU count {trip_group.total_sku_count} below minimum {self.target_sku_min}"
                )
                validation_result['is_valid'] = False
            elif trip_group.total_sku_count > self.target_sku_max:
                validation_result['violations'].append(
                    f"SKU count {trip_group.total_sku_count} above maximum {self.target_sku_max}"
                )
                validation_result['is_valid'] = False
            
            # Check weight constraints
            if trip_group.total_weight_kg > self.max_trip_weight:
                validation_result['violations'].append(
                    f"Total weight {trip_group.total_weight_kg}kg exceeds maximum {self.max_trip_weight}kg"
                )
                validation_result['is_valid'] = False
            
            # Check volume constraints
            if trip_group.total_volume_m3 > self.max_trip_volume:
                validation_result['violations'].append(
                    f"Total volume {trip_group.total_volume_m3}m³ exceeds maximum {self.max_trip_volume}m³"
                )
                validation_result['is_valid'] = False
            
            # Check geographic spread
            all_locations = []
            for sku in trip_group.skus:
                all_locations.extend(sku.delivery_locations)
            
            if all_locations:
                geographic_spread = self._calculate_geographic_spread(all_locations)
                if geographic_spread > self.max_geographic_spread:
                    validation_result['warnings'].append(
                        f"Geographic spread {geographic_spread:.1f}km exceeds recommended {self.max_geographic_spread}km"
                    )
            
            # Add metrics
            validation_result['metrics'] = {
                'sku_count': trip_group.total_sku_count,
                'total_weight_kg': float(trip_group.total_weight_kg),
                'total_volume_m3': float(trip_group.total_volume_m3),
                'delivery_efficiency': trip_group.delivery_efficiency,
                'geographic_spread_km': geographic_spread if all_locations else 0.0
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating SKU consolidation: {str(e)}")
            validation_result['is_valid'] = False
            validation_result['violations'].append(f"Validation error: {str(e)}")
            return validation_result
