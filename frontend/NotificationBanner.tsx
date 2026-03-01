// NotificationBanner.tsx
// Notification banner component for PII and model switching alerts

import React, { useState, useEffect } from 'react';

interface Notification {
  id: string;
  type: 'pii_detected' | 'model_switched' | 'request_processed' | 'error_occurred';
  level: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  details: any;
}

interface NotificationBannerProps {
  notifications: Notification[];
  onDismiss?: (id: string) => void;
  onDismissAll?: () => void;
}

const NotificationBanner: React.FC<NotificationBannerProps> = ({
  notifications,
  onDismiss,
  onDismissAll
}) => {
  const [visibleNotifications, setVisibleNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    setVisibleNotifications(notifications);
  }, [notifications]);

  const handleDismiss = (id: string) => {
    setVisibleNotifications(prev => prev.filter(notification => notification.id !== id));
    if (onDismiss) onDismiss(id);
  };

  const handleDismissAll = () => {
    setVisibleNotifications([]);
    if (onDismissAll) onDismissAll();
  };

  const getNotificationStyle = (level: string) => {
    switch (level) {
      case 'error':
        return {
          backgroundColor: '#ffebee',
          borderLeft: '4px solid #f44336',
          color: '#c62828'
        };
      case 'warning':
        return {
          backgroundColor: '#fff8e1',
          borderLeft: '4px solid #ffc107',
          color: '#ff8f00'
        };
      case 'info':
        return {
          backgroundColor: '#e3f2fd',
          borderLeft: '4px solid #2196f3',
          color: '#1565c0'
        };
      default:
        return {
          backgroundColor: '#f5f5f5',
          borderLeft: '4px solid #9e9e9e',
          color: '#616161'
        };
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'pii_detected':
        return '🔒';
      case 'model_switched':
        return '🔄';
      case 'error_occurred':
        return '❌';
      case 'request_processed':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <div className="notification-banner-container">
      <div className="notification-header">
        <h3>Notifications ({visibleNotifications.length})</h3>
        <button onClick={handleDismissAll} className="dismiss-all-button">
          Dismiss All
        </button>
      </div>

      <div className="notifications-list">
        {visibleNotifications.map((notification) => (
          <div
            key={notification.id}
            className={`notification-item ${notification.level}`}
            style={getNotificationStyle(notification.level)}
          >
            <div className="notification-content">
              <span className="notification-icon">{getIcon(notification.type)}</span>
              <div className="notification-message">
                <p>{notification.message}</p>
                {notification.details && (
                  <small>
                    {JSON.stringify(notification.details)}
                  </small>
                )}
              </div>
              <button
                onClick={() => handleDismiss(notification.id)}
                className="dismiss-button"
                aria-label="Dismiss notification"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .notification-banner-container {
          position: fixed;
          top: 20px;
          right: 20px;
          max-width: 400px;
          z-index: 10000;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .notification-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .notification-header h3 {
          margin: 0;
          color: #333;
          font-size: 1rem;
        }

        .dismiss-all-button {
          background: none;
          border: 1px solid #ccc;
          border-radius: 4px;
          padding: 0.25rem 0.5rem;
          font-size: 0.8rem;
          cursor: pointer;
          color: #666;
        }

        .dismiss-all-button:hover {
          background-color: #f5f5f5;
        }

        .notifications-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .notification-item {
          border-radius: 4px;
          padding: 1rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .notification-item:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .notification-content {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
        }

        .notification-icon {
          font-size: 1.2rem;
          flex-shrink: 0;
        }

        .notification-message {
          flex-grow: 1;
        }

        .notification-message p {
          margin: 0 0 0.25rem 0;
          font-size: 0.9rem;
          line-height: 1.4;
        }

        .notification-message small {
          color: inherit;
          opacity: 0.8;
          font-size: 0.75rem;
        }

        .dismiss-button {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          padding: 0;
          margin: 0;
          line-height: 1;
          color: inherit;
          opacity: 0.7;
          flex-shrink: 0;
        }

        .dismiss-button:hover {
          opacity: 1;
        }

        @media (max-width: 768px) {
          .notification-banner-container {
            max-width: calc(100vw - 40px);
          }
        }
      `}</style>
    </div>
  );
};

export default NotificationBanner;