import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
from app.utils.config import settings

logger = logging.getLogger(__name__)

class AzureFunctionsClient:
    """Client for communicating with Azure Functions"""
    
    def __init__(self):
        self.base_url = settings.AZURE_FUNCTIONS_BASE_URL 
        self.function_key = settings.AZURE_FUNCTIONS_KEY 
        self.timeout = httpx.Timeout(120.0)  # Increased timeout for file processing
        
    async def process_order_file(self, order_id: str) -> Dict[str, Any]:
        """Call Azure Function to process order file"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}",
                    params={
                        "order_id": order_id
                    },
                    headers={
                        "x-functions-key": self.function_key
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Order file processing completed for {order_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Functions HTTP error for order {order_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to process order file: HTTP {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f"Azure Functions timeout for order {order_id}: {e}")
            raise Exception("Azure Functions request timed out")
        except Exception as e:
            logger.error(f"Error calling Azure Functions for order {order_id}: {e}")
            raise Exception(f"Azure Functions call failed: {e}")
    
    async def validate_order_completeness(self, order_id: str) -> Dict[str, Any]:
        """Call Azure Function to validate order completeness"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/validate_order_completeness",
                    params={
                        "order_id": order_id,
                        "code": self.function_key
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Order validation completed for {order_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Functions validation error for order {order_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to validate order: HTTP {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f"Azure Functions validation timeout for order {order_id}: {e}")
            raise Exception("Validation request timed out")
        except Exception as e:
            logger.error(f"Error calling validation function for order {order_id}: {e}")
            raise Exception(f"Validation function call failed: {e}")
    
    async def generate_draft_email(self, order_id: str) -> Dict[str, Any]:
        """Call Azure Function to generate draft email"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/draft_order_email",
                    params={
                        "order_id": order_id,
                        "code": self.function_key
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Draft email generated for order {order_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Functions email generation error for order {order_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to generate email: HTTP {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f"Azure Functions email timeout for order {order_id}: {e}")
            raise Exception("Email generation request timed out")
        except Exception as e:
            logger.error(f"Error calling email generation function for order {order_id}: {e}")
            raise Exception(f"Email generation function call failed: {e}")
    
    async def extract_retailer_info(self, order_id: str) -> Dict[str, Any]:
        """Call Azure Function to extract retailer information"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/extract_retailer_info",
                    params={
                        "order_id": order_id,
                        "code": self.function_key
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Retailer extraction completed for order {order_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Functions retailer extraction error for order {order_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to extract retailer info: HTTP {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f"Azure Functions retailer extraction timeout for order {order_id}: {e}")
            raise Exception("Retailer extraction request timed out")
        except Exception as e:
            logger.error(f"Error calling retailer extraction function for order {order_id}: {e}")
            raise Exception(f"Retailer extraction function call failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Azure Functions health"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    params={"code": self.function_key}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info("Azure Functions health check passed")
                return result
                
        except Exception as e:
            logger.error(f"Azure Functions health check failed: {e}")
            raise Exception(f"Health check failed: {e}")
