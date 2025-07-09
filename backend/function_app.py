import azure.functions as func
from azure.functions import AsgiMiddleware
from app.main import app as fastapi_app

app = func.FunctionApp()

@app.function_name(name="HttpTrigger")
@app.route(route="{*route}", auth_level=func.AuthLevel.ANONYMOUS)
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    return AsgiMiddleware(fastapi_app).handle(req)