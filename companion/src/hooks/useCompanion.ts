import { useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";

export function useCompanion() {
  const connect = useCallback(async () => {
    try {
      await invoke("connect_websocket");
    } catch (e) {
      console.error("Failed to connect WebSocket:", e);
      throw e;
    }
  }, []);

  const disconnect = useCallback(async () => {
    try {
      await invoke("disconnect_websocket");
    } catch (e) {
      console.error("Failed to disconnect WebSocket:", e);
    }
  }, []);

  return { connect, disconnect };
}
