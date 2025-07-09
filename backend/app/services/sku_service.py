from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.sku_item import OrderSKUItem
from app.models.schemas import SKUItemCreate, SKUItemResponse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class SKUService:
    """Service for managing SKU items and order calculations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_sku_items(self, order_id: str, sku_items: List[SKUItemCreate]) -> List[OrderSKUItem]:
        """Create multiple SKU items for an order"""
        created_items = []
        
        for sku_data in sku_items:
            sku_item = OrderSKUItem(
                order_id=order_id,
                sku_code=sku_data.sku_code,
                product_name=sku_data.product_name,
                category=sku_data.category,
                brand=sku_data.brand,
                quantity_ordered=sku_data.quantity_ordered,
                unit_of_measure=sku_data.unit_of_measure,
                unit_price=sku_data.unit_price,
                total_price=sku_data.total_price,
                weight_kg=sku_data.weight_kg,
                volume_m3=sku_data.volume_m3,
                temperature_requirement=sku_data.temperature_requirement,
                fragile=sku_data.fragile,
                product_attributes=sku_data.product_attributes or {},
                processing_remarks=sku_data.processing_remarks
            )
            
            self.db.add(sku_item)
            created_items.append(sku_item)
        
        await self.db.commit()
        
        for item in created_items:
            await self.db.refresh(item)
        
        return created_items
    
    async def get_sku_items_by_order(self, order_id: str) -> List[OrderSKUItem]:
        """Get all SKU items for an order"""
        result = await self.db.execute(
            select(OrderSKUItem).where(OrderSKUItem.order_id == order_id)
        )
        return result.scalars().all()
    
    async def calculate_order_summary(self, order_id: str) -> Dict[str, Any]:
        """Calculate order summary from SKU items"""
        result = await self.db.execute(
            select(
                func.count(OrderSKUItem.id).label('total_sku_count'),
                func.sum(OrderSKUItem.quantity_ordered).label('total_quantity'),
                func.sum(OrderSKUItem.weight_kg * OrderSKUItem.quantity_ordered).label('total_weight_kg'),
                func.sum(OrderSKUItem.volume_m3 * OrderSKUItem.quantity_ordered).label('total_volume_m3'),
                func.sum(OrderSKUItem.total_price).label('subtotal')
            ).where(OrderSKUItem.order_id == order_id)
        )
        
        summary = result.first()
        
        if not summary:
            return {
                'total_sku_count': 0,
                'total_quantity': 0,
                'total_weight_kg': Decimal('0.00'),
                'total_volume_m3': Decimal('0.00'),
                'subtotal': Decimal('0.00'),
                'tax': Decimal('0.00'),
                'total': Decimal('0.00')
            }
        
        subtotal = summary.subtotal or Decimal('0.00')
        tax = subtotal * Decimal('0.08')  # 8% tax rate - should be configurable
        total = subtotal + tax
        
        return {
            'total_sku_count': summary.total_sku_count or 0,
            'total_quantity': summary.total_quantity or 0,
            'total_weight_kg': summary.total_weight_kg or Decimal('0.00'),
            'total_volume_m3': summary.total_volume_m3 or Decimal('0.00'),
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
    
    async def validate_sku_items(self, sku_items: List[SKUItemCreate]) -> Dict[str, Any]:
        """Validate SKU items data"""
        validation_errors = []
        missing_fields = []
        
        for i, sku_item in enumerate(sku_items):
            item_errors = []
            
            # Validate required fields
            if not sku_item.sku_code:
                item_errors.append("SKU code is required")
            
            if not sku_item.product_name:
                item_errors.append("Product name is required")
            
            if sku_item.quantity_ordered <= 0:
                item_errors.append("Quantity must be positive")
            
            # Validate price consistency
            if sku_item.unit_price and sku_item.total_price:
                expected_total = sku_item.unit_price * sku_item.quantity_ordered
                if abs(expected_total - sku_item.total_price) > Decimal('0.01'):
                    item_errors.append("Total price doesn't match unit price × quantity")
            
            # Check for missing optional but important fields
            if not sku_item.category:
                missing_fields.append(f"Category for SKU {sku_item.sku_code}")
            
            if not sku_item.weight_kg:
                missing_fields.append(f"Weight for SKU {sku_item.sku_code}")
            
            if not sku_item.volume_m3:
                missing_fields.append(f"Volume for SKU {sku_item.sku_code}")
            
            if item_errors:
                validation_errors.append(f"SKU item {i+1}: {', '.join(item_errors)}")
        
        return {
            'is_valid': len(validation_errors) == 0,
            'validation_errors': validation_errors,
            'missing_fields': missing_fields
        }
    
    async def update_sku_item(self, sku_item_id: str, update_data: Dict[str, Any]) -> Optional[OrderSKUItem]:
        """Update a specific SKU item"""
        result = await self.db.execute(
            select(OrderSKUItem).where(OrderSKUItem.id == sku_item_id)
        )
        sku_item = result.scalar_one_or_none()
        
        if not sku_item:
            return None
        
        for field, value in update_data.items():
            if hasattr(sku_item, field):
                setattr(sku_item, field, value)
        
        await self.db.commit()
        await self.db.refresh(sku_item)
        return sku_item
    
    async def delete_sku_item(self, sku_item_id: str) -> bool:
        """Delete a specific SKU item"""
        result = await self.db.execute(
            select(OrderSKUItem).where(OrderSKUItem.id == sku_item_id)
        )
        sku_item = result.scalar_one_or_none()
        
        if not sku_item:
            return False
        
        await self.db.delete(sku_item)
        await self.db.commit()
        return True
    
    def convert_to_response(self, sku_item: OrderSKUItem) -> SKUItemResponse:
        """Convert SKU item model to response schema"""
        return SKUItemResponse(
            id=str(sku_item.id),
            sku_code=sku_item.sku_code,
            product_name=sku_item.product_name,
            category=sku_item.category,
            brand=sku_item.brand,
            quantity_ordered=sku_item.quantity_ordered,
            unit_of_measure=sku_item.unit_of_measure,
            unit_price=sku_item.unit_price,
            total_price=sku_item.total_price,
            weight_kg=sku_item.weight_kg,
            volume_m3=sku_item.volume_m3,
            temperature_requirement=sku_item.temperature_requirement,
            fragile=sku_item.fragile,
            product_attributes=sku_item.product_attributes,
            processing_remarks=sku_item.processing_remarks,
            created_at=sku_item.created_at,
            updated_at=sku_item.updated_at
        )
