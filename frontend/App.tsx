// App.tsx
// Main application component demonstrating the PII-aware model routing

import React, { useState, useEffect } from 'react';
import ApiClient from './api_client';
import ModelSelector from './ModelSelector';
import NotificationBanner from './NotificationBanner';
import ModelIndicator from './ModelIndicator';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const App: React.FC = () => {
  // Initialize API client
  const [apiClient] = useState(() => new ApiClient('https://api.pii-proxy.yourdomain.com', 'your-api-key'));

  // State management
  const [currentModel, setCurrentModel] = useState('claude-3-opus');
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isModelSwitched, setIsModelSwitched] = useState(false);
  const [switchedFromModel, setSwitchedFromModel] = useState('');

  // Initialize available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const models = await apiClient.getAvailableModels();
        setAvailableModels(models);
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };

    fetchModels();
  }, [apiClient]);

  // Handle model change
  const handleModelChange = (model: string) => {
    setCurrentModel(model);
    apiClient.setCurrentModel(model);
  };

  // Send message to API
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Store original model for potential switch notification
      const originalModel = currentModel;

      // Send request to backend
      const { response, notifications: newNotifications } = await apiClient.sendRequest(
        [...messages, userMessage].map(msg => ({ role: msg.role, content: msg.content })),
        currentModel
      );

      // Add notifications
      if (newNotifications.length > 0) {
        setNotifications(prev => [...newNotifications, ...prev]);
      }

      // Check if model was switched
      if (response?.usage?.model_switched) {
        setIsModelSwitched(true);
        setSwitchedFromModel(originalModel);

        // Auto-reset switch indicator after 5 seconds
        setTimeout(() => {
          setIsModelSwitched(false);
          setSwitchedFromModel('');
        }, 5000);
      }

      // Add assistant response
      if (response?.choices?.[0]?.message) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.choices[0].message.content,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error notification
      const errorNotification = {
        id: Date.now().toString(),
        type: 'error_occurred',
        level: 'error',
        message: `Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {}
      };

      setNotifications(prev => [errorNotification, ...prev]);
    } finally {
      setIsLoading(false);
    }
  };

  // Dismiss notification
  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  // Dismiss all notifications
  const dismissAllNotifications = () => {
    setNotifications([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>PII-Aware Model Router</h1>
        <p>Secure LLM access with automatic PII detection and model routing</p>
      </header>

      <main className="app-main">
        <div className="model-controls">
          <ModelSelector
            currentModel={currentModel}
            onModelChange={handleModelChange}
            availableModels={availableModels}
            isModelSwitched={isModelSwitched}
            switchedFromModel={switchedFromModel}
          />

          <ModelIndicator
            currentModel={currentModel}
            isFallbackActive={isModelSwitched}
            fallbackReason={isModelSwitched ? `Automatically switched from ${switchedFromModel} due to PII detection` : ''}
          />
        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-header">
                  <strong>{message.role === 'user' ? 'You' : 'Assistant'}</strong>
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message assistant">
                <div className="message-header">
                  <strong>Assistant</strong>
                </div>
                <div className="message-content">
                  <div className="loading-dots">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="chat-input">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message here..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </main>

      <NotificationBanner
        notifications={notifications.map((notification, index) => ({
          ...notification,
          id: notification.id || `notification-${index}`
        }))}
        onDismiss={dismissNotification}
        onDismissAll={dismissAllNotifications}
      />

      <style jsx>{`
        .app {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .app-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .app-header h1 {
          color: #333;
          margin-bottom: 0.5rem;
        }

        .app-header p {
          color: #666;
          margin-top: 0;
        }

        .app-main {
          display: grid;
          grid-template-columns: 300px 1fr;
          gap: 2rem;
        }

        .model-controls {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .chat-container {
          display: flex;
          flex-direction: column;
          height: 600px;
          border: 1px solid #ddd;
          border-radius: 8px;
          overflow: hidden;
        }

        .chat-messages {
          flex-grow: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .message {
          padding: 1rem;
          border-radius: 8px;
          max-width: 80%;
        }

        .message.user {
          align-self: flex-end;
          background-color: #e3f2fd;
        }

        .message.assistant {
          align-self: flex-start;
          background-color: #f5f5f5;
        }

        .message-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
          color: #666;
        }

        .message-content {
          line-height: 1.5;
        }

        .loading-dots {
          display: flex;
          gap: 0.25rem;
        }

        .loading-dots span {
          animation: loading 1.4s infinite ease-in-out;
        }

        .loading-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }

        .loading-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes loading {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }

        .chat-input {
          display: flex;
          border-top: 1px solid #ddd;
          padding: 1rem;
          gap: 1rem;
        }

        .chat-input textarea {
          flex-grow: 1;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          resize: none;
          min-height: 60px;
          font-family: inherit;
        }

        .chat-input button {
          padding: 0.75rem 1.5rem;
          background-color: #1976d2;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }

        .chat-input button:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .chat-input button:hover:not(:disabled) {
          background-color: #1565c0;
        }

        @media (max-width: 768px) {
          .app-main {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default App;