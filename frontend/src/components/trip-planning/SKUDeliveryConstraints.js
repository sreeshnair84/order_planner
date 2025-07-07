import React, { useState, useEffect } from 'react';

const SKUDeliveryConstraints = ({ consolidationResults, onConstraintsUpdate }) => {
  const [constraints, setConstraints] = useState({
    temperature: {
      frozen: { min: -18, max: -15, color: '#3B82F6' },
      refrigerated: { min: 2, max: 8, color: '#10B981' },
      ambient: { min: 15, max: 25, color: '#F59E0B' }
    },
    fragility: {
      high: { handling: 'careful', packaging: 'extra', color: '#EF4444' },
      medium: { handling: 'standard', packaging: 'standard', color: '#F59E0B' },
      low: { handling: 'normal', packaging: 'basic', color: '#10B981' }
    },
    timeWindows: {
      morning: { start: '08:00', end: '12:00', color: '#8B5CF6' },
      afternoon: { start: '12:00', end: '17:00', color: '#3B82F6' },
      evening: { start: '17:00', end: '20:00', color: '#F59E0B' }
    }
  });

  const [skuConstraintAnalysis, setSkuConstraintAnalysis] = useState(null);
  const [constraintViolations, setConstraintViolations] = useState([]);

  useEffect(() => {
    if (consolidationResults) {
      analyzeSKUConstraints();
    }
  }, [consolidationResults, constraints]);

  const analyzeSKUConstraints = () => {
    if (!consolidationResults || !consolidationResults.trip_groups) return;

    const analysis = {
      temperatureDistribution: {},
      fragilityDistribution: {},
      timeWindowDistribution: {},
      compatibilityIssues: []
    };

    const violations = [];

    consolidationResults.trip_groups.forEach((group, groupIndex) => {
      if (group.sku_details) {
        // Analyze temperature requirements
        const tempRequirements = group.sku_details.map(sku => sku.temperature_requirement).filter(Boolean);
        const uniqueTemps = [...new Set(tempRequirements)];
        
        if (uniqueTemps.length > 1) {
          violations.push({
            tripId: `Trip ${groupIndex + 1}`,
            type: 'temperature_conflict',
            message: `Multiple temperature requirements: ${uniqueTemps.join(', ')}`,
            severity: 'high',
            skus: group.sku_details.filter(sku => sku.temperature_requirement)
          });
        }

        // Analyze fragility
        const fragileItems = group.sku_details.filter(sku => sku.fragile);
        const nonFragileItems = group.sku_details.filter(sku => !sku.fragile);
        
        if (fragileItems.length > 0 && nonFragileItems.length > 0) {
          violations.push({
            tripId: `Trip ${groupIndex + 1}`,
            type: 'fragility_conflict',
            message: `Fragile and non-fragile items mixed`,
            severity: 'medium',
            skus: fragileItems
          });
        }

        // Update distributions
        tempRequirements.forEach(temp => {
          analysis.temperatureDistribution[temp] = (analysis.temperatureDistribution[temp] || 0) + 1;
        });

        analysis.fragilityDistribution[fragileItems.length > 0 ? 'fragile' : 'normal'] = 
          (analysis.fragilityDistribution[fragileItems.length > 0 ? 'fragile' : 'normal'] || 0) + 1;
      }
    });

    setSkuConstraintAnalysis(analysis);
    setConstraintViolations(violations);
  };

  const handleConstraintUpdate = (category, subcategory, field, value) => {
    const updatedConstraints = {
      ...constraints,
      [category]: {
        ...constraints[category],
        [subcategory]: {
          ...constraints[category][subcategory],
          [field]: value
        }
      }
    };
    
    setConstraints(updatedConstraints);
    onConstraintsUpdate(updatedConstraints);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Constraint Violations */}
      {constraintViolations.length > 0 && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4 text-red-700">
            SKU Delivery Constraint Violations
          </h3>
          <div className="space-y-4">
            {constraintViolations.map((violation, index) => (
              <div key={index} className={`p-4 rounded-lg border ${getSeverityColor(violation.severity)}`}>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">{violation.tripId}</h4>
                  <span className="text-xs px-2 py-1 rounded-full bg-current bg-opacity-20">
                    {violation.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm mb-2">{violation.message}</p>
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium">Affected SKUs ({violation.skus.length})</summary>
                  <div className="mt-2 space-y-1">
                    {violation.skus.map((sku, skuIndex) => (
                      <div key={skuIndex} className="pl-4 border-l-2 border-current border-opacity-30">
                        <p className="font-medium">{sku.product_name}</p>
                        <p className="text-xs">SKU: {sku.sku_code}</p>
                        {sku.temperature_requirement && (
                          <p className="text-xs">Temp: {sku.temperature_requirement}</p>
                        )}
                        {sku.fragile && (
                          <p className="text-xs">⚠️ Fragile</p>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Temperature Constraint Settings */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Temperature Constraints</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(constraints.temperature).map(([category, settings]) => (
            <div key={category} className="p-4 border rounded-lg">
              <h4 className="font-medium mb-3 capitalize">{category}</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Min Temperature (°C)</label>
                  <input
                    type="number"
                    value={settings.min}
                    onChange={(e) => handleConstraintUpdate('temperature', category, 'min', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Temperature (°C)</label>
                  <input
                    type="number"
                    value={settings.max}
                    onChange={(e) => handleConstraintUpdate('temperature', category, 'max', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Color Code</label>
                  <input
                    type="color"
                    value={settings.color}
                    onChange={(e) => handleConstraintUpdate('temperature', category, 'color', e.target.value)}
                    className="w-full h-10 border rounded-md"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fragility Constraint Settings */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Fragility Constraints</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(constraints.fragility).map(([level, settings]) => (
            <div key={level} className="p-4 border rounded-lg">
              <h4 className="font-medium mb-3 capitalize">{level} Fragility</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Handling Requirement</label>
                  <select
                    value={settings.handling}
                    onChange={(e) => handleConstraintUpdate('fragility', level, 'handling', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="normal">Normal</option>
                    <option value="standard">Standard Care</option>
                    <option value="careful">Careful Handling</option>
                    <option value="special">Special Handling</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Packaging Level</label>
                  <select
                    value={settings.packaging}
                    onChange={(e) => handleConstraintUpdate('fragility', level, 'packaging', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="basic">Basic</option>
                    <option value="standard">Standard</option>
                    <option value="extra">Extra Protection</option>
                    <option value="premium">Premium Protection</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Color Code</label>
                  <input
                    type="color"
                    value={settings.color}
                    onChange={(e) => handleConstraintUpdate('fragility', level, 'color', e.target.value)}
                    className="w-full h-10 border rounded-md"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Time Window Constraints */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Delivery Time Windows</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(constraints.timeWindows).map(([period, settings]) => (
            <div key={period} className="p-4 border rounded-lg">
              <h4 className="font-medium mb-3 capitalize">{period}</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Time</label>
                  <input
                    type="time"
                    value={settings.start}
                    onChange={(e) => handleConstraintUpdate('timeWindows', period, 'start', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Time</label>
                  <input
                    type="time"
                    value={settings.end}
                    onChange={(e) => handleConstraintUpdate('timeWindows', period, 'end', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Color Code</label>
                  <input
                    type="color"
                    value={settings.color}
                    onChange={(e) => handleConstraintUpdate('timeWindows', period, 'color', e.target.value)}
                    className="w-full h-10 border rounded-md"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Constraint Analysis Summary */}
      {skuConstraintAnalysis && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4">Constraint Analysis Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Temperature Distribution */}
            <div>
              <h4 className="font-medium mb-3">Temperature Requirements</h4>
              <div className="space-y-2">
                {Object.entries(skuConstraintAnalysis.temperatureDistribution).map(([temp, count]) => (
                  <div key={temp} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm capitalize">{temp || 'Ambient'}</span>
                    <span className="text-sm font-medium">{count} SKUs</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Fragility Distribution */}
            <div>
              <h4 className="font-medium mb-3">Fragility Distribution</h4>
              <div className="space-y-2">
                {Object.entries(skuConstraintAnalysis.fragilityDistribution).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm capitalize">{type}</span>
                    <span className="text-sm font-medium">{count} Trips</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Compatibility Issues */}
            <div>
              <h4 className="font-medium mb-3">Compatibility Issues</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-red-50 rounded">
                  <span className="text-sm">Temperature Conflicts</span>
                  <span className="text-sm font-medium text-red-600">
                    {constraintViolations.filter(v => v.type === 'temperature_conflict').length}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-yellow-50 rounded">
                  <span className="text-sm">Fragility Conflicts</span>
                  <span className="text-sm font-medium text-yellow-600">
                    {constraintViolations.filter(v => v.type === 'fragility_conflict').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SKUDeliveryConstraints;
