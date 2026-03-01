// api_client.ts
// API client for communicating with backend proxy

interface PiiDetails {
  has_pii: boolean;
  risk_score?: number;
  entities?: Record<string, number>;
  original_model?: string;
  selected_model?: string;
  model_switched?: boolean;
}

interface Notification {
  type: 'pii_detected' | 'model_switched' | 'request_processed' | 'error_occurred';
  level: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  details: any;
}

interface ApiResponse {
  id: string;
  choices: Array<{
    message: {
      role: string;
      content: string;
    };
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    pii_detected?: boolean;
    pii_risk_score?: number;
    model_switched?: boolean;
  };
  notifications?: Notification[];
}

class ApiClient {
  private baseUrl: string;
  private apiKey: string;
  private currentModel: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.currentModel = 'claude-3-opus'; // Default model
  }

  /**
   * Send a request to the backend proxy
   */
  async sendRequest(
    messages: Array<{role: string; content: string}>,
    model?: string
  ): Promise<{response: ApiResponse | null; notifications: Notification[]}> {
    const selectedModel = model || this.currentModel;

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: messages,
        }),
      });

      const data: ApiResponse = await response.json();

      // Extract notifications from response
      const notifications: Notification[] = data.notifications || [];

      // Add notification if model was switched due to PII
      if (data.usage?.model_switched) {
        notifications.push({
          type: 'model_switched',
          level: 'info',
          message: `Model automatically switched from ${selectedModel} to ${data.usage.model_switched ? 'local model' : selectedModel}`,
          timestamp: new Date().toISOString(),
          details: {
            original_model: selectedModel,
            selected_model: data.usage.model_switched ? 'local model' : selectedModel,
            reason: 'PII detected in request'
          }
        });
      }

      // Add notification if PII was detected
      if (data.usage?.pii_detected) {
        notifications.push({
          type: 'pii_detected',
          level: 'warning',
          message: `PII detected in your request (risk score: ${data.usage.pii_risk_score?.toFixed(2) || 'unknown'}). For your protection, we've automatically switched to a local model.`,
          timestamp: new Date().toISOString(),
          details: {
            risk_score: data.usage.pii_risk_score,
            model_switched: data.usage.model_switched
          }
        });
      }

      return { response: data, notifications };
    } catch (error) {
      console.error('API request failed:', error);

      // Create error notification
      const errorNotification: Notification = {
        type: 'error_occurred',
        level: 'error',
        message: `Failed to send request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      };

      return { response: null, notifications: [errorNotification] };
    }
  }

  /**
   * Set the current model preference
   */
  setCurrentModel(model: string): void {
    this.currentModel = model;
  }

  /**
   * Get the current model preference
   */
  getCurrentModel(): string {
    return this.currentModel;
  }

  /**
   * Get available models
   */
  async getAvailableModels(): Promise<string[]> {
    // In a real implementation, this would fetch from the backend
    return [
      'claude-3-opus',
      'claude-3-sonnet',
      'gpt-4',
      'llama3',
      'mistral'
    ];
  }
}

export default ApiClient;
export type { PiiDetails, Notification, ApiResponse };