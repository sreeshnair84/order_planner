#!/bin/bash
# HTTPS Configuration Verification Script

echo "🔍 Testing HTTPS Configuration..."
echo "=================================="

# Test if HTTPS endpoint is accessible
echo "1. Testing HTTPS API endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "https://dispatchplannerapp.wonderfultree-66eac7c6.eastus.azurecontainerapps.io/health" | grep -q "200"; then
    echo "✅ HTTPS endpoint is accessible"
else
    echo "❌ HTTPS endpoint is not responding"
fi

# Test if HTTP endpoint is blocked (should fail or redirect)
echo "2. Testing HTTP endpoint (should be blocked)..."
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://dispatchplannerapp.wonderfultree-66eac7c6.eastus.azurecontainerapps.io/health" 2>/dev/null || echo "blocked")
if [ "$HTTP_RESPONSE" = "blocked" ] || [ "$HTTP_RESPONSE" = "000" ]; then
    echo "✅ HTTP endpoint is properly blocked"
elif [ "$HTTP_RESPONSE" = "307" ] || [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ]; then
    echo "⚠️  HTTP endpoint redirects (this might still cause mixed content issues)"
else
    echo "❌ HTTP endpoint is still accessible (status: $HTTP_RESPONSE)"
fi

# Check Container App ingress status
echo "3. Checking Container App ingress configuration..."
ALLOW_INSECURE=$(az containerapp show --name dispatchplannerapp --resource-group "ODL-Infosys-Hack-1775541-02" --query "properties.configuration.ingress.allowInsecure" -o tsv 2>/dev/null)
if [ "$ALLOW_INSECURE" = "false" ]; then
    echo "✅ Container App properly configured (allowInsecure: false)"
elif [ "$ALLOW_INSECURE" = "true" ]; then
    echo "⚠️  Container App still allows insecure traffic (allowInsecure: true)"
    echo "   👉 Please disable 'Allow insecure traffic' in Azure Portal"
else
    echo "❓ Could not check Container App configuration"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. If HTTP is not blocked, disable 'Allow insecure traffic' in Azure Portal"
echo "2. Test your frontend at: https://dispatchplanneraf.z13.web.core.windows.net/dashboard"
echo "3. Check browser DevTools for any remaining mixed content errors"
echo "4. Verify bearer tokens are included in API requests"
