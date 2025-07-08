from typing import Dict, List, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking, EmailCommunication
from app.models.user import User
from decimal import Decimal
import logging
import uuid
from datetime import datetime
import pandas as pd
import xml.etree.ElementTree as ET
from lxml import etree
import re
import json

logger = logging.getLogger(__name__)

class FileParserService:
    """Enhanced file parser service with comprehensive logging"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.supported_formats = ['.csv', '.xml', '.log', '.txt', '.json']
    
    def _make_json_serializable(self, obj):
        """Convert numpy/pandas data types to JSON serializable types"""
        import numpy as np
        # Handle pandas Series or numpy arrays
        if isinstance(obj, (pd.Series, np.ndarray)):
            return [self._make_json_serializable(item) for item in obj.tolist()]
        # Handle tuple
        elif isinstance(obj, tuple):
            return [self._make_json_serializable(item) for item in obj]
        # Handle dict or list
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        # Handle pandas/numpy scalar types
        elif hasattr(obj, 'dtype'):
            if 'int' in str(obj.dtype):
                return int(obj)
            elif 'float' in str(obj.dtype):
                return float(obj)
            elif 'bool' in str(obj.dtype):
                return bool(obj)
            else:
                return str(obj)
        # Handle pd.NA, np.nan, None
        elif (isinstance(obj, float) and pd.isna(obj)) or obj is pd.NA:
            return None
        else:
            return obj
    
    async def parse_file(self, order_id: str, file_path: str, file_type: str) -> Dict[str, Any]:
        """Parse file and log all steps for tracking. Supports Azure Blob URLs."""
        try:
            # Log parsing start
            await self._log_tracking(order_id, "FILE_PARSING_STARTED", 
                                   f"Starting to parse {file_type} file: {file_path}")

            # If file_path is an Azure Blob URL, download to temp file
            local_path = file_path
            if file_path.startswith("https://") and ".blob.core.windows.net/" in file_path:
                try:
                    import tempfile
                    from app.services.azure_blob_service import AzureBlobService
                    from app.utils.config import settings
                    from urllib.parse import urlparse
                    
                    # Parse container and blob name from URL
                    url = urlparse(file_path)
                    path_parts = url.path.lstrip('/').split('/', 1)
                    container_name = path_parts[0]
                    blob_name = path_parts[1] if len(path_parts) > 1 else ''
                    
                    logger.info(f"Downloading Azure blob: container={container_name}, blob={blob_name}")
                    
                    # Use our enhanced Azure Blob Service with proper error handling
                    connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
                    if not connection_string or "your-account-key" in connection_string:
                        raise ValueError("Azure Storage connection string not properly configured")
                    
                    async with AzureBlobService(connection_string, container_name) as blob_service:
                        # Validate connection first
                        if not await blob_service.validate_connection():
                            raise ValueError("Failed to validate Azure Storage connection")
                        
                        # Check if blob exists
                        if not await blob_service.blob_exists(blob_name):
                            raise ValueError(f"Blob {blob_name} not found in container {container_name}")
                        
                        # Download blob data
                        blob_data = await blob_service.download_blob(blob_name)
                        
                        # Create temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as tmp:
                            tmp.write(blob_data)
                            local_path = tmp.name
                            
                        logger.info(f"Successfully downloaded blob to temporary file: {local_path}")
                        
                except Exception as download_error:
                    logger.error(f"Failed to download Azure blob: {str(download_error)}")
                    await self._log_tracking(order_id, "FILE_DOWNLOAD_ERROR", 
                                           f"Failed to download file from Azure: {str(download_error)}")
                    raise ValueError(f"Cannot access file from Azure Blob Storage: {str(download_error)}")

            if file_type.lower() == '.csv':
                result = await self._parse_csv(order_id, local_path)
            elif file_type.lower() == '.xml':
                result = await self._parse_xml(order_id, local_path)
            elif file_type.lower() in ['.log', '.txt']:
                result = await self._parse_log(order_id, local_path)
            elif file_type.lower() == '.json':
                result = await self._parse_json(order_id, local_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Log parsing completion
            await self._log_tracking(order_id, "FILE_PARSING_COMPLETED", 
                                   f"Successfully parsed {file_type} file with {result.get('total_records', 0)} records")

            return result

        except Exception as e:
            error_msg = f"Error parsing file {file_path}: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "FILE_PARSING_ERROR", error_msg)
            
            # Clean up temporary file if it was created
            if local_path != file_path and local_path.startswith('/tmp') or local_path.startswith('\\tmp'):
                try:
                    import os
                    os.unlink(local_path)
                    logger.info(f"Cleaned up temporary file: {local_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {local_path}: {cleanup_error}")
            
            raise
        finally:
            # Always clean up temporary file if it was created
            if 'local_path' in locals() and local_path != file_path:
                try:
                    import os
                    if os.path.exists(local_path):
                        os.unlink(local_path)
                        logger.info(f"Cleaned up temporary file: {local_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {local_path}: {cleanup_error}")
    
    async def _parse_csv(self, order_id: str, file_path: str) -> Dict[str, Any]:
        """Parse CSV file with pandas and extract structured data"""
        try:
            # Read CSV with error handling
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Reset index if it's a MultiIndex to avoid tuple issues
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(drop=True)
            
            await self._log_tracking(order_id, "CSV_PARSING_PROGRESS", 
                                   f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            # Basic validation
            if df.empty:
                raise ValueError("CSV file is empty")
            
            # Identify data structure
            columns = df.columns.tolist()
            field_mapping = await self._identify_order_fields(columns)
            
            await self._log_tracking(order_id, "CSV_FIELD_MAPPING", 
                                   f"Identified fields: {field_mapping}")
            
            # Extract structured data
            parsed_data = {
                "format": "csv",
                "total_records": int(len(df)),
                "columns": [str(col) for col in columns],
                "field_mapping": field_mapping,
                "parsed_at": datetime.utcnow().isoformat(),
                "data_summary": {
                    "total_rows": int(len(df)),
                    "total_columns": int(len(df.columns)),
                    "memory_usage": int(df.memory_usage(deep=True).sum())
                }
            }
            
            # Extract order items
            order_items = await self._extract_order_items_from_csv(df, field_mapping)
            parsed_data["order_items"] = order_items
            
            # Extract retailer information
            retailer_info = await self._extract_retailer_info_from_csv(df, field_mapping)
            parsed_data["retailer_info"] = retailer_info
            
            # Calculate order summary
            order_summary = await self._calculate_order_summary(order_items)
            parsed_data["order_summary"] = order_summary
            
            await self._log_tracking(order_id, "CSV_EXTRACTION_COMPLETED", 
                                   f"Extracted {len(order_items)} order items")
            
            # Ensure all data is JSON serializable
            parsed_data = self._make_json_serializable(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            error_msg = f"CSV parsing error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "CSV_PARSING_ERROR", error_msg)
            raise
    
    async def _parse_xml(self, order_id: str, file_path: str) -> Dict[str, Any]:
        """Parse XML file using lxml/ElementTree"""
        try:
            # Parse XML with lxml for better error handling
            parser = etree.XMLParser(recover=True)
            tree = etree.parse(file_path, parser)
            root = tree.getroot()
            
            await self._log_tracking(order_id, "XML_PARSING_PROGRESS", 
                                   f"Loaded XML with root element: {root.tag}")
            
            # Extract order data structure
            parsed_data = {
                "format": "xml",
                "root_element": root.tag,
                "namespace": root.nsmap if hasattr(root, 'nsmap') else {},
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Extract order items based on common XML patterns
            order_items = await self._extract_order_items_from_xml(root)
            parsed_data["order_items"] = order_items
            parsed_data["total_records"] = len(order_items)
            
            # Extract retailer information
            retailer_info = await self._extract_retailer_info_from_xml(root)
            parsed_data["retailer_info"] = retailer_info
            
            # Calculate order summary
            order_summary = await self._calculate_order_summary(order_items)
            parsed_data["order_summary"] = order_summary
            
            await self._log_tracking(order_id, "XML_EXTRACTION_COMPLETED", 
                                   f"Extracted {len(order_items)} order items from XML")
            
            return parsed_data
            
        except Exception as e:
            error_msg = f"XML parsing error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "XML_PARSING_ERROR", error_msg)
            raise
    
    async def _parse_log(self, order_id: str, file_path: str) -> Dict[str, Any]:
        """Parse log file using regex patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            await self._log_tracking(order_id, "LOG_PARSING_PROGRESS", 
                                   f"Loaded log file with {len(content)} characters")
            
            # Common log patterns for order data
            patterns = {
                'order_number': r'ORDER[_-]?(?:NUMBER|ID)[:\s]+([A-Z0-9\-]+)',
                'sku_code': r'SKU[:\s]+([A-Z0-9\-]+)',
                'quantity': r'QTY[:\s]+(\d+)',
                'price': r'PRICE[:\s]+\$?(\d+\.?\d*)',
                'retailer': r'RETAILER[:\s]+([A-Z\s]+)',
                'timestamp': r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})'
            }
            
            extracted_data = {}
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                extracted_data[key] = matches
            
            # Structure the data
            parsed_data = {
                "format": "log",
                "file_size": len(content),
                "extracted_patterns": extracted_data,
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Convert to order items format
            order_items = await self._convert_log_to_order_items(extracted_data)
            parsed_data["order_items"] = order_items
            parsed_data["total_records"] = len(order_items)
            
            await self._log_tracking(order_id, "LOG_EXTRACTION_COMPLETED", 
                                   f"Extracted {len(order_items)} order items from log patterns")
            
            return parsed_data
            
        except Exception as e:
            error_msg = f"Log parsing error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "LOG_PARSING_ERROR", error_msg)
            raise
    
    async def _parse_json(self, order_id: str, file_path: str) -> Dict[str, Any]:
        """Parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            await self._log_tracking(order_id, "JSON_PARSING_PROGRESS", 
                                   f"Loaded JSON with {len(data) if isinstance(data, (list, dict)) else 1} items")
            
            parsed_data = {
                "format": "json",
                "data_type": type(data).__name__,
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Extract order items based on JSON structure
            if isinstance(data, list):
                order_items = data
            elif isinstance(data, dict):
                # Look for common keys that contain order items
                order_items = data.get('orders', data.get('items', data.get('order_items', [data])))
            else:
                order_items = [data]
            
            parsed_data["order_items"] = order_items
            parsed_data["total_records"] = len(order_items)
            
            await self._log_tracking(order_id, "JSON_EXTRACTION_COMPLETED", 
                                   f"Extracted {len(order_items)} order items from JSON")
            
            return parsed_data
            
        except Exception as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "JSON_PARSING_ERROR", error_msg)
            raise
    
    async def _identify_order_fields(self, columns: List[str]) -> Dict[str, str]:
        """Identify order fields from column names"""
        field_mapping = {}
        
        # Common field patterns
        field_patterns = {
            'order_number': ['order_number', 'order_id', 'order_no', 'orderno', 'order'],
            'sku_code': ['sku', 'sku_code', 'product_code', 'item_code', 'code'],
            'product_name': ['product_name', 'product', 'item_name', 'name', 'description'],
            'quantity': ['quantity', 'qty', 'amount', 'count'],
            'price': ['price', 'unit_price', 'cost', 'rate'],
            'category': ['category', 'cat', 'type', 'class'],
            'brand': ['brand', 'manufacturer', 'vendor'],
            'retailer': ['retailer', 'customer', 'client', 'store'],
            'delivery_date': ['delivery_date', 'due_date', 'ship_date', 'date']
        }
        
        for field_name, patterns in field_patterns.items():
            for column in columns:
                if any(pattern.lower() in column.lower() for pattern in patterns):
                    field_mapping[field_name] = column
                    break
        
        return field_mapping
    
    async def _extract_order_items_from_csv(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract order items from CSV DataFrame"""
        order_items = []
        
        for index, row in df.iterrows():
            # Handle index properly - it might be a tuple or scalar
            if isinstance(index, tuple):
                row_index = index[0] if index else 0
            else:
                row_index = index
            
            item = {
                'row_index': int(row_index),
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            # Map fields
            for field_name, column_name in field_mapping.items():
                if column_name in df.columns:
                    value = row[column_name]
                    if pd.notna(value):
                        item[field_name] = self._make_json_serializable(value)
            
            order_items.append(item)
        
        return order_items
    
    async def _extract_retailer_info_from_csv(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extract retailer information from CSV"""
        retailer_info = {}
        
        if 'retailer' in field_mapping:
            retailer_column = field_mapping['retailer']
            if retailer_column in df.columns:
                unique_retailers = df[retailer_column].dropna().unique()
                retailer_info['retailers'] = [self._make_json_serializable(r) for r in unique_retailers.tolist()]
                if len(unique_retailers) == 1:
                    retailer_info['primary_retailer'] = self._make_json_serializable(unique_retailers[0])
        
        return retailer_info
    
    async def _extract_order_items_from_xml(self, root) -> List[Dict[str, Any]]:
        """Extract order items from XML root element"""
        order_items = []
        
        # Common XML patterns for order items
        item_patterns = ['item', 'product', 'sku', 'order_item', 'line_item']
        
        for pattern in item_patterns:
            items = root.findall(f".//{pattern}")
            if items:
                for item in items:
                    item_data = {
                        'xml_tag': item.tag,
                        'extracted_at': datetime.utcnow().isoformat()
                    }
                    
                    # Extract attributes
                    item_data.update(item.attrib)
                    
                    # Extract child elements
                    for child in item:
                        item_data[child.tag] = child.text
                    
                    order_items.append(item_data)
                break
        
        return order_items
    
    async def _extract_retailer_info_from_xml(self, root) -> Dict[str, Any]:
        """Extract retailer information from XML"""
        retailer_info = {}
        
        # Look for retailer information in common locations
        retailer_patterns = ['retailer', 'customer', 'client', 'store']
        
        for pattern in retailer_patterns:
            elements = root.findall(f".//{pattern}")
            if elements:
                retailer_info[pattern] = [elem.text for elem in elements if elem.text]
        
        return retailer_info
    
    async def _convert_log_to_order_items(self, extracted_data: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Convert extracted log data to order items format"""
        order_items = []
        
        # Assume parallel arrays for different fields
        max_length = max(len(values) for values in extracted_data.values() if values)
        
        for i in range(max_length):
            item = {
                'log_entry_index': i,
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            for field_name, values in extracted_data.items():
                if i < len(values):
                    item[field_name] = values[i]
            
            order_items.append(item)
        
        return order_items
    
    async def _calculate_order_summary(self, order_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate order summary statistics"""
        summary = {
            'total_items': len(order_items),
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        # Calculate totals if numeric fields are present
        total_quantity = 0
        total_value = 0
        
        for item in order_items:
            if 'quantity' in item:
                try:
                    qty_value = item['quantity']
                    if isinstance(qty_value, tuple):
                        qty_value = qty_value[0] if qty_value else 0
                    total_quantity += float(qty_value)
                except (ValueError, TypeError):
                    pass
            
            if 'price' in item and 'quantity' in item:
                try:
                    price_value = item['price']
                    qty_value = item['quantity']
                    
                    if isinstance(price_value, tuple):
                        price_value = price_value[0] if price_value else 0
                    if isinstance(qty_value, tuple):
                        qty_value = qty_value[0] if qty_value else 0
                    
                    price = float(price_value)
                    qty = float(qty_value)
                    total_value += price * qty
                except (ValueError, TypeError):
                    pass
        
        summary['total_quantity'] = self._make_json_serializable(total_quantity)
        summary['total_value'] = self._make_json_serializable(total_value)
        
        return summary
    
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
