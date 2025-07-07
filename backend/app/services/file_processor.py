import pandas as pd
import xml.etree.ElementTree as ET
from lxml import etree
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service class to process different file formats and extract order data"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xml', '.log', '.txt']
    
    async def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Process a file based on its type and extract order data"""
        try:
            if file_type.lower() == '.csv':
                return await self._process_csv(file_path)
            elif file_type.lower() == '.xml':
                return await self._process_xml(file_path)
            elif file_type.lower() in ['.log', '.txt']:
                return await self._process_log(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    async def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file and extract order data with SKU details"""
        try:
            df = pd.read_csv(file_path)
            
            # Basic validation
            if df.empty:
                raise ValueError("CSV file is empty")
            
            # Extract order data
            order_data = {
                "format": "csv",
                "total_rows": len(df),
                "columns": df.columns.tolist(),
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Try to identify standard order fields
            order_fields = self._identify_order_fields(df.columns.tolist())
            if order_fields:
                order_data["identified_fields"] = order_fields
            
            # Extract SKU items
            sku_items = self._extract_sku_items_from_csv(df, order_fields)
            if sku_items:
                order_data["sku_items"] = sku_items
            
            # Extract retailer information
            retailer_info = self._extract_retailer_info_from_csv(df, order_fields)
            if retailer_info:
                order_data["retailer_info"] = retailer_info
            
            # Calculate order summary
            order_summary = self._calculate_order_summary(sku_items)
            order_data["order_summary"] = order_summary
            
            # Basic data validation
            validation_result = self._validate_order_data(order_data)
            order_data["validation_result"] = validation_result
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise ValueError(f"Failed to process CSV file: {str(e)}")
    
    def _extract_sku_items_from_csv(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract SKU items from CSV data"""
        sku_items = []
        
        for index, row in df.iterrows():
            sku_item = {}
            
            # Extract basic SKU information
            if 'sku_code' in field_mapping:
                sku_item['sku_code'] = str(row[field_mapping['sku_code']])
            
            if 'product_name' in field_mapping:
                sku_item['product_name'] = str(row[field_mapping['product_name']])
            
            if 'category' in field_mapping:
                sku_item['category'] = str(row[field_mapping['category']])
            
            if 'brand' in field_mapping:
                sku_item['brand'] = str(row[field_mapping['brand']])
            
            if 'quantity' in field_mapping:
                try:
                    sku_item['quantity_ordered'] = int(row[field_mapping['quantity']])
                except (ValueError, TypeError):
                    sku_item['quantity_ordered'] = 0
            
            if 'unit_of_measure' in field_mapping:
                sku_item['unit_of_measure'] = str(row[field_mapping['unit_of_measure']])
            
            if 'unit_price' in field_mapping:
                try:
                    sku_item['unit_price'] = float(row[field_mapping['unit_price']])
                except (ValueError, TypeError):
                    sku_item['unit_price'] = 0.0
            
            if 'total_price' in field_mapping:
                try:
                    sku_item['total_price'] = float(row[field_mapping['total_price']])
                except (ValueError, TypeError):
                    sku_item['total_price'] = 0.0
            
            # Extract product attributes
            if 'weight' in field_mapping:
                try:
                    sku_item['weight_kg'] = float(row[field_mapping['weight']])
                except (ValueError, TypeError):
                    sku_item['weight_kg'] = 0.0
            
            if 'volume' in field_mapping:
                try:
                    sku_item['volume_m3'] = float(row[field_mapping['volume']])
                except (ValueError, TypeError):
                    sku_item['volume_m3'] = 0.0
            
            if 'temperature' in field_mapping:
                sku_item['temperature_requirement'] = str(row[field_mapping['temperature']])
            
            if 'fragile' in field_mapping:
                sku_item['fragile'] = bool(row[field_mapping['fragile']])
            
            # Only add if we have minimum required fields
            if 'sku_code' in sku_item and 'product_name' in sku_item:
                sku_items.append(sku_item)
        
        return sku_items
    
    def _extract_retailer_info_from_csv(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extract retailer information from CSV data"""
        retailer_info = {}
        
        # Try to get retailer info from first row (assuming it's consistent)
        if not df.empty:
            first_row = df.iloc[0]
            
            if 'customer' in field_mapping:
                retailer_info['name'] = str(first_row[field_mapping['customer']])
            
            if 'contact_person' in field_mapping:
                retailer_info['contact_person'] = str(first_row[field_mapping['contact_person']])
            
            if 'email' in field_mapping:
                retailer_info['email'] = str(first_row[field_mapping['email']])
            
            if 'phone' in field_mapping:
                retailer_info['phone'] = str(first_row[field_mapping['phone']])
            
            if 'address' in field_mapping:
                retailer_info['address'] = str(first_row[field_mapping['address']])
        
        return retailer_info
    
    def _calculate_order_summary(self, sku_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate order summary from SKU items"""
        summary = {
            'total_sku_count': len(sku_items),
            'total_quantity': 0,
            'total_weight_kg': 0.0,
            'total_volume_m3': 0.0,
            'subtotal': 0.0,
            'tax': 0.0,
            'total': 0.0
        }
        
        for item in sku_items:
            summary['total_quantity'] += item.get('quantity_ordered', 0)
            summary['total_weight_kg'] += item.get('weight_kg', 0.0) * item.get('quantity_ordered', 0)
            summary['total_volume_m3'] += item.get('volume_m3', 0.0) * item.get('quantity_ordered', 0)
            summary['subtotal'] += item.get('total_price', 0.0)
        
        summary['tax'] = summary['subtotal'] * 0.08  # 8% tax rate
        summary['total'] = summary['subtotal'] + summary['tax']
        
        return summary
    
    async def _process_xml(self, file_path: str) -> Dict[str, Any]:
        """Process XML file and extract order data"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Convert XML to dictionary
            xml_data = self._xml_to_dict(root)
            
            order_data = {
                "format": "xml",
                "root_element": root.tag,
                "data": xml_data,
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Try to extract order information
            order_info = self._extract_order_from_xml(xml_data)
            if order_info:
                order_data["order_info"] = order_info
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error processing XML file: {str(e)}")
            raise ValueError(f"Failed to process XML file: {str(e)}")
    
    async def _process_log(self, file_path: str) -> Dict[str, Any]:
        """Process log file and extract order data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract structured data from log
            log_entries = self._parse_log_content(content)
            
            order_data = {
                "format": "log",
                "total_lines": len(content.splitlines()),
                "entries": log_entries,
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Try to extract order information
            order_info = self._extract_order_from_log(log_entries)
            if order_info:
                order_data["order_info"] = order_info
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error processing log file: {str(e)}")
            raise ValueError(f"Failed to process log file: {str(e)}")
    
    def _identify_order_fields(self, columns: List[str]) -> Dict[str, str]:
        """Identify standard order fields from column names"""
        field_mapping = {}
        
        # Common field patterns
        patterns = {
            'order_id': r'order[_\s]?id|order[_\s]?number|order[_\s]?ref',
            'sku_code': r'sku[_\s]?code|product[_\s]?code|item[_\s]?code|part[_\s]?number',
            'product_name': r'product[_\s]?name|item[_\s]?name|description|product[_\s]?description',
            'category': r'category|product[_\s]?category|item[_\s]?category',
            'brand': r'brand|manufacturer|make',
            'quantity': r'quantity|qty|amount|count',
            'unit_of_measure': r'unit|uom|unit[_\s]?of[_\s]?measure',
            'unit_price': r'unit[_\s]?price|price[_\s]?per[_\s]?unit|rate',
            'total_price': r'total[_\s]?price|total[_\s]?cost|line[_\s]?total|extended[_\s]?price',
            'weight': r'weight|wt|mass',
            'volume': r'volume|vol|cubic|size',
            'temperature': r'temperature|temp|storage[_\s]?temp',
            'fragile': r'fragile|breakable|delicate',
            'date': r'date|time|order[_\s]?date',
            'customer': r'customer|client|retailer|company',
            'contact_person': r'contact[_\s]?person|contact[_\s]?name|rep|representative',
            'email': r'email|e[_\s]?mail|contact[_\s]?email',
            'phone': r'phone|telephone|contact[_\s]?phone|tel',
            'address': r'address|location|delivery[_\s]?address|shipping[_\s]?address'
        }
        
        for field, pattern in patterns.items():
            for col in columns:
                if re.search(pattern, col.lower()):
                    field_mapping[field] = col
                    break
        
        return field_mapping
    
    def _validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete order data and identify missing fields"""
        validation_errors = []
        missing_fields = []
        
        # Check for required order fields
        required_fields = ['retailer_info', 'sku_items']
        for field in required_fields:
            if field not in order_data or not order_data[field]:
                missing_fields.append(field)
        
        # Validate SKU items
        if 'sku_items' in order_data:
            for i, sku_item in enumerate(order_data['sku_items']):
                if not sku_item.get('sku_code'):
                    validation_errors.append(f"SKU item {i+1}: Missing SKU code")
                
                if not sku_item.get('product_name'):
                    validation_errors.append(f"SKU item {i+1}: Missing product name")
                
                if not sku_item.get('quantity_ordered', 0) > 0:
                    validation_errors.append(f"SKU item {i+1}: Invalid quantity")
        
        # Validate retailer info
        if 'retailer_info' in order_data:
            retailer_info = order_data['retailer_info']
            if not retailer_info.get('name'):
                missing_fields.append('retailer_name')
            
            if not retailer_info.get('email'):
                missing_fields.append('retailer_email')
        
        return {
            'is_valid': len(validation_errors) == 0 and len(missing_fields) == 0,
            'validation_errors': validation_errors,
            'missing_fields': missing_fields
        }
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _extract_order_from_xml(self, xml_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract order information from XML data"""
        # This is a simplified extraction - in real implementation,
        # you'd need to handle various XML schemas
        order_info = {}
        
        # Look for common order elements
        if 'order' in xml_data:
            order_info = xml_data['order']
        elif 'Order' in xml_data:
            order_info = xml_data['Order']
        
        return order_info if order_info else None
    
    def _parse_log_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse log content and extract structured data"""
        entries = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Try to extract timestamp
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2})', line)
            timestamp = timestamp_match.group(1) if timestamp_match else None
            
            # Try to extract log level
            level_match = re.search(r'\b(DEBUG|INFO|WARN|ERROR|FATAL)\b', line)
            level = level_match.group(1) if level_match else 'INFO'
            
            # Extract key-value pairs
            kv_pairs = re.findall(r'(\w+)=([^\s,]+)', line)
            
            entry = {
                'line_number': line_num,
                'timestamp': timestamp,
                'level': level,
                'message': line,
                'extracted_data': dict(kv_pairs) if kv_pairs else {}
            }
            
            entries.append(entry)
        
        return entries
    
    def _extract_order_from_log(self, log_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract order information from log entries"""
        order_info = {}
        
        for entry in log_entries:
            extracted_data = entry.get('extracted_data', {})
            
            # Look for order-related fields
            for key, value in extracted_data.items():
                if key.lower() in ['order_id', 'orderid', 'order_number']:
                    order_info['order_id'] = value
                elif key.lower() in ['customer', 'client', 'retailer']:
                    order_info['customer'] = value
                elif key.lower() in ['total', 'amount']:
                    order_info['total'] = value
        
        return order_info if order_info else None
    
    def validate_order_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parsed order data and identify missing fields"""
        required_fields = [
            'retailer_info',
            'sku_items',
            'order_summary'
        ]
        
        missing_fields = []
        validation_errors = []
        
        # Check for required fields
        for field in required_fields:
            if field not in parsed_data or not parsed_data[field]:
                missing_fields.append(field)
        
        # Validate SKU items
        if 'sku_items' in parsed_data:
            for i, sku_item in enumerate(parsed_data['sku_items']):
                if not sku_item.get('sku_code'):
                    validation_errors.append(f"SKU item {i+1}: Missing SKU code")
                
                if not sku_item.get('product_name'):
                    validation_errors.append(f"SKU item {i+1}: Missing product name")
                
                if not sku_item.get('quantity_ordered', 0) > 0:
                    validation_errors.append(f"SKU item {i+1}: Invalid quantity")
        
        # Validate retailer information
        if 'retailer_info' in parsed_data:
            retailer_info = parsed_data['retailer_info']
            if not retailer_info.get('name'):
                missing_fields.append('retailer_name')
            
            if not retailer_info.get('email'):
                missing_fields.append('retailer_email')
        
        return {
            'is_valid': len(missing_fields) == 0 and len(validation_errors) == 0,
            'missing_fields': missing_fields,
            'validation_errors': validation_errors
        }
