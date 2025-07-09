az containerapp env create --name dispatchPlannerAppEnv --resource-group "ODL-Infosys-Hack-1775541-02" --location "East US"
az acr create --resource-group "ODL-Infosys-Hack-1775541-02" --name dispatchplannerregistry --sku Basic
az acr login -n dispatchplannerregistry 
docker buildx build . -t "dispatchplannerregistry.azurecr.io/dispatchplanner:latest"

docker push "dispatchplannerregistry.azurecr.io/dispatchplanner:latest"
az acr update -n dispatchplannerregistry --admin-enabled true
$RegistryPassword = az acr credential show --name dispatchplannerregistry --query "passwords[0].value" --output tsv
docker push "dispatchplannerregistry.azurecr.io/dispatchplanner:latest" 
az containerapp create `
    --name dispatchplannerapp `
    --resource-group "ODL-Infosys-Hack-1775541-02" `
    --environment dispatchPlannerAppEnv `
    --image dispatchplannerregistry.azurecr.io/dispatchplanner:latest `
    --target-port 8000 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 3 `
    --cpu 0.5 `
    --memory 1Gi `
    --registry-server dispatchplannerregistry.azurecr.io `
    --registry-username dispatchplannerregistry `
    --registry-password $RegistryPassword