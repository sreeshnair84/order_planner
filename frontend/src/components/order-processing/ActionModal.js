import React, { useState } from 'react';
import { X, Save, Send, AlertTriangle } from 'lucide-react';

const ActionModal = ({ action, orderId, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCorrectMissingFields = () => {
    const missingFields = action.data;
    
    return (
      <div className="space-y-4">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <h3 className="text-lg font-semibold text-yellow-800">Missing Fields Correction</h3>
          </div>
          <p className="text-yellow-700 mb-4">
            Please provide the missing information below to complete your order validation.
          </p>
        </div>

        <div className="space-y-4">
          {missingFields.map((field, index) => (
            <div key={index} className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                {field.replace(/[\[\]]/g, ' ').replace(/\./g, ' ► ')}
              </label>
              {field.includes('quantity') || field.includes('price') ? (
                <input
                  type="number"
                  step="0.01"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`Enter ${field.split('.').pop()}`}
                  value={formData[field] || ''}
                  onChange={(e) => setFormData({...formData, [field]: e.target.value})}
                />
              ) : field.includes('date') ? (
                <input
                  type="date"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={formData[field] || ''}
                  onChange={(e) => setFormData({...formData, [field]: e.target.value})}
                />
              ) : (
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`Enter ${field.split('.').pop()}`}
                  value={formData[field] || ''}
                  onChange={(e) => setFormData({...formData, [field]: e.target.value})}
                />
              )}
            </div>
          ))}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">What happens next?</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Your corrections will be saved to the order</li>
            <li>• The order will be automatically re-validated</li>
            <li>• If validation passes, processing will continue</li>
            <li>• You'll receive a confirmation email</li>
          </ul>
        </div>
      </div>
    );
  };

  const handleCorrectValidationErrors = () => {
    const validationErrors = action.data;
    
    return (
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <h3 className="text-lg font-semibold text-red-800">Validation Error Correction</h3>
          </div>
          <p className="text-red-700 mb-4">
            The following validation errors need to be corrected:
          </p>
        </div>

        <div className="space-y-4">
          {validationErrors.map((error, index) => {
            const fieldMatch = error.match(/^([^:]+):/);
            const fieldName = fieldMatch ? fieldMatch[1] : `error_${index}`;
            const errorDescription = error.replace(/^[^:]+:\s*/, '');
            
            return (
              <div key={index} className="border border-red-200 rounded-lg p-4">
                <div className="font-medium text-red-800 mb-2">{fieldName}</div>
                <div className="text-sm text-red-600 mb-3">{errorDescription}</div>
                
                {error.includes('quantity') && (
                  <input
                    type="number"
                    min="1"
                    step="1"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter valid quantity (minimum 1)"
                    value={formData[fieldName] || ''}
                    onChange={(e) => setFormData({...formData, [fieldName]: e.target.value})}
                  />
                )}
                
                {error.includes('price') && (
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter valid price (minimum 0)"
                    value={formData[fieldName] || ''}
                    onChange={(e) => setFormData({...formData, [fieldName]: e.target.value})}
                  />
                )}
                
                {error.includes('SKU') && (
                  <input
                    type="text"
                    pattern="[A-Z0-9\-_]{3,50}"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter valid SKU code (3-50 alphanumeric characters)"
                    value={formData[fieldName] || ''}
                    onChange={(e) => setFormData({...formData, [fieldName]: e.target.value.toUpperCase()})}
                  />
                )}
                
                {error.includes('date') && (
                  <input
                    type="date"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    value={formData[fieldName] || ''}
                    onChange={(e) => setFormData({...formData, [fieldName]: e.target.value})}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const handleViewEmail = () => {
    const email = action.data;
    
    return (
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">Email Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="font-medium">Subject:</span> {email.subject}</div>
            <div><span className="font-medium">Type:</span> {email.email_type}</div>
            <div><span className="font-medium">To:</span> {email.recipient}</div>
            <div><span className="font-medium">From:</span> {email.sender}</div>
            <div><span className="font-medium">Created:</span> {new Date(email.created_at).toLocaleString()}</div>
            <div><span className="font-medium">Status:</span> {email.sent_at ? 'Sent' : 'Draft'}</div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-800 mb-3">Email Content</h4>
          <div 
            className="prose max-w-none border border-gray-200 rounded p-4 max-h-96 overflow-y-auto"
            dangerouslySetInnerHTML={{ __html: email.body }}
          />
        </div>

        {!email.sent_at && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">
              This email is still in draft status. You can edit it or send it from the actions below.
            </p>
          </div>
        )}
      </div>
    );
  };

  const handleResendEmail = () => {
    const email = action.data;
    
    return (
      <div className="space-y-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-green-800 mb-2">Resend Email</h3>
          <p className="text-green-700">
            This will resend the email to the customer with the current content.
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Recipient Email
            </label>
            <input
              type="email"
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              value={formData.recipient || email.recipient}
              onChange={(e) => setFormData({...formData, recipient: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Message (Optional)
            </label>
            <textarea
              rows={4}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Add a personal message to be included with the email..."
              value={formData.additionalMessage || ''}
              onChange={(e) => setFormData({...formData, additionalMessage: e.target.value})}
            />
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">Email Preview</h4>
          <div className="text-sm text-blue-700">
            <div><strong>To:</strong> {formData.recipient || email.recipient}</div>
            <div><strong>Subject:</strong> {email.subject}</div>
            <div><strong>Type:</strong> {email.email_type}</div>
          </div>
        </div>
      </div>
    );
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      let endpoint = '';
      let payload = {};

      switch (action.type) {
        case 'correct_missing_fields':
          endpoint = `/api/orders/${orderId}/correct-missing-fields`;
          payload = { corrections: formData };
          break;
        case 'correct_validation_errors':
          endpoint = `/api/orders/${orderId}/correct-validation-errors`;
          payload = { corrections: formData };
          break;
        case 'resend_email':
          endpoint = `/api/orders/${orderId}/resend-email`;
          payload = { 
            email_id: action.data.id,
            recipient: formData.recipient,
            additional_message: formData.additionalMessage
          };
          break;
        default:
          throw new Error('Unknown action type');
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        onSuccess();
        onClose();
        alert('Action completed successfully!');
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Action failed');
      }
    } catch (error) {
      console.error('Error performing action:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderContent = () => {
    switch (action.type) {
      case 'correct_missing_fields':
        return handleCorrectMissingFields();
      case 'correct_validation_errors':
        return handleCorrectValidationErrors();
      case 'view_email':
        return handleViewEmail();
      case 'resend_email':
        return handleResendEmail();
      default:
        return <div>Unknown action type</div>;
    }
  };

  const getModalTitle = () => {
    switch (action.type) {
      case 'correct_missing_fields':
        return 'Correct Missing Fields';
      case 'correct_validation_errors':
        return 'Fix Validation Errors';
      case 'view_email':
        return 'View Email';
      case 'resend_email':
        return 'Resend Email';
      default:
        return 'Action';
    }
  };

  const showSubmitButton = () => {
    return action.type !== 'view_email';
  };

  const getSubmitButtonText = () => {
    switch (action.type) {
      case 'correct_missing_fields':
        return 'Save Corrections & Re-validate';
      case 'correct_validation_errors':
        return 'Apply Fixes & Re-validate';
      case 'resend_email':
        return 'Send Email';
      default:
        return 'Submit';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">{getModalTitle()}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {renderContent()}
        </div>

        <div className="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          {showSubmitButton() && (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  {action.type === 'resend_email' ? <Send className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                  <span>{getSubmitButtonText()}</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActionModal;
