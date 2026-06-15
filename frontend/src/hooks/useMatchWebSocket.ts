"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { WsMessage } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useMatchWebSocket(matchId: string) {
  const [messages, setMessages] = useState<WsMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(`${WS_URL}/api/v1/ws/matches/${matchId}`);

    ws.current.onopen = () => setConnected(true);

    ws.current.onmessage = (event) => {
      const data: WsMessage = JSON.parse(event.data);
      if (data.type === "PING") return;
      setMessages((prev) => [data, ...prev].slice(0, 100));
    };

    ws.current.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.current.onerror = () => ws.current?.close();
  }, [matchId]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current!);
      ws.current?.close();
    };
  }, [connect]);

  return { messages, connected };
}
