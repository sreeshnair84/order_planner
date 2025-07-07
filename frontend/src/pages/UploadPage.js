import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { useMutation } from 'react-query';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { Upload, File, X } from 'lucide-react';
import Layout from '../components/common/Layout';
import { orderService } from '../services/orderService';

const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const navigate = useNavigate();
  const { register, handleSubmit } = useForm();

  const uploadMutation = useMutation(
    ({ file, metadata }) => orderService.uploadOrder(file, metadata),
    {
      onSuccess: (data) => {
        toast.success('Order uploaded successfully!');
        navigate('/tracking');
      },
      onError: (error) => {
        toast.error(error.detail || 'Upload failed. Please try again.');
      },
    }
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
      'text/plain': ['.txt', '.log'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
      }
    },
    onDropRejected: (rejectedFiles) => {
      const file = rejectedFiles[0];
      if (file.errors.some(e => e.code === 'file-too-large')) {
        toast.error('File is too large. Maximum size is 10MB.');
      } else if (file.errors.some(e => e.code === 'file-invalid-type')) {
        toast.error('Invalid file type. Please upload CSV, XML, or LOG files.');
      } else {
        toast.error('File upload failed. Please try again.');
      }
    },
  });

  const removeFile = () => {
    setSelectedFile(null);
  };

  const onSubmit = (data) => {
    if (!selectedFile) {
      toast.error('Please select a file to upload.');
      return;
    }

    uploadMutation.mutate({
      file: selectedFile,
      metadata: {
        priority: data.priority,
        special_instructions: data.special_instructions,
      },
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Upload Order</h1>
          <p className="mt-2 text-sm text-gray-600">
            Upload your order files (CSV, XML, or LOG format) to get started.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* File Upload */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Select Order File
            </h3>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                {isDragActive
                  ? 'Drop the file here...'
                  : 'Drag and drop your order file here, or click to select'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Supported formats: CSV, XML, LOG (Max 10MB)
              </p>
            </div>

            {selectedFile && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <File className="h-5 w-5 text-gray-600 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Order Metadata */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Order Details
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="form-label">Priority Level</label>
                <select
                  {...register('priority')}
                  className="form-input"
                  defaultValue="NORMAL"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              <div>
                <label className="form-label">Special Instructions</label>
                <textarea
                  {...register('special_instructions')}
                  rows={3}
                  className="form-input"
                  placeholder="Enter any special instructions or notes for this order..."
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="btn btn-secondary px-6 py-2"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || uploadMutation.isLoading}
              className="btn btn-primary px-6 py-2 disabled:opacity-50"
            >
              {uploadMutation.isLoading ? 'Uploading...' : 'Upload Order'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default UploadPage;
