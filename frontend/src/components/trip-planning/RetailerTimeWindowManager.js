import React, { useState, useEffect } from 'react';
import { tripPlanningService } from '../../services/tripPlanningService';

const RetailerTimeWindowManager = ({ optimizedRoutes, onTimeWindowUpdate }) => {
  const [timeWindows, setTimeWindows] = useState({});
  const [conflicts, setConflicts] = useState([]);
  const [selectedRetailer, setSelectedRetailer] = useState(null);
  const [bulkEditMode, setBulkEditMode] = useState(false);

  useEffect(() => {
    if (optimizedRoutes && optimizedRoutes.length > 0) {
      initializeTimeWindows();
    }
  }, [optimizedRoutes]);

  const initializeTimeWindows = () => {
    const windows = {};
    optimizedRoutes.forEach(route => {
      route.delivery_sequence.forEach(delivery => {
        if (!windows[delivery.order_id]) {
          windows[delivery.order_id] = {
            order_id: delivery.order_id,
            retailer_id: delivery.retailer_id || `retailer-${delivery.order_id}`,
            retailer_name: delivery.retailer_name || `Retailer ${delivery.order_id}`,
            address: delivery.address,
            preferred_window: {
              start: '09:00',
              end: '17:00'
            },
            alternative_windows: [
              { start: '08:00', end: '12:00', priority: 2 },
              { start: '13:00', end: '18:00', priority: 3 }
            ],
            special_requirements: [],
            estimated_arrival: delivery.estimated_arrival || null,
            current_window: {
              start: '09:00',
              end: '17:00'
            }
          };
        }
      });
    });
    setTimeWindows(windows);
    checkTimeWindowConflicts(windows);
  };

  const checkTimeWindowConflicts = (windows) => {
    const conflictList = [];
    
    optimizedRoutes.forEach((route, routeIndex) => {
      for (let i = 0; i < route.delivery_sequence.length - 1; i++) {
        const current = route.delivery_sequence[i];
        const next = route.delivery_sequence[i + 1];
        
        const currentWindow = windows[current.order_id];
        const nextWindow = windows[next.order_id];
        
        if (currentWindow && nextWindow) {
          const currentEnd = new Date(`2024-01-01T${currentWindow.current_window.end}`);
          const nextStart = new Date(`2024-01-01T${nextWindow.current_window.start}`);
          
          // Check if there's enough travel time between deliveries
          const travelTimeMinutes = 30; // Assume 30 minutes travel time
          const requiredGap = new Date(currentEnd.getTime() + travelTimeMinutes * 60000);
          
          if (requiredGap > nextStart) {
            conflictList.push({
              type: 'timing_conflict',
              route: route.route_name,
              message: `Insufficient time between ${current.order_id} and ${next.order_id}`,
              severity: 'high',
              orders: [current.order_id, next.order_id],
              suggestedFix: 'Extend time window or reorder deliveries'
            });
          }
        }
      }
    });
    
    setConflicts(conflictList);
  };

  const updateTimeWindow = (orderId, windowType, field, value) => {
    const updatedWindows = {
      ...timeWindows,
      [orderId]: {
        ...timeWindows[orderId],
        [windowType]: {
          ...timeWindows[orderId][windowType],
          [field]: value
        }
      }
    };
    
    setTimeWindows(updatedWindows);
    checkTimeWindowConflicts(updatedWindows);
    onTimeWindowUpdate(updatedWindows);
  };

  const addSpecialRequirement = (orderId, requirement) => {
    const updatedWindows = {
      ...timeWindows,
      [orderId]: {
        ...timeWindows[orderId],
        special_requirements: [
          ...timeWindows[orderId].special_requirements,
          requirement
        ]
      }
    };
    
    setTimeWindows(updatedWindows);
  };

  const removeSpecialRequirement = (orderId, index) => {
    const updatedWindows = {
      ...timeWindows,
      [orderId]: {
        ...timeWindows[orderId],
        special_requirements: timeWindows[orderId].special_requirements.filter((_, i) => i !== index)
      }
    };
    
    setTimeWindows(updatedWindows);
  };

  const bulkUpdateTimeWindows = (newWindow) => {
    const updatedWindows = { ...timeWindows };
    Object.keys(updatedWindows).forEach(orderId => {
      updatedWindows[orderId].current_window = { ...newWindow };
    });
    
    setTimeWindows(updatedWindows);
    checkTimeWindowConflicts(updatedWindows);
    onTimeWindowUpdate(updatedWindows);
  };

  const resolveConflict = async (conflict) => {
    try {
      const conflictData = {
        conflict_type: conflict.type,
        affected_orders: conflict.orders,
        suggested_resolution: conflict.suggestedFix
      };
      
      const resolution = await tripPlanningService.resolveTimeConflict(conflictData);
      
      // Apply the resolution to time windows
      if (resolution.updated_windows) {
        resolution.updated_windows.forEach(window => {
          updateTimeWindow(window.order_id, 'current_window', 'start', window.start);
          updateTimeWindow(window.order_id, 'current_window', 'end', window.end);
        });
      }
    } catch (error) {
      console.error('Error resolving conflict:', error);
    }
  };

  const getConflictSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-50 border-red-200 text-red-700';
      case 'medium': return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'low': return 'bg-green-50 border-green-200 text-green-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const specialRequirementOptions = [
    'Loading dock required',
    'Appointment necessary',
    'Security clearance needed',
    'Refrigerated truck required',
    'Fork lift access needed',
    'Ground floor delivery only',
    'Business hours only',
    'Weekend delivery not allowed'
  ];

  return (
    <div className="space-y-6">
      {/* Time Window Conflicts */}
      {conflicts.length > 0 && (
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold mb-4 text-red-700">
            Time Window Conflicts ({conflicts.length})
          </h3>
          <div className="space-y-4">
            {conflicts.map((conflict, index) => (
              <div key={index} className={`p-4 rounded-lg border ${getConflictSeverityColor(conflict.severity)}`}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium">{conflict.route}</h4>
                    <p className="text-sm">{conflict.message}</p>
                    <p className="text-xs mt-1">Suggested: {conflict.suggestedFix}</p>
                  </div>
                  <button
                    onClick={() => resolveConflict(conflict)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                  >
                    Auto-Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bulk Edit Controls */}
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Time Window Management</h3>
          <button
            onClick={() => setBulkEditMode(!bulkEditMode)}
            className={`px-4 py-2 rounded-md ${
              bulkEditMode 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {bulkEditMode ? 'Exit Bulk Edit' : 'Bulk Edit Mode'}
          </button>
        </div>

        {bulkEditMode && (
          <div className="p-4 bg-blue-50 rounded-lg mb-4">
            <h4 className="font-medium mb-3">Apply to All Retailers</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Start Time</label>
                <input
                  type="time"
                  className="w-full px-3 py-2 border rounded-md"
                  onChange={(e) => {
                    const endTime = document.getElementById('bulk-end-time').value;
                    if (endTime) {
                      bulkUpdateTimeWindows({ start: e.target.value, end: endTime });
                    }
                  }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">End Time</label>
                <input
                  type="time"
                  id="bulk-end-time"
                  className="w-full px-3 py-2 border rounded-md"
                  onChange={(e) => {
                    const startTime = document.querySelector('input[type="time"]').value;
                    if (startTime) {
                      bulkUpdateTimeWindows({ start: startTime, end: e.target.value });
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Individual Retailer Time Windows */}
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Retailer Time Windows</h3>
        <div className="space-y-4">
          {Object.values(timeWindows).map(retailer => (
            <div key={retailer.order_id} className="p-4 border rounded-lg">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-medium">{retailer.retailer_name}</h4>
                  <p className="text-sm text-gray-600">Order: {retailer.order_id}</p>
                  <p className="text-xs text-gray-500">{retailer.address}</p>
                </div>
                <button
                  onClick={() => setSelectedRetailer(
                    selectedRetailer === retailer.order_id ? null : retailer.order_id
                  )}
                  className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-md hover:bg-gray-200"
                >
                  {selectedRetailer === retailer.order_id ? 'Collapse' : 'Expand'}
                </button>
              </div>

              {/* Current Time Window */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Current Start Time</label>
                  <input
                    type="time"
                    value={retailer.current_window.start}
                    onChange={(e) => updateTimeWindow(retailer.order_id, 'current_window', 'start', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Current End Time</label>
                  <input
                    type="time"
                    value={retailer.current_window.end}
                    onChange={(e) => updateTimeWindow(retailer.order_id, 'current_window', 'end', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>

              {/* Expanded Details */}
              {selectedRetailer === retailer.order_id && (
                <div className="space-y-4 pt-4 border-t">
                  {/* Preferred Time Window */}
                  <div>
                    <h5 className="font-medium mb-2">Preferred Time Window</h5>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Preferred Start</label>
                        <input
                          type="time"
                          value={retailer.preferred_window.start}
                          onChange={(e) => updateTimeWindow(retailer.order_id, 'preferred_window', 'start', e.target.value)}
                          className="w-full px-3 py-2 border rounded-md"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Preferred End</label>
                        <input
                          type="time"
                          value={retailer.preferred_window.end}
                          onChange={(e) => updateTimeWindow(retailer.order_id, 'preferred_window', 'end', e.target.value)}
                          className="w-full px-3 py-2 border rounded-md"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Alternative Windows */}
                  <div>
                    <h5 className="font-medium mb-2">Alternative Time Windows</h5>
                    {retailer.alternative_windows.map((window, index) => (
                      <div key={index} className="grid grid-cols-3 gap-4 mb-2">
                        <input
                          type="time"
                          value={window.start}
                          onChange={(e) => {
                            const updatedAlternatives = [...retailer.alternative_windows];
                            updatedAlternatives[index].start = e.target.value;
                            setTimeWindows({
                              ...timeWindows,
                              [retailer.order_id]: {
                                ...retailer,
                                alternative_windows: updatedAlternatives
                              }
                            });
                          }}
                          className="px-3 py-2 border rounded-md"
                        />
                        <input
                          type="time"
                          value={window.end}
                          onChange={(e) => {
                            const updatedAlternatives = [...retailer.alternative_windows];
                            updatedAlternatives[index].end = e.target.value;
                            setTimeWindows({
                              ...timeWindows,
                              [retailer.order_id]: {
                                ...retailer,
                                alternative_windows: updatedAlternatives
                              }
                            });
                          }}
                          className="px-3 py-2 border rounded-md"
                        />
                        <select
                          value={window.priority}
                          onChange={(e) => {
                            const updatedAlternatives = [...retailer.alternative_windows];
                            updatedAlternatives[index].priority = parseInt(e.target.value);
                            setTimeWindows({
                              ...timeWindows,
                              [retailer.order_id]: {
                                ...retailer,
                                alternative_windows: updatedAlternatives
                              }
                            });
                          }}
                          className="px-3 py-2 border rounded-md"
                        >
                          <option value={1}>High Priority</option>
                          <option value={2}>Medium Priority</option>
                          <option value={3}>Low Priority</option>
                        </select>
                      </div>
                    ))}
                  </div>

                  {/* Special Requirements */}
                  <div>
                    <h5 className="font-medium mb-2">Special Requirements</h5>
                    <div className="space-y-2">
                      {retailer.special_requirements.map((req, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <span className="text-sm">{req}</span>
                          <button
                            onClick={() => removeSpecialRequirement(retailer.order_id, index)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            addSpecialRequirement(retailer.order_id, e.target.value);
                            e.target.value = '';
                          }
                        }}
                        className="w-full px-3 py-2 border rounded-md"
                      >
                        <option value="">Add Special Requirement</option>
                        {specialRequirementOptions.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Estimated vs Actual */}
                  {retailer.estimated_arrival && (
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                      <span className="text-sm font-medium">Estimated Arrival:</span>
                      <span className="text-sm">
                        {new Date(retailer.estimated_arrival).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RetailerTimeWindowManager;
