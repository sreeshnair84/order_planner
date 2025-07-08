import os
import aiofiles
import logging
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceExistsError

logger = logging.getLogger(__name__)

class AzureBlobService:
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self._client = None
        self._container_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the Azure Blob Service client and cleanup resources"""
        if self._client:
            await self._client.close()
            self._client = None
            self._container_client = None

    async def get_client(self):
        if not self._client:
            logger.info(f"Initializing Azure Blob Service Client")
            self._client = BlobServiceClient.from_connection_string(self.connection_string)
            logger.info("Azure Blob Service Client initialized successfully")
        return self._client

    async def get_container_client(self):
        if not self._container_client:
            logger.info(f"Getting container client for: {self.container_name}")
            client = await self.get_client()
            self._container_client = client.get_container_client(self.container_name)
            try:
                await self._container_client.create_container()
                logger.info(f"Container {self.container_name} created")
            except ResourceExistsError:
                logger.info(f"Container {self.container_name} already exists")
        return self._container_client

    async def upload_file(self, file_path: str, blob_name: str = None) -> str:
        container_client = await self.get_container_client()
        if not blob_name:
            blob_name = os.path.basename(file_path)
        async with aiofiles.open(file_path, 'rb') as f:
            data = await f.read()
            await container_client.upload_blob(blob_name, data, overwrite=True)
        return blob_name

    async def upload_fileobj(self, file_obj, blob_name: str) -> str:
        try:
            logger.info(f"Starting upload to blob: {blob_name}")
            container_client = await self.get_container_client()
            data = await file_obj.read()
            logger.info(f"Read {len(data)} bytes from file object")
            
            await container_client.upload_blob(blob_name, data, overwrite=True)
            logger.info(f"Successfully uploaded blob: {blob_name}")
            return blob_name
        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {str(e)}")
            raise

    async def get_blob_url(self, blob_name: str) -> str:
        try:
            client = await self.get_client()
            blob_client = client.get_blob_client(container=self.container_name, blob=blob_name)
            url = blob_client.url
            logger.info(f"Generated blob URL: {url}")
            return url
        except Exception as e:
            logger.error(f"Error getting blob URL for {blob_name}: {str(e)}")
            raise

    async def download_blob(self, blob_name: str) -> bytes:
        """Download blob content as bytes"""
        try:
            logger.info(f"Starting download of blob: {blob_name}")
            client = await self.get_client()
            blob_client = client.get_blob_client(container=self.container_name, blob=blob_name)
            
            # Download blob content
            download_stream = await blob_client.download_blob()
            blob_data = await download_stream.readall()
            
            logger.info(f"Successfully downloaded blob {blob_name}: {len(blob_data)} bytes")
            return blob_data
            
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {str(e)}")
            # Check for authentication errors
            if "AuthenticationFailed" in str(e):
                logger.error("Azure Storage authentication failed. Please check:")
                logger.error("1. Connection string is correct and not expired")
                logger.error("2. Storage account key hasn't been regenerated")
                logger.error("3. System clock is synchronized")
            raise
    
    async def download_blob_to_file(self, blob_name: str, file_path: str) -> str:
        """Download blob content to a local file"""
        try:
            logger.info(f"Downloading blob {blob_name} to file: {file_path}")
            blob_data = await self.download_blob(blob_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(blob_data)
            
            logger.info(f"Successfully saved blob to file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name} to file {file_path}: {str(e)}")
            raise
    
    async def blob_exists(self, blob_name: str) -> bool:
        """Check if a blob exists"""
        try:
            client = await self.get_client()
            blob_client = client.get_blob_client(container=self.container_name, blob=blob_name)
            
            # Try to get blob properties
            await blob_client.get_blob_properties()
            return True
            
        except Exception as e:
            if "BlobNotFound" in str(e):
                return False
            logger.error(f"Error checking blob existence {blob_name}: {str(e)}")
            raise
    
    async def validate_connection(self) -> bool:
        """Validate the Azure Storage connection"""
        try:
            client = await self.get_client()
            # Try to get account information to validate connection
            account_info = await client.get_account_information()
            logger.info(f"Azure Storage connection validated successfully. Account kind: {account_info.get('account_kind', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Azure Storage connection validation failed: {str(e)}")
            if "AuthenticationFailed" in str(e):
                logger.error("Authentication failed - please check your connection string and account key")
            return False
