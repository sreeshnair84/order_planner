import azure.functions as func
import json
import logging
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Azure Functions app
app_func = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app_func.route(route="api/{*route}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def api_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function HTTP trigger for API routes"""
    
    try:
        logger.info(f'Processing API request: {req.method} {req.url}')
        
        # Get request details
        method = req.method
        url = req.url
        headers = dict(req.headers)
        body = req.get_body()
        
        # Handle CORS preflight
        if method == "OPTIONS":
            return func.HttpResponse(
                "",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                }
            )
        
        # For now, return a simple response
        # In production, you would integrate with your FastAPI app here
        return func.HttpResponse(
            json.dumps({"message": "Order Management API", "method": method, "url": str(url)}),
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except Exception as e:
        logger.error(f'Error processing request: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*"
            }
        )

@app_func.route(route="{*route}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def catch_all(req: func.HttpRequest) -> func.HttpResponse:
    """Catch-all route for other requests"""
    
    try:
        logger.info(f'Processing catch-all request: {req.method} {req.url}')
        
        # Handle health check
        if req.url.endswith("/health"):
            return func.HttpResponse(
                json.dumps({"status": "healthy", "service": "Order Management System"}),
                status_code=200,
                mimetype="application/json"
            )
        
        # Default response
        return func.HttpResponse(
            json.dumps({"message": "Order Management System - Azure Functions", "status": "running"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f'Error in catch-all handler: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )
    
    # Handle request body
    try:
        body = req.get_body()
        asgi_request["body"] = body
    except:
        asgi_request["body"] = b""
    
    # Create response container
    response_data = {"status": 500, "headers": [], "body": b""}
    
    async def receive():
        return {
            "type": "http.request",
            "body": asgi_request["body"],
            "more_body": False,
        }
    
    async def send(message):
        if message["type"] == "http.response.start":
            response_data["status"] = message["status"]
            response_data["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response_data["body"] += message.get("body", b"")
    
    # Process request through FastAPI
    try:
        await app(asgi_request, receive, send)
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )
    
    # Convert headers back to dict format
    headers_dict = {}
    for header_tuple in response_data["headers"]:
        if len(header_tuple) >= 2:
            key = header_tuple[0].decode() if isinstance(header_tuple[0], bytes) else header_tuple[0]
            value = header_tuple[1].decode() if isinstance(header_tuple[1], bytes) else header_tuple[1]
            headers_dict[key] = value
    
    return func.HttpResponse(
        response_data["body"],
        status_code=response_data["status"],
        headers=headers_dict
    )
