// ModelSelector.tsx
// Model selector component with hybrid approach

import React, { useState, useEffect } from 'react';

interface ModelSelectorProps {
  currentModel: string;
  onModelChange: (model: string) => void;
  availableModels: string[];
  isModelSwitched?: boolean;
  switchedFromModel?: string;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  currentModel,
  onModelChange,
  availableModels,
  isModelSwitched = false,
  switchedFromModel
}) => {
  const [selectedModel, setSelectedModel] = useState(currentModel);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    setSelectedModel(currentModel);
  }, [currentModel]);

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newModel = e.target.value;
    setSelectedModel(newModel);
    onModelChange(newModel);
  };

  const getModelLabel = (model: string) => {
    const labels: Record<string, string> = {
      'claude-3-opus': 'Claude 3 Opus (Cloud)',
      'claude-3-sonnet': 'Claude 3 Sonnet (Cloud)',
      'gpt-4': 'GPT-4 (Cloud)',
      'llama3': 'Llama 3 (Local)',
      'mistral': 'Mistral (Local)'
    };
    return labels[model] || model;
  };

  const getModelType = (model: string) => {
    const cloudModels = ['claude-3-opus', 'claude-3-sonnet', 'gpt-4'];
    return cloudModels.includes(model) ? 'cloud' : 'local';
  };

  return (
    <div className="model-selector">
      <label htmlFor="model-select" className="model-selector-label">
        Selected Model:
      </label>
      <div className="model-selector-container">
        <select
          id="model-select"
          value={selectedModel}
          onChange={handleModelChange}
          className={`model-select ${getModelType(selectedModel)} ${isModelSwitched ? 'switched' : ''}`}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          {availableModels.map((model) => (
            <option key={model} value={model}>
              {getModelLabel(model)}
            </option>
          ))}
        </select>

        {isModelSwitched && (
          <div className="model-switch-indicator" title={`Automatically switched from ${switchedFromModel}`}>
            ↻
          </div>
        )}
      </div>

      {showTooltip && (
        <div className="model-tooltip">
          <strong>{getModelLabel(selectedModel)}</strong>
          <br />
          Type: {getModelType(selectedModel) === 'cloud' ? '☁️ Cloud Model' : '💻 Local Model'}
          {isModelSwitched && (
            <>
              <br />
              <span className="warning-text">⚠️ Switched from {switchedFromModel} due to PII detection</span>
            </>
          )}
        </div>
      )}

      <style jsx>{`
        .model-selector {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .model-selector-label {
          font-weight: bold;
          color: #333;
        }

        .model-selector-container {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .model-select {
          padding: 0.5rem;
          border: 2px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
          background-color: white;
        }

        .model-select.cloud {
          border-color: #4285f4;
        }

        .model-select.local {
          border-color: #34a853;
        }

        .model-select.switched {
          border-color: #f9ab00;
          animation: pulse 1s infinite;
        }

        .model-switch-indicator {
          font-size: 1.2rem;
          color: #f9ab00;
          cursor: help;
        }

        .model-tooltip {
          position: absolute;
          background-color: #333;
          color: white;
          padding: 0.5rem;
          border-radius: 4px;
          font-size: 0.9rem;
          z-index: 1000;
          width: 250px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        .warning-text {
          color: #f9ab00;
        }

        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(249, 171, 0, 0.4); }
          70% { box-shadow: 0 0 0 10px rgba(249, 171, 0, 0); }
          100% { box-shadow: 0 0 0 0 rgba(249, 171, 0, 0); }
        }
      `}</style>
    </div>
  );
};

export default ModelSelector;