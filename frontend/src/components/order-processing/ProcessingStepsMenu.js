import React, { useState, useEffect } from 'react';
import { FiPlay, FiPause, FiRefreshCw, FiEdit, FiCheckCircle, FiAlertCircle, FiClock, FiMail, FiFileText, FiDatabase, FiSettings } from 'react-icons/fi';

const ProcessingStepsMenu = ({ orderId, onActionSelect }) => {
  const [processingSteps, setProcessingSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeStep, setActiveStep] = useState(null);

  useEffect(() => {
    loadProcessingSteps();
  }, [orderId]);

  const loadProcessingSteps = async () => {
    try {
      const response = await fetch(`/api/orders/${orderId}/processing-steps`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setProcessingSteps(data.data.steps || []);
    } catch (error) {
      console.error('Error loading processing steps:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStepAction = async (stepId, action) => {
    try {
      const response = await fetch(`/api/orders/${orderId}/processing-steps/${stepId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ action }),
      });
      
      if (response.ok) {
        loadProcessingSteps(); // Refresh steps
        if (onActionSelect) {
          onActionSelect(action, stepId);
        }
      }
    } catch (error) {
      console.error('Error executing step action:', error);
    }
  };

  const getStepIcon = (stepType, status) => {
    const iconProps = { className: "w-5 h-5" };
    
    switch (stepType) {
      case 'file_parsing':
        return <FiFileText {...iconProps} />;
      case 'validation':
        return status === 'completed' ? <FiCheckCircle {...iconProps} /> : <FiAlertCircle {...iconProps} />;
      case 'email_generation':
        return <FiMail {...iconProps} />;
      case 'sku_processing':
        return <FiDatabase {...iconProps} />;
      default:
        return <FiSettings {...iconProps} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'in_progress':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'skipped':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAvailableActions = (step) => {
    const actions = [];
    
    if (step.status === 'failed') {
      actions.push({ id: 'retry', label: 'Retry', icon: FiRefreshCw, color: 'blue' });
    }
    
    if (step.status === 'pending') {
      actions.push({ id: 'start', label: 'Start', icon: FiPlay, color: 'green' });
    }
    
    if (step.status === 'in_progress') {
      actions.push({ id: 'pause', label: 'Pause', icon: FiPause, color: 'orange' });
    }
    
    if (step.editable) {
      actions.push({ id: 'edit', label: 'Edit', icon: FiEdit, color: 'gray' });
    }
    
    if (step.can_skip) {
      actions.push({ id: 'skip', label: 'Skip', icon: FiClock, color: 'gray' });
    }
    
    return actions;
  };

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Processing Steps</h3>
        <button
          onClick={loadProcessingSteps}
          className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
        >
          <FiRefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        {processingSteps.map((step, index) => (
          <div
            key={step.id}
            className={`border rounded-lg p-4 transition-all duration-200 ${
              activeStep === step.id ? 'ring-2 ring-blue-500' : ''
            } ${getStatusColor(step.status)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getStepIcon(step.type, step.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium truncate">
                      {step.name}
                    </h4>
                    <span className="text-xs px-2 py-1 rounded-full bg-white bg-opacity-70">
                      Step {index + 1}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {step.description}
                  </p>
                  {step.last_execution && (
                    <p className="text-xs text-gray-500 mt-1">
                      Last executed: {new Date(step.last_execution).toLocaleString()}
                    </p>
                  )}
                  {step.error_message && (
                    <p className="text-xs text-red-600 mt-1 bg-red-50 p-2 rounded">
                      Error: {step.error_message}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                {getAvailableActions(step).map((action) => {
                  const IconComponent = action.icon;
                  return (
                    <button
                      key={action.id}
                      onClick={() => handleStepAction(step.id, action.id)}
                      className={`p-2 rounded-lg border text-xs font-medium transition-colors
                        ${action.color === 'blue' ? 'border-blue-200 text-blue-600 hover:bg-blue-50' :
                          action.color === 'green' ? 'border-green-200 text-green-600 hover:bg-green-50' :
                          action.color === 'orange' ? 'border-orange-200 text-orange-600 hover:bg-orange-50' :
                          'border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                      title={action.label}
                    >
                      <IconComponent className="w-4 h-4" />
                    </button>
                  );
                })}
              </div>
            </div>

            {step.checkpoints && step.checkpoints.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200 border-opacity-50">
                <h5 className="text-xs font-medium text-gray-700 mb-2">Checkpoints:</h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {step.checkpoints.map((checkpoint) => (
                    <div
                      key={checkpoint.id}
                      className={`text-xs p-2 rounded border ${
                        checkpoint.status === 'passed' ? 'bg-green-50 border-green-200 text-green-700' :
                        checkpoint.status === 'failed' ? 'bg-red-50 border-red-200 text-red-700' :
                        'bg-gray-50 border-gray-200 text-gray-700'
                      }`}
                    >
                      <div className="font-medium">{checkpoint.name}</div>
                      {checkpoint.value && (
                        <div className="text-gray-600">{checkpoint.value}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step.sub_steps && step.sub_steps.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200 border-opacity-50">
                <div className="space-y-2">
                  {step.sub_steps.map((subStep) => (
                    <div key={subStep.id} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{subStep.name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(subStep.status)}`}>
                        {subStep.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {processingSteps.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FiSettings className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No processing steps available for this order</p>
        </div>
      )}
    </div>
  );
};

export default ProcessingStepsMenu;
