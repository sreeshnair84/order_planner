/**
 * Unified Order Processing Component
 * Provides a streamlined interface for order processing using the consolidated backend.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { getApiUrl } from '../../utils/api';

const UnifiedOrderProcessor = ({ orderId, onProcessingComplete }) => {
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [orderSummary, setOrderSummary] = useState(null);
  const [processingMethod, setProcessingMethod] = useState('unified_processor');
  const [availableMethods, setAvailableMethods] = useState({});

  useEffect(() => {
    loadOrderSummary();
    loadProcessingMethods();
  }, [orderId]);

  const loadOrderSummary = async () => {
    try {
      const response = await fetch(getApiUrl(`api/orders/${orderId}/summary-unified`), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOrderSummary(data.data);
      }
    } catch (error) {
      console.error('Error loading order summary:', error);
    }
  };

  const loadProcessingMethods = async () => {
    try {
      const response = await fetch(getApiUrl('api/orders/processing/methods'));
      if (response.ok) {
        const data = await response.json();
        setAvailableMethods(data.methods);
      }
    } catch (error) {
      console.error('Error loading processing methods:', error);
    }
  };

  const processOrderComplete = async () => {
    setProcessing(true);
    setError(null);
    setResults(null);
    setProgress(0);

    try {
      setCurrentStep('Initializing...');
      setProgress(10);

      const response = await fetch(getApiUrl(`api/orders/${orderId}/process-unified`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          use_agent: processingMethod === 'ai_agent'
        })
      });

      setProgress(50);
      setCurrentStep('Processing...');

      if (response.ok) {
        const data = await response.json();
        setProgress(100);
        setCurrentStep('Completed');
        setResults(data);
        
        if (onProcessingComplete) {
          onProcessingComplete(data);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Processing failed');
      }
    } catch (error) {
      setError(error.message);
      setCurrentStep('Failed');
    } finally {
      setProcessing(false);
    }
  };

  const processIndividualStep = async (stepName) => {
    setProcessing(true);
    setError(null);

    try {
      setCurrentStep(`Processing ${stepName}...`);

      const response = await fetch(getApiUrl(`api/orders/${orderId}/process-step`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          step_name: stepName,
          use_agent: processingMethod === 'ai_agent'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
        setCurrentStep(`${stepName} completed`);
        await loadOrderSummary(); // Refresh summary
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `${stepName} processing failed`);
      }
    } catch (error) {
      setError(error.message);
      setCurrentStep(`${stepName} failed`);
    } finally {
      setProcessing(false);
    }
  };

  const retryStep = async (stepName) => {
    setProcessing(true);
    setError(null);

    try {
      setCurrentStep(`Retrying ${stepName}...`);

      const response = await fetch(getApiUrl(`api/orders/${orderId}/retry-step`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          step_name: stepName
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
        setCurrentStep(`${stepName} retry completed`);
        await loadOrderSummary();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `${stepName} retry failed`);
      }
    } catch (error) {
      setError(error.message);
      setCurrentStep(`${stepName} retry failed`);
    } finally {
      setProcessing(false);
    }
  };

  const renderOrderSummary = () => {
    if (!orderSummary) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Order Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Order Number</label>
              <p className="text-lg font-semibold">{orderSummary.order_number}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <Badge variant={orderSummary.status === 'PROCESSED' ? 'success' : 'warning'}>
                {orderSummary.status}
              </Badge>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">SKU Count</label>
              <p className="text-lg">{orderSummary.totals?.sku_count || 0}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Total Value</label>
              <p className="text-lg font-semibold">${orderSummary.totals?.total?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Processing Info</label>
              <div className="space-y-1">
                <p className="text-sm">
                  Parsed Data: {orderSummary.processing_info?.parsed_data_available ? '✅' : '❌'}
                </p>
                <p className="text-sm">
                  Priority: <Badge variant="outline">{orderSummary.processing_info?.priority || 'LOW'}</Badge>
                </p>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Delivery Info</label>
              <div className="space-y-1">
                <p className="text-sm">{orderSummary.customer_info?.address || 'No address'}</p>
                <p className="text-sm">Contact: {orderSummary.customer_info?.contact || 'No contact'}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderProcessingMethods = () => (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Processing Method</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(availableMethods).map(([key, method]) => (
            <div key={key} className="flex items-start space-x-3">
              <input
                type="radio"
                id={key}
                name="processingMethod"
                value={key}
                checked={processingMethod === key}
                onChange={(e) => setProcessingMethod(e.target.value)}
                className="mt-1"
              />
              <div className="flex-1">
                <label htmlFor={key} className="font-medium cursor-pointer">
                  {method.name}
                </label>
                <p className="text-sm text-gray-600">{method.description}</p>
                <div className="flex space-x-2 mt-1">
                  {method.advantages?.map((advantage, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {advantage}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderProcessingControls = () => (
    <Tabs defaultValue="complete" className="mb-6">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="complete">Complete Processing</TabsTrigger>
        <TabsTrigger value="steps">Individual Steps</TabsTrigger>
      </TabsList>

      <TabsContent value="complete" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Complete Order Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Process the entire order workflow in one operation: parse → validate → email → SKU processing → logistics.
            </p>
            
            {processing && (
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span>{currentStep}</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} className="w-full" />
              </div>
            )}

            <Button 
              onClick={processOrderComplete}
              disabled={processing}
              className="w-full"
            >
              {processing ? 'Processing...' : 'Start Complete Processing'}
            </Button>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="steps" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Individual Processing Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {['parse', 'validate', 'email', 'sku_processing', 'logistics'].map((step) => (
                <div key={step} className="space-y-2">
                  <Button
                    onClick={() => processIndividualStep(step)}
                    disabled={processing}
                    variant="outline"
                    className="w-full"
                  >
                    {step.replace('_', ' ').toUpperCase()}
                  </Button>
                  <Button
                    onClick={() => retryStep(step)}
                    disabled={processing}
                    variant="ghost"
                    size="sm"
                    className="w-full text-xs"
                  >
                    Retry {step}
                  </Button>
                </div>
              ))}
            </div>

            {processing && (
              <div className="mt-4">
                <p className="text-sm text-gray-600">{currentStep}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );

  const renderResults = () => {
    if (!results) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Processing Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Badge variant={results.success ? 'success' : 'destructive'}>
                {results.success ? 'Success' : 'Failed'}
              </Badge>
              <Badge variant="outline">
                {results.processing_method || 'unknown'}
              </Badge>
            </div>

            <p className="text-sm">{results.message}</p>

            {results.data && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Processing Details</h4>
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(results.data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {renderOrderSummary()}
      {renderProcessingMethods()}
      {renderProcessingControls()}
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {renderResults()}
    </div>
  );
};

export default UnifiedOrderProcessor;
