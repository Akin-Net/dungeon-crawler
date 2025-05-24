// frontend/src/hooks/useGameWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';

const WEBSOCKET_URL = 'ws://localhost:8000/ws/dungeon';

export function useGameWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [messageBatch, setMessageBatch] = useState([]); 
  const [error, setError] = useState(null);
  const ws = useRef(null);
  
  const incomingMessageQueue = useRef([]);
  const messageProcessingTimeout = useRef(null);

  useEffect(() => {
    let didUnmount = false;
    console.log("[useGameWebSocket] useEffect attempting to connect to:", WEBSOCKET_URL);
    
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED && ws.current.readyState !== WebSocket.CLOSING) {
        console.warn("[useGameWebSocket] Closing existing WebSocket before new attempt.");
        ws.current.close(1000, "Hook re-running, closing old socket");
    }

    const socket = new WebSocket(WEBSOCKET_URL);
    ws.current = socket;

    setIsConnected(false); setError(null); setMessageBatch([]);

    socket.onopen = () => {
      if (didUnmount || socket !== ws.current) return;
      console.log("[useGameWebSocket] WebSocket connected successfully.");
      setIsConnected(true); setError(null);
    };

    socket.onmessage = (event) => { /* ... same message batching logic ... */ 
      if (didUnmount || socket !== ws.current) return;
      try {
        const parsedMessage = JSON.parse(event.data);
        incomingMessageQueue.current.push(parsedMessage);
        if (!messageProcessingTimeout.current) {
          messageProcessingTimeout.current = setTimeout(() => {
            if (incomingMessageQueue.current.length > 0) {
              // console.log(`[useGameWebSocket] Batching ${incomingMessageQueue.current.length} messages.`);
              setMessageBatch([...incomingMessageQueue.current]);
              incomingMessageQueue.current = []; 
            }
            messageProcessingTimeout.current = null;
          }, 0); 
        }
      } catch (e) { /* ... error handling ... */ }
    };
    socket.onerror = (event) => { /* ... same ... */ };
    socket.onclose = (event) => { /* ... same ... */ };
    return () => { /* ... same cleanup ... */ };
  }, []);

  const sendMessage = useCallback((messageObject) => {
    console.log("[useGameWebSocket] sendMessage CALLED. Action:", messageObject?.action); // Log call
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const messageString = JSON.stringify(messageObject);
      console.log("[useGameWebSocket] SENDING WS message:", messageString); // Log what's being sent
      ws.current.send(messageString);
    } else {
      console.error("[useGameWebSocket] FAILED TO SEND: WebSocket not open or not initialized.", 
                   "ws.current exists:", !!ws.current, 
                   "readyState:", ws.current?.readyState,
                   "Attempted action:", messageObject?.action);
      setError("Cannot send message: Not connected or WebSocket issue.");
    }
  }, []); // ws.current is a ref, no need in deps

  return { isConnected, messageBatch, sendMessage, error };
}