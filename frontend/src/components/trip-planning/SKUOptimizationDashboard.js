import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const SKUOptimizationDashboard = ({ consolidationResults, onOptimizationParamsChange }) => {
  const [optimizationParams, setOptimizationParams] = useState({
    targetSkuMin: 90,
    targetSkuMax: 100,
    maxTripWeight: 25000,
    maxTripVolume: 100,
    maxDeliveryStops: 20,
    maxTripDuration: 8
  });

  const [skuEfficiencyMetrics, setSkuEfficiencyMetrics] = useState(null);

  // ...existing code...

  const calculateSKUEfficiencyMetrics = useCallback(() => {
    if (!consolidationResults || !consolidationResults.trip_groups) return;

    const metrics = {
      totalSKUs: consolidationResults.total_skus,
      targetCompliance: consolidationResults.trip_groups.filter(group => 
        group.sku_count >= optimizationParams.targetSkuMin && 
        group.sku_count <= optimizationParams.targetSkuMax
      ).length,
      averageSKUPerTrip: consolidationResults.trip_groups.reduce((sum, group) => sum + group.sku_count, 0) / consolidationResults.trip_groups.length,
      skuDistribution: consolidationResults.trip_groups.map((group, index) => ({
        tripId: `Trip ${index + 1}`,
        skuCount: group.sku_count,
        efficiency: group.delivery_efficiency * 100,
        weight: group.total_weight_kg,
        volume: group.total_volume_m3
      })),
      constraintViolations: consolidationResults.trip_groups.filter(group => 
        group.sku_count < optimizationParams.targetSkuMin || 
        group.sku_count > optimizationParams.targetSkuMax ||
        group.total_weight_kg > optimizationParams.maxTripWeight ||
        group.total_volume_m3 > optimizationParams.maxTripVolume
      )
    };

    setSkuEfficiencyMetrics(metrics);
  }, [consolidationResults, optimizationParams]);

  useEffect(() => {
    if (consolidationResults) {
      calculateSKUEfficiencyMetrics();
    }
  }, [consolidationResults, calculateSKUEfficiencyMetrics]);

  const handleParamChange = (param, value) => {
    const newParams = { ...optimizationParams, [param]: value };
    setOptimizationParams(newParams);
    onOptimizationParamsChange(newParams);
  };

  const getSKUComplianceColor = (skuCount) => {
    if (skuCount >= optimizationParams.targetSkuMin && skuCount <= optimizationParams.targetSkuMax) {
      return '#10B981'; // Green
    } else if (skuCount >= optimizationParams.targetSkuMin - 10 && skuCount <= optimizationParams.targetSkuMax + 10) {
      return '#F59E0B'; // Yellow
    } else {
      return '#EF4444'; // Red
    }
  };

  const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6'];

  return (
    <div className="space-y-6">
      {/* SKU Optimization Target Controls */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">SKU Optimization Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Target SKU Min</label>
            <input
              type="number"
              value={optimizationParams.targetSkuMin}
              onChange={(e) => handleParamChange('targetSkuMin', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="1"
              max="150"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Target SKU Max</label>
            <input
              type="number"
              value={optimizationParams.targetSkuMax}
              onChange={(e) => handleParamChange('targetSkuMax', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="1"
              max="150"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Trip Weight (kg)</label>
            <input
              type="number"
              value={optimizationParams.maxTripWeight}
              onChange={(e) => handleParamChange('maxTripWeight', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="1000"
              max="50000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Trip Volume (m³)</label>
            <input
              type="number"
              value={optimizationParams.maxTripVolume}
              onChange={(e) => handleParamChange('maxTripVolume', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="10"
              max="200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Delivery Stops</label>
            <input
              type="number"
              value={optimizationParams.maxDeliveryStops}
              onChange={(e) => handleParamChange('maxDeliveryStops', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="5"
              max="50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Trip Duration (hrs)</label>
            <input
              type="number"
              value={optimizationParams.maxTripDuration}
              onChange={(e) => handleParamChange('maxTripDuration', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-md"
              min="4"
              max="16"
            />
          </div>
        </div>
      </div>

      {/* SKU Optimization Metrics */}
      {skuEfficiencyMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-600">Total SKUs</h4>
            <p className="text-2xl font-bold text-blue-600">{skuEfficiencyMetrics.totalSKUs}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-600">Target Compliance</h4>
            <p className="text-2xl font-bold text-green-600">
              {skuEfficiencyMetrics.targetCompliance} / {consolidationResults.trip_groups.length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-600">Avg SKUs/Trip</h4>
            <p className="text-2xl font-bold text-purple-600">
              {skuEfficiencyMetrics.averageSKUPerTrip.toFixed(1)}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-600">Constraint Violations</h4>
            <p className="text-2xl font-bold text-red-600">
              {skuEfficiencyMetrics.constraintViolations.length}
            </p>
          </div>
        </div>
      )}

      {/* SKU Distribution Chart */}
      {skuEfficiencyMetrics && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4">SKU Distribution by Trip</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={skuEfficiencyMetrics.skuDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tripId" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="skuCount" fill="#3B82F6" name="SKU Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* SKU Efficiency Breakdown */}
      {skuEfficiencyMetrics && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4">Trip Efficiency Analysis</h3>
          <div className="space-y-4">
            {skuEfficiencyMetrics.skuDistribution.map((trip, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: getSKUComplianceColor(trip.skuCount) }}
                  ></div>
                  <div>
                    <p className="font-medium">{trip.tripId}</p>
                    <p className="text-sm text-gray-600">
                      {trip.skuCount} SKUs • {trip.efficiency.toFixed(1)}% efficiency
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {trip.weight.toFixed(1)} kg • {trip.volume.toFixed(1)} m³
                  </p>
                  <p className="text-xs text-gray-500">
                    {trip.skuCount >= optimizationParams.targetSkuMin && 
                     trip.skuCount <= optimizationParams.targetSkuMax ? 
                     'Within Target' : 'Outside Target'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Constraint Violations */}
      {skuEfficiencyMetrics && skuEfficiencyMetrics.constraintViolations.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-red-200">
          <h3 className="text-lg font-semibold mb-4 text-red-700">Constraint Violations</h3>
          <div className="space-y-3">
            {skuEfficiencyMetrics.constraintViolations.map((violation, index) => (
              <div key={index} className="p-3 bg-red-50 rounded-lg">
                <p className="font-medium text-red-800">Trip {index + 1} Violations:</p>
                <ul className="text-sm text-red-700 mt-1">
                  {violation.sku_count < optimizationParams.targetSkuMin && (
                    <li>• SKU count ({violation.sku_count}) below minimum ({optimizationParams.targetSkuMin})</li>
                  )}
                  {violation.sku_count > optimizationParams.targetSkuMax && (
                    <li>• SKU count ({violation.sku_count}) above maximum ({optimizationParams.targetSkuMax})</li>
                  )}
                  {violation.total_weight_kg > optimizationParams.maxTripWeight && (
                    <li>• Weight ({violation.total_weight_kg.toFixed(1)}kg) exceeds maximum ({optimizationParams.maxTripWeight}kg)</li>
                  )}
                  {violation.total_volume_m3 > optimizationParams.maxTripVolume && (
                    <li>• Volume ({violation.total_volume_m3.toFixed(1)}m³) exceeds maximum ({optimizationParams.maxTripVolume}m³)</li>
                  )}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SKUOptimizationDashboard;
