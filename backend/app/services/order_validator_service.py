from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking
from decimal import Decimal
import logging
import uuid
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class OrderValidatorService:
    """Service for validating order completeness and identifying missing fields"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fmcg_product_catalog = {}  # Will be loaded from database or external source
    
    async def validate_order_completeness(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order completeness and identify missing fields"""
        try:
            # Log validation start with detailed context
            await self._log_tracking(order_id, "ORDER_VALIDATION_STARTED", 
                                   f"Starting comprehensive order validation for order {order_id}")
            
            # Log input data structure for debugging
            await self._log_tracking(order_id, "VALIDATION_INPUT_DATA", 
                                   f"Input data keys: {list(parsed_data.keys()) if parsed_data else 'None'}")
            
            validation_result = {
                "order_id": order_id,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "is_valid": True,
                "missing_fields": [],
                "validation_errors": [],
                "data_quality_issues": [],
                "business_rule_violations": [],
                "validation_steps": [],  # Track each validation step
                "detailed_context": {}  # Store detailed context for debugging
            }
            
            # Log each validation step
            step_counter = 1
            
            # 1. Required fields validation
            await self._log_tracking(order_id, "VALIDATION_STEP_1", 
                                   f"Step {step_counter}: Starting required fields validation")
            required_fields_result = await self._validate_required_fields(order_id, parsed_data)
            validation_result.update(required_fields_result)
            validation_result["validation_steps"].append({
                "step": step_counter,
                "name": "Required Fields Validation",
                "status": "completed",
                "result": f"Found {len(required_fields_result.get('missing_fields', []))} missing fields"
            })
            step_counter += 1
            
            # 2. Data type validation
            await self._log_tracking(order_id, "VALIDATION_STEP_2", 
                                   f"Step {step_counter}: Starting data type validation")
            data_type_result = await self._validate_data_types(order_id, parsed_data)
            validation_result["data_type_errors"] = data_type_result["errors"]
            validation_result["validation_errors"].extend(data_type_result["errors"])
            validation_result["validation_steps"].append({
                "step": step_counter,
                "name": "Data Type Validation",
                "status": "completed",
                "result": f"Found {len(data_type_result['errors'])} data type errors"
            })
            step_counter += 1
            
            # 3. Business rule validation
            await self._log_tracking(order_id, "VALIDATION_STEP_3", 
                                   f"Step {step_counter}: Starting business rules validation")
            business_rule_result = await self._validate_business_rules(order_id, parsed_data)
            validation_result["business_rule_violations"] = business_rule_result["violations"]
            validation_result["validation_errors"].extend(business_rule_result["violations"])
            validation_result["validation_steps"].append({
                "step": step_counter,
                "name": "Business Rules Validation",
                "status": "completed",
                "result": f"Found {len(business_rule_result['violations'])} rule violations"
            })
            step_counter += 1
            
            # 4. FMCG product catalog validation
            await self._log_tracking(order_id, "VALIDATION_STEP_4", 
                                   f"Step {step_counter}: Starting catalog validation")
            catalog_result = await self._validate_against_catalog(order_id, parsed_data)
            validation_result["catalog_validation"] = catalog_result
            validation_result["validation_errors"].extend(catalog_result.get("errors", []))
            validation_result["validation_steps"].append({
                "step": step_counter,
                "name": "Catalog Validation",
                "status": "completed",
                "result": f"Found {len(catalog_result.get('errors', []))} catalog errors"
            })
            step_counter += 1
            
            # 5. Data quality checks
            await self._log_tracking(order_id, "VALIDATION_STEP_5", 
                                   f"Step {step_counter}: Starting data quality checks")
            quality_result = await self._perform_data_quality_checks(order_id, parsed_data)
            validation_result["data_quality_issues"] = quality_result["issues"]
            validation_result["validation_steps"].append({
                "step": step_counter,
                "name": "Data Quality Checks",
                "status": "completed",
                "result": f"Found {len(quality_result['issues'])} quality issues"
            })
            
            # Add detailed context for troubleshooting
            validation_result["detailed_context"] = {
                "input_data_structure": self._analyze_data_structure(parsed_data),
                "field_mapping": self._create_field_mapping(parsed_data),
                "validation_timestamps": {
                    "started": datetime.utcnow().isoformat(),
                    "completed": datetime.utcnow().isoformat()
                }
            }
            
            # Determine overall validation status
            validation_result["is_valid"] = (
                len(validation_result["missing_fields"]) == 0 and
                len(validation_result["validation_errors"]) == 0 and
                len(validation_result["business_rule_violations"]) == 0
            )
            
            # Calculate validation score
            validation_result["validation_score"] = await self._calculate_validation_score(validation_result)
            
            # Log comprehensive completion details
            status = "ORDER_VALIDATION_COMPLETED" if validation_result["is_valid"] else "ORDER_VALIDATION_FAILED"
            completion_message = (
                f"Order validation completed. "
                f"Valid: {validation_result['is_valid']}, "
                f"Missing fields: {len(validation_result['missing_fields'])}, "
                f"Validation errors: {len(validation_result['validation_errors'])}, "
                f"Business rule violations: {len(validation_result['business_rule_violations'])}, "
                f"Data quality issues: {len(validation_result['data_quality_issues'])}, "
                f"Validation score: {validation_result['validation_score']:.2f}"
            )
            
            await self._log_tracking(order_id, status, completion_message)
            
            # Log detailed missing fields for troubleshooting
            if validation_result["missing_fields"]:
                missing_fields_details = "; ".join(validation_result["missing_fields"])
                await self._log_tracking(order_id, "MISSING_FIELDS_DETAILS", 
                                       f"Missing fields: {missing_fields_details}")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Order validation error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "ORDER_VALIDATION_ERROR", error_msg)
            raise
    
    async def _validate_required_fields(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields are present"""
        required_fields = {
            "order_level": [
                "order_number",
                "retailer_info",
                "delivery_date",
                "priority"
            ],
            "item_level": [
                "sku_code",
                "quantity",
                "price"
            ],
            "retailer_level": [
                "retailer_name",
                "delivery_address",
                "contact_info"
            ]
        }
        
        missing_fields = []
        validation_details = {}
        
        # Check order level fields
        order_items = parsed_data.get("order_items", [])
        retailer_info = parsed_data.get("retailer_info", {})
        
        for field in required_fields["order_level"]:
            if field not in parsed_data or not parsed_data[field]:
                missing_fields.append(f"order.{field}")
        
        # Check item level fields
        for i, item in enumerate(order_items):
            for field in required_fields["item_level"]:
                if field not in item or not item[field]:
                    missing_fields.append(f"item[{i}].{field}")
        
        # Check retailer level fields
        for field in required_fields["retailer_level"]:
            if field not in retailer_info or not retailer_info[field]:
                missing_fields.append(f"retailer.{field}")
        
        validation_details["missing_fields"] = missing_fields
        validation_details["required_fields_check"] = {
            "total_required": sum(len(fields) for fields in required_fields.values()),
            "missing_count": len(missing_fields),
            "completion_rate": 1 - (len(missing_fields) / sum(len(fields) for fields in required_fields.values()))
        }
        
        await self._log_tracking(order_id, "REQUIRED_FIELDS_VALIDATION", 
                               f"Required fields validation: {len(missing_fields)} missing fields")
        
        return validation_details
    
    async def _validate_data_types(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data types for quantities, dates, SKUs"""
        errors = []
        
        order_items = parsed_data.get("order_items", [])
        
        for i, item in enumerate(order_items):
            # Validate quantity
            if "quantity" in item:
                if not self._is_valid_quantity(item["quantity"]):
                    errors.append(f"item[{i}].quantity: Invalid quantity format '{item['quantity']}'")
            
            # Validate price
            if "price" in item:
                if not self._is_valid_price(item["price"]):
                    errors.append(f"item[{i}].price: Invalid price format '{item['price']}'")
            
            # Validate SKU format
            if "sku_code" in item:
                if not self._is_valid_sku_code(item["sku_code"]):
                    errors.append(f"item[{i}].sku_code: Invalid SKU format '{item['sku_code']}'")
        
        # Validate dates
        if "delivery_date" in parsed_data:
            if not self._is_valid_date(parsed_data["delivery_date"]):
                errors.append(f"order.delivery_date: Invalid date format '{parsed_data['delivery_date']}'")
        
        await self._log_tracking(order_id, "DATA_TYPE_VALIDATION", 
                               f"Data type validation: {len(errors)} errors found")
        
        return {"errors": errors}
    
    async def _validate_business_rules(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business rules like minimum order quantities and valid product codes"""
        violations = []
        
        order_items = parsed_data.get("order_items", [])
        
        for i, item in enumerate(order_items):
            # Minimum order quantity rule
            if "quantity" in item:
                try:
                    quantity = float(item["quantity"])
                    if quantity < 1:
                        violations.append(f"item[{i}].quantity: Below minimum order quantity (1)")
                    elif quantity > 10000:
                        violations.append(f"item[{i}].quantity: Exceeds maximum order quantity (10000)")
                except (ValueError, TypeError):
                    pass
            
            # Price validation rules
            if "price" in item:
                try:
                    price = float(item["price"])
                    if price < 0:
                        violations.append(f"item[{i}].price: Negative price not allowed")
                    elif price > 100000:
                        violations.append(f"item[{i}].price: Price exceeds maximum limit (100000)")
                except (ValueError, TypeError):
                    pass
            
            # SKU code format rules
            if "sku_code" in item:
                sku_code = item["sku_code"]
                if len(sku_code) < 3:
                    violations.append(f"item[{i}].sku_code: SKU code too short (minimum 3 characters)")
                elif len(sku_code) > 50:
                    violations.append(f"item[{i}].sku_code: SKU code too long (maximum 50 characters)")
        
        # Order level business rules
        total_value = sum(
            float(item.get("price", 0)) * float(item.get("quantity", 0))
            for item in order_items
            if self._is_valid_price(item.get("price")) and self._is_valid_quantity(item.get("quantity"))
        )
        
        if total_value < 100:
            violations.append("order.total_value: Order value below minimum (100)")
        elif total_value > 1000000:
            violations.append("order.total_value: Order value exceeds maximum (1000000)")
        
        await self._log_tracking(order_id, "BUSINESS_RULE_VALIDATION", 
                               f"Business rule validation: {len(violations)} violations found")
        
        return {"violations": violations}
    
    async def _validate_against_catalog(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-reference with FMCG product catalog"""
        catalog_result = {
            "valid_products": [],
            "invalid_products": [],
            "errors": []
        }
        
        order_items = parsed_data.get("order_items", [])
        
        for i, item in enumerate(order_items):
            sku_code = item.get("sku_code")
            if sku_code:
                # Check against catalog (mock implementation)
                if await self._is_valid_product_code(sku_code):
                    catalog_result["valid_products"].append({
                        "index": i,
                        "sku_code": sku_code,
                        "status": "valid"
                    })
                else:
                    catalog_result["invalid_products"].append({
                        "index": i,
                        "sku_code": sku_code,
                        "status": "invalid"
                    })
                    catalog_result["errors"].append(f"item[{i}].sku_code: Product code '{sku_code}' not found in catalog")
        
        await self._log_tracking(order_id, "CATALOG_VALIDATION", 
                               f"Catalog validation: {len(catalog_result['valid_products'])} valid, "
                               f"{len(catalog_result['invalid_products'])} invalid products")
        
        return catalog_result
    
    async def _perform_data_quality_checks(self, order_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data quality checks"""
        issues = []
        
        order_items = parsed_data.get("order_items", [])
        
        # Check for duplicates
        sku_codes = [item.get("sku_code") for item in order_items if item.get("sku_code")]
        duplicate_skus = [sku for sku in set(sku_codes) if sku_codes.count(sku) > 1]
        
        if duplicate_skus:
            issues.append(f"data_quality.duplicates: Duplicate SKU codes found: {duplicate_skus}")
        
        # Check for missing critical data
        empty_items = [i for i, item in enumerate(order_items) if not item.get("sku_code") or not item.get("quantity")]
        if empty_items:
            issues.append(f"data_quality.empty_items: Items with missing critical data at indices: {empty_items}")
        
        # Check for inconsistent data
        inconsistent_prices = []
        for i, item in enumerate(order_items):
            if item.get("price") and item.get("quantity"):
                try:
                    price = float(item["price"])
                    quantity = float(item["quantity"])
                    if price * quantity <= 0:
                        inconsistent_prices.append(i)
                except (ValueError, TypeError):
                    pass
        
        if inconsistent_prices:
            issues.append(f"data_quality.inconsistent_prices: Items with inconsistent pricing at indices: {inconsistent_prices}")
        
        await self._log_tracking(order_id, "DATA_QUALITY_CHECKS", 
                               f"Data quality checks: {len(issues)} issues found")
        
        return {"issues": issues}
    
    async def _calculate_validation_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall validation score (0-1)"""
        total_checks = 0
        passed_checks = 0
        
        # Required fields score
        if "required_fields_check" in validation_result:
            total_checks += 1
            if validation_result["required_fields_check"]["completion_rate"] > 0.8:
                passed_checks += validation_result["required_fields_check"]["completion_rate"]
        
        # Data type validation score
        total_checks += 1
        if len(validation_result.get("data_type_errors", [])) == 0:
            passed_checks += 1
        
        # Business rule validation score
        total_checks += 1
        if len(validation_result.get("business_rule_violations", [])) == 0:
            passed_checks += 1
        
        # Catalog validation score
        total_checks += 1
        catalog_validation = validation_result.get("catalog_validation", {})
        valid_products = len(catalog_validation.get("valid_products", []))
        total_products = valid_products + len(catalog_validation.get("invalid_products", []))
        if total_products > 0:
            passed_checks += valid_products / total_products
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    def _is_valid_quantity(self, quantity: Any) -> bool:
        """Check if quantity is valid"""
        try:
            qty = float(quantity)
            return qty > 0 and qty <= 10000
        except (ValueError, TypeError):
            return False
    
    def _is_valid_price(self, price: Any) -> bool:
        """Check if price is valid"""
        try:
            p = float(price)
            return p >= 0 and p <= 100000
        except (ValueError, TypeError):
            return False
    
    def _is_valid_sku_code(self, sku_code: Any) -> bool:
        """Check if SKU code format is valid"""
        if not isinstance(sku_code, str):
            return False
        
        # Common SKU format patterns
        patterns = [
            r'^[A-Z0-9]{3,50}$',  # Basic alphanumeric
            r'^[A-Z0-9\-_]{3,50}$',  # With hyphens and underscores
            r'^\d{8,15}$',  # Numeric codes
        ]
        
        return any(re.match(pattern, sku_code) for pattern in patterns)
    
    def _is_valid_date(self, date_str: Any) -> bool:
        """Check if date format is valid"""
        if not isinstance(date_str, str):
            return False
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    async def _is_valid_product_code(self, sku_code: str) -> bool:
        """Check if product code exists in catalog (mock implementation)"""
        # Mock implementation - in real system, would check against database
        # Common FMCG product code patterns
        valid_prefixes = ['COCA', 'PEPS', 'NEST', 'UNIV', 'PROC', 'JOHN', 'KRAF']
        return any(sku_code.startswith(prefix) for prefix in valid_prefixes)
    
    async def _log_tracking(self, order_id: str, status: str, message: str, details: Optional[str] = None):
        """Log tracking information"""
        try:
            tracking_entry = OrderTracking(
                order_id=uuid.UUID(order_id),
                status=status,
                message=message,
                details=details
            )
            self.db.add(tracking_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error logging tracking: {str(e)}")
    
    def _analyze_data_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of input data for debugging"""
        if not data:
            return {"structure": "empty", "keys": []}
        
        structure = {}
        for key, value in data.items():
            if isinstance(value, dict):
                structure[key] = {"type": "dict", "keys": list(value.keys())}
            elif isinstance(value, list):
                structure[key] = {"type": "list", "length": len(value)}
                if value and isinstance(value[0], dict):
                    structure[key]["sample_keys"] = list(value[0].keys())
            else:
                structure[key] = {"type": type(value).__name__, "value": str(value)[:100]}
        
        return structure
    
    def _create_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mapping of expected vs actual fields"""
        mapping = {
            "order_level": {},
            "item_level": {},
            "retailer_level": {}
        }
        
        # Order level mapping
        order_fields = ["order_number", "retailer_info", "delivery_date", "priority"]
        for field in order_fields:
            mapping["order_level"][field] = {
                "present": field in data and data[field] is not None,
                "value": str(data.get(field, ""))[:50] if data.get(field) else None
            }
        
        # Item level mapping
        order_items = data.get("order_items", [])
        item_fields = ["sku_code", "quantity", "price"]
        for i, item in enumerate(order_items[:3]):  # Sample first 3 items
            mapping["item_level"][f"item_{i}"] = {}
            for field in item_fields:
                mapping["item_level"][f"item_{i}"][field] = {
                    "present": field in item and item[field] is not None,
                    "value": str(item.get(field, ""))[:50] if item.get(field) else None
                }
        
        # Retailer level mapping
        retailer_info = data.get("retailer_info", {})
        retailer_fields = ["retailer_name", "delivery_address", "contact_info"]
        for field in retailer_fields:
            mapping["retailer_level"][field] = {
                "present": field in retailer_info and retailer_info[field] is not None,
                "value": str(retailer_info.get(field, ""))[:50] if retailer_info.get(field) else None
            }
        
        return mapping
