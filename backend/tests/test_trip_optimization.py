import pytest
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trip_route_optimizer import (
    TripRouteOptimizer, 
    SKUDeliveryInfo, 
    DeliveryLocation, 
    TripRoute
)
from app.services.sku_consolidation_engine import (
    SKUConsolidationEngine, 
    ConsolidatedSKU, 
    TripSKUGroup
)
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.trip_planning import ManufacturingLocation, Truck, DeliveryRoute


class TestTripRouteOptimizer:
    """Test suite for trip route optimization"""
    
    @pytest.fixture
    def optimizer(self):
        """Create trip route optimizer instance"""
        return TripRouteOptimizer()
    
    @pytest.fixture
    def sample_manufacturing_location(self):
        """Sample manufacturing location"""
        return {
            'id': 'mfg-001',
            'name': 'Main Manufacturing Plant',
            'address': '123 Industrial Ave',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
    
    @pytest.fixture
    def sample_delivery_locations(self):
        """Sample delivery locations"""
        return [
            DeliveryLocation(
                id='loc-001',
                name='Retailer Store A',
                address='456 Retail St',
                latitude=40.7589,
                longitude=-73.9851,
                retailer_id='retailer-001',
                delivery_window_start=datetime.now(),
                delivery_window_end=datetime.now() + timedelta(hours=8)
            ),
            DeliveryLocation(
                id='loc-002',
                name='Retailer Store B',
                address='789 Commerce Blvd',
                latitude=40.7282,
                longitude=-73.7949,
                retailer_id='retailer-002',
                delivery_window_start=datetime.now(),
                delivery_window_end=datetime.now() + timedelta(hours=10)
            ),
            DeliveryLocation(
                id='loc-003',
                name='Retailer Store C',
                address='321 Market Ave',
                latitude=40.6892,
                longitude=-74.0445,
                retailer_id='retailer-003',
                delivery_window_start=datetime.now(),
                delivery_window_end=datetime.now() + timedelta(hours=12)
            )
        ]
    
    @pytest.fixture
    def sample_sku_items(self, sample_delivery_locations):
        """Sample SKU items for testing"""
        return [
            SKUDeliveryInfo(
                sku_code='SKU-001',
                product_name='Premium Widget A',
                category='Electronics',
                brand='TechCorp',
                quantity=50,
                weight_kg=Decimal('25.5'),
                volume_m3=Decimal('2.1'),
                temperature_requirement='AMBIENT',
                fragile=False,
                delivery_locations=[sample_delivery_locations[0]],
                order_id='order-001'
            ),
            SKUDeliveryInfo(
                sku_code='SKU-002',
                product_name='Premium Widget B',
                category='Electronics',
                brand='TechCorp',
                quantity=75,
                weight_kg=Decimal('35.2'),
                volume_m3=Decimal('3.5'),
                temperature_requirement='COLD',
                fragile=True,
                delivery_locations=[sample_delivery_locations[1]],
                order_id='order-002'
            ),
            SKUDeliveryInfo(
                sku_code='SKU-003',
                product_name='Premium Widget C',
                category='Home & Garden',
                brand='HomeCorp',
                quantity=100,
                weight_kg=Decimal('45.8'),
                volume_m3=Decimal('4.2'),
                temperature_requirement='AMBIENT',
                fragile=False,
                delivery_locations=[sample_delivery_locations[2]],
                order_id='order-003'
            )
        ]
    
    @pytest.mark.asyncio
    async def test_optimize_trip_route(self, optimizer, sample_sku_items, sample_manufacturing_location):
        """Test trip route optimization"""
        # Test optimization
        result = await optimizer.optimize_trip_route(
            sample_sku_items, 
            sample_manufacturing_location
        )
        
        # Assertions
        assert isinstance(result, TripRoute)
        assert result.trip_id.startswith('TRIP-')
        assert result.manufacturing_location_id == sample_manufacturing_location['id']
        assert len(result.route_stops) == 3
        assert len(result.sku_items) == 3
        assert result.total_distance_km > 0
        assert result.estimated_duration_hours > 0
        assert result.total_weight_kg > 0
        assert result.total_volume_m3 > 0
        assert 0 <= result.capacity_utilization <= 1.5
    
    @pytest.mark.asyncio
    async def test_validate_trip_constraints(self, optimizer, sample_sku_items, sample_manufacturing_location):
        """Test trip constraint validation"""
        # Create optimized trip
        trip = await optimizer.optimize_trip_route(
            sample_sku_items, 
            sample_manufacturing_location
        )
        
        # Validate constraints
        validation_result = await optimizer.validate_trip_constraints(trip)
        
        # Assertions
        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'violations' in validation_result
        assert 'warnings' in validation_result
        assert isinstance(validation_result['violations'], list)
        assert isinstance(validation_result['warnings'], list)
    
    def test_calculate_distance(self, optimizer):
        """Test distance calculation"""
        # Test known distance (NYC to Philadelphia ~95 miles / 153 km)
        distance = optimizer._calculate_distance(40.7128, -74.0060, 39.9526, -75.1652)
        
        # Should be approximately 130-160 km
        assert 130 <= distance <= 160
    
    def test_extract_delivery_stops(self, optimizer, sample_sku_items):
        """Test delivery stop extraction"""
        stops = optimizer._extract_delivery_stops(sample_sku_items)
        
        assert len(stops) == 3
        assert all(isinstance(stop, DeliveryLocation) for stop in stops)
        assert len(set(stop.id for stop in stops)) == 3  # All unique
    
    def test_group_skus_by_location(self, optimizer, sample_sku_items):
        """Test SKU grouping by location"""
        location_map = optimizer._group_skus_by_location(sample_sku_items)
        
        assert len(location_map) == 3
        assert all(len(skus) == 1 for skus in location_map.values())


class TestSKUConsolidationEngine:
    """Test suite for SKU consolidation engine"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def consolidation_engine(self, mock_db_session):
        """Create consolidation engine instance"""
        return SKUConsolidationEngine(mock_db_session)
    
    @pytest.fixture
    def sample_consolidated_skus(self):
        """Sample consolidated SKUs"""
        return [
            ConsolidatedSKU(
                sku_code='SKU-001',
                product_name='Premium Widget A',
                category='Electronics',
                brand='TechCorp',
                total_quantity=150,
                total_weight_kg=Decimal('75.5'),
                total_volume_m3=Decimal('6.3'),
                temperature_requirement='AMBIENT',
                fragile=False,
                retailer_orders=['order-001', 'order-002'],
                delivery_locations=[
                    DeliveryLocation(
                        id='loc-001',
                        name='Store A',
                        address='123 Main St',
                        latitude=40.7128,
                        longitude=-74.0060,
                        retailer_id='retailer-001',
                        delivery_window_start=datetime.now(),
                        delivery_window_end=datetime.now() + timedelta(hours=8)
                    )
                ],
                consolidation_efficiency=0.85
            ),
            ConsolidatedSKU(
                sku_code='SKU-002',
                product_name='Premium Widget B',
                category='Electronics',
                brand='TechCorp',
                total_quantity=200,
                total_weight_kg=Decimal('95.2'),
                total_volume_m3=Decimal('8.1'),
                temperature_requirement='COLD',
                fragile=True,
                retailer_orders=['order-003', 'order-004'],
                delivery_locations=[
                    DeliveryLocation(
                        id='loc-002',
                        name='Store B',
                        address='456 Oak Ave',
                        latitude=40.7589,
                        longitude=-73.9851,
                        retailer_id='retailer-002',
                        delivery_window_start=datetime.now(),
                        delivery_window_end=datetime.now() + timedelta(hours=10)
                    )
                ],
                consolidation_efficiency=0.92
            )
        ]
    
    @pytest.mark.asyncio
    async def test_create_trip_groups(self, consolidation_engine, sample_consolidated_skus):
        """Test trip group creation"""
        # Test group creation
        trip_groups = await consolidation_engine.create_trip_groups(
            sample_consolidated_skus,
            'mfg-001'
        )
        
        # Assertions
        assert len(trip_groups) >= 1
        assert all(isinstance(group, TripSKUGroup) for group in trip_groups)
        assert all(group.group_id.startswith('TRIP-GROUP-') for group in trip_groups)
        assert all(len(group.skus) > 0 for group in trip_groups)
        assert all(group.total_sku_count > 0 for group in trip_groups)
        assert all(group.total_weight_kg > 0 for group in trip_groups)
        assert all(group.delivery_efficiency > 0 for group in trip_groups)
    
    def test_can_add_sku_to_group(self, consolidation_engine, sample_consolidated_skus):
        """Test SKU addition constraint validation"""
        # Create empty group
        group = TripSKUGroup(
            group_id='TEST-GROUP-001',
            skus=[],
            total_sku_count=0,
            total_weight_kg=Decimal('0'),
            total_volume_m3=Decimal('0'),
            geographic_center=(0.0, 0.0),
            delivery_efficiency=0.0
        )
        
        # Test adding first SKU
        can_add = consolidation_engine._can_add_sku_to_group(group, sample_consolidated_skus[0])
        assert can_add is True
        
        # Add SKU to group
        group.skus.append(sample_consolidated_skus[0])
        group.total_weight_kg += sample_consolidated_skus[0].total_weight_kg
        group.total_volume_m3 += sample_consolidated_skus[0].total_volume_m3
        
        # Test adding second SKU
        can_add = consolidation_engine._can_add_sku_to_group(group, sample_consolidated_skus[1])
        assert can_add is True
    
    def test_calculate_geographic_center(self, consolidation_engine, sample_consolidated_skus):
        """Test geographic center calculation"""
        center = consolidation_engine._calculate_geographic_center(sample_consolidated_skus)
        
        assert isinstance(center, tuple)
        assert len(center) == 2
        assert isinstance(center[0], float)
        assert isinstance(center[1], float)
        assert center != (0.0, 0.0)  # Should have valid coordinates
    
    def test_calculate_delivery_efficiency(self, consolidation_engine, sample_consolidated_skus):
        """Test delivery efficiency calculation"""
        efficiency = consolidation_engine._calculate_delivery_efficiency(sample_consolidated_skus)
        
        assert isinstance(efficiency, float)
        assert 0 <= efficiency <= 10  # Should be a reasonable efficiency score
    
    def test_calculate_distance(self, consolidation_engine):
        """Test distance calculation"""
        # Test known distance
        distance = consolidation_engine._calculate_distance(40.7128, -74.0060, 39.9526, -75.1652)
        
        # Should be approximately 130-160 km
        assert 130 <= distance <= 160


class TestTripOptimizationIntegration:
    """Integration tests for trip optimization system"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_orders(self):
        """Sample orders for testing"""
        return [
            Order(
                id='order-001',
                order_number='ORD-001',
                status='CONFIRMED',
                delivery_date=date.today(),
                delivery_address='123 Main St',
                delivery_latitude=40.7128,
                delivery_longitude=-74.0060,
                retailer_id='retailer-001'
            ),
            Order(
                id='order-002',
                order_number='ORD-002',
                status='PROCESSING',
                delivery_date=date.today(),
                delivery_address='456 Oak Ave',
                delivery_latitude=40.7589,
                delivery_longitude=-73.9851,
                retailer_id='retailer-002'
            )
        ]
    
    @pytest.fixture
    def sample_sku_items(self):
        """Sample SKU items for orders"""
        return [
            OrderSKUItem(
                id='sku-001',
                order_id='order-001',
                sku_code='SKU-001',
                product_name='Premium Widget A',
                category='Electronics',
                brand='TechCorp',
                quantity=50,
                weight_kg=Decimal('25.5'),
                volume_m3=Decimal('2.1'),
                temperature_requirement='AMBIENT',
                fragile=False
            ),
            OrderSKUItem(
                id='sku-002',
                order_id='order-002',
                sku_code='SKU-002',
                product_name='Premium Widget B',
                category='Electronics',
                brand='TechCorp',
                quantity=75,
                weight_kg=Decimal('35.2'),
                volume_m3=Decimal('3.5'),
                temperature_requirement='COLD',
                fragile=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_end_to_end_trip_optimization(self, mock_db_session, sample_orders, sample_sku_items):
        """Test complete trip optimization workflow"""
        # Setup mocks
        orders_result = Mock()
        orders_result.scalars.return_value.all.return_value = sample_orders
        
        sku_items_result = Mock()
        sku_items_result.scalars.return_value.all.return_value = sample_sku_items
        
        mock_db_session.execute.side_effect = [orders_result, sku_items_result]
        
        # Initialize engines
        consolidation_engine = SKUConsolidationEngine(mock_db_session)
        route_optimizer = TripRouteOptimizer()
        
        # Test consolidation
        consolidated_skus = await consolidation_engine.consolidate_skus_by_manufacturer(
            ['order-001', 'order-002'],
            'mfg-001'
        )
        
        # Verify consolidation results
        assert len(consolidated_skus) >= 1
        
        # Test trip group creation
        trip_groups = await consolidation_engine.create_trip_groups(
            consolidated_skus,
            'mfg-001'
        )
        
        # Verify trip groups
        assert len(trip_groups) >= 1
        assert all(isinstance(group, TripSKUGroup) for group in trip_groups)
        
        # Test route optimization for first trip group
        if trip_groups:
            first_group = trip_groups[0]
            
            # Convert to SKU delivery info
            trip_skus = []
            for consolidated_sku in first_group.skus:
                for location in consolidated_sku.delivery_locations:
                    trip_sku = SKUDeliveryInfo(
                        sku_code=consolidated_sku.sku_code,
                        product_name=consolidated_sku.product_name,
                        category=consolidated_sku.category,
                        brand=consolidated_sku.brand,
                        quantity=consolidated_sku.total_quantity,
                        weight_kg=consolidated_sku.total_weight_kg,
                        volume_m3=consolidated_sku.total_volume_m3,
                        temperature_requirement=consolidated_sku.temperature_requirement,
                        fragile=consolidated_sku.fragile,
                        delivery_locations=[location],
                        order_id=consolidated_sku.retailer_orders[0]
                    )
                    trip_skus.append(trip_sku)
            
            # Test route optimization
            manufacturing_location = {
                'id': 'mfg-001',
                'name': 'Main Plant',
                'latitude': 40.7128,
                'longitude': -74.0060
            }
            
            if trip_skus:
                optimized_route = await route_optimizer.optimize_trip_route(
                    trip_skus,
                    manufacturing_location
                )
                
                # Verify optimization results
                assert isinstance(optimized_route, TripRoute)
                assert optimized_route.total_distance_km > 0
                assert optimized_route.estimated_duration_hours > 0
                assert optimized_route.capacity_utilization > 0


# Performance and Load Tests
class TestTripOptimizationPerformance:
    """Performance tests for trip optimization"""
    
    @pytest.mark.asyncio
    async def test_large_scale_optimization(self):
        """Test optimization with large datasets"""
        # Generate large dataset
        large_sku_dataset = []
        for i in range(500):  # 500 SKUs
            sku = SKUDeliveryInfo(
                sku_code=f'SKU-{i:03d}',
                product_name=f'Product {i}',
                category='Electronics',
                brand='TestBrand',
                quantity=50,
                weight_kg=Decimal('25.0'),
                volume_m3=Decimal('2.0'),
                temperature_requirement='AMBIENT',
                fragile=False,
                delivery_locations=[
                    DeliveryLocation(
                        id=f'loc-{i:03d}',
                        name=f'Location {i}',
                        address=f'{i} Test St',
                        latitude=40.7128 + (i * 0.001),
                        longitude=-74.0060 + (i * 0.001),
                        retailer_id=f'retailer-{i // 10}',
                        delivery_window_start=datetime.now(),
                        delivery_window_end=datetime.now() + timedelta(hours=8)
                    )
                ],
                order_id=f'order-{i:03d}'
            )
            large_sku_dataset.append(sku)
        
        # Test optimization performance
        optimizer = TripRouteOptimizer()
        manufacturing_location = {
            'id': 'mfg-001',
            'name': 'Main Plant',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
        
        start_time = datetime.now()
        
        # Process in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(large_sku_dataset), batch_size):
            batch = large_sku_dataset[i:i + batch_size]
            result = await optimizer.optimize_trip_route(batch, manufacturing_location)
            
            # Verify results
            assert isinstance(result, TripRoute)
            assert result.total_distance_km > 0
            assert result.estimated_duration_hours > 0
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Performance assertion - should complete within reasonable time
        assert execution_time < 60  # Should complete within 60 seconds


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
