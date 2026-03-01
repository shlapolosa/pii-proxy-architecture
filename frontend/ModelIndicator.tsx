// ModelIndicator.tsx
// Current model indicator component with fallback indicators

import React from 'react';

interface ModelIndicatorProps {
  currentModel: string;
  isFallbackActive?: boolean;
  fallbackReason?: string;
  modelNameMapping?: Record<string, string>;
}

const ModelIndicator: React.FC<ModelIndicatorProps> = ({
  currentModel,
  isFallbackActive = false,
  fallbackReason = '',
  modelNameMapping = {}
}) => {
  const getModelDisplayName = (model: string) => {
    const defaultMapping: Record<string, string> = {
      'claude-3-opus': 'Claude 3 Opus',
      'claude-3-sonnet': 'Claude 3 Sonnet',
      'gpt-4': 'GPT-4',
      'llama3': 'Llama 3',
      'mistral': 'Mistral'
    };

    const mapping = { ...defaultMapping, ...modelNameMapping };
    return mapping[model] || model;
  };

  const getModelType = (model: string) => {
    const cloudModels = ['claude-3-opus', 'claude-3-sonnet', 'gpt-4'];
    return cloudModels.includes(model) ? 'cloud' : 'local';
  };

  const modelType = getModelType(currentModel);
  const displayName = getModelDisplayName(currentModel);

  return (
    <div className="model-indicator">
      <div className="model-info">
        <span className={`model-type ${modelType}`}>
          {modelType === 'cloud' ? '☁️' : '💻'} {modelType.charAt(0).toUpperCase() + modelType.slice(1)}
        </span>
        <span className="model-name">{displayName}</span>
        {isFallbackActive && (
          <span className="fallback-indicator" title={fallbackReason}>
            ⚠️ Fallback Active
          </span>
        )}
      </div>

      <div className="model-status">
        {isFallbackActive ? (
          <span className="status-fallback">Security Fallback Mode</span>
        ) : (
          <span className="status-normal">Normal Operation</span>
        )}
      </div>

      <style jsx>{`
        .model-indicator {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
          padding: 0.75rem 1rem;
          background-color: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 6px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .model-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-weight: 500;
        }

        .model-type {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.25rem 0.5rem;
          border-radius: 12px;
          font-size: 0.8rem;
          font-weight: 600;
        }

        .model-type.cloud {
          background-color: #e3f2fd;
          color: #1976d2;
        }

        .model-type.local {
          background-color: #e8f5e9;
          color: #388e3c;
        }

        .model-name {
          font-size: 1rem;
          color: #212529;
        }

        .fallback-indicator {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.25rem 0.5rem;
          background-color: #fff8e1;
          color: #ff8f00;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
          cursor: help;
        }

        .model-status {
          font-size: 0.8rem;
          color: #6c757d;
        }

        .status-fallback {
          color: #ff8f00;
          font-weight: 500;
        }

        .status-normal {
          color: #28a745;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};

export default ModelIndicator;