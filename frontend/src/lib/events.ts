// Simple event emitter for Toast notifications
type EventCallback<T = unknown> = (data: T) => void;

interface Events {
  [key: string]: EventCallback[];
}

const eventStore: Events = {};

export const eventEmitter = {
  on<T = unknown>(event: string, callback: EventCallback<T>): () => void {
    if (!eventStore[event]) {
      eventStore[event] = [];
    }
    eventStore[event].push(callback as EventCallback);
    
    // Return unsubscribe function
    return () => {
      eventStore[event] = eventStore[event].filter((cb) => cb !== callback);
    };
  },

  emit<T = unknown>(event: string, data: T): void {
    if (eventStore[event]) {
      eventStore[event].forEach((callback) => callback(data));
    }
  },

  off(event: string, callback: EventCallback): void {
    if (eventStore[event]) {
      eventStore[event] = eventStore[event].filter((cb) => cb !== callback);
    }
  },
};

// Export as 'events' for compatibility with Toast.tsx
export { eventEmitter as events };
