// Fix: Cast import.meta to any to resolve TypeScript error about missing env property
const BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL as string) || 'http://127.0.0.1:8000';

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

export const request = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const url = `${BASE_URL}${path}`;
  
  const headers = {
    ...options.headers,
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = `Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch (e) {
        // Fallback if response is not JSON
      }
      throw new Error(errorMessage);
    }

    // Handle non-JSON responses (like plain markdown, though backend currently sends JSON)
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json() as Promise<T>;
    }
    return response.text() as unknown as Promise<T>;

  } catch (error: any) {
    console.error('API Request Failed:', error);
    throw error;
  }
};