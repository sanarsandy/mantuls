/**
 * useWhiteboardWS.ts
 *
 * WebSocket composable untuk real-time collaboration Excalidraw.
 *
 * Usage:
 *   const ws = useWhiteboardWS(roomId, token, {
 *     onSync:     (elements, appState, users) => ...
 *     onUpdate:   (elements, appState, fromEmail) => ...
 *     onCursor:   (email, color, x, y) => ...
 *     onPresence: (action, user, onlineUsers) => ...
 *     onRestore:  (elements, appState, label) => ...
 *   })
 *
 *   ws.sendUpdate(elements, appState)
 *   ws.sendCursor(x, y)
 *   ws.sendAutosave(elements, appState)
 *   ws.disconnect()
 */

import { ref, onUnmounted } from 'vue'

export interface WsUser {
  email: string
  name: string
  color: string
}

export interface WhiteboardWSCallbacks {
  onSync?: (elements: any[], appState: any, users: WsUser[], isEditor: boolean) => void
  onUpdate?: (elements: any[], appState: any, fromEmail: string) => void
  onCursor?: (email: string, color: string, x: number, y: number) => void
  onPresence?: (action: 'join' | 'leave', user: WsUser, onlineUsers: WsUser[]) => void
  onRestore?: (elements: any[], appState: any, label: string) => void
  onError?: (msg: string) => void
}

export function useWhiteboardWS(
  roomId: string,
  token: string,
  callbacks: WhiteboardWSCallbacks
) {
  const isConnected = ref(false)
  const isReconnecting = ref(false)

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  const MAX_RECONNECT = 5

  // ── Build WS URL (http→ws, https→wss) ────────────────────────────────────
  function buildUrl(): string {
    const config = useRuntimeConfig()
    const apiBase: string = config.public.apiBase || 'http://localhost:8000'
    const wsBase = apiBase.replace(/^http/, 'ws')
    return `${wsBase}/api/v1/whiteboard/ws/${roomId}?token=${encodeURIComponent(token)}`
  }

  // ── Connect ───────────────────────────────────────────────────────────────
  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

    const url = buildUrl()
    ws = new WebSocket(url)

    ws.onopen = () => {
      isConnected.value = true
      isReconnecting.value = false
      reconnectAttempts = 0
    }

    ws.onclose = (ev) => {
      isConnected.value = false
      // Don't reconnect on auth failures
      if (ev.code === 4001 || ev.code === 4003) {
        callbacks.onError?.(`Connection closed: ${ev.reason}`)
        return
      }
      scheduleReconnect()
    }

    ws.onerror = () => {
      callbacks.onError?.('WebSocket connection error')
    }

    ws.onmessage = (ev) => {
      try {
        handleMessage(JSON.parse(ev.data))
      } catch {
        // ignore malformed messages
      }
    }
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT) {
      callbacks.onError?.('Connection lost. Please refresh the page.')
      return
    }
    isReconnecting.value = true
    reconnectAttempts++
    const delay = Math.min(1000 * 2 ** reconnectAttempts, 30_000)
    reconnectTimer = setTimeout(() => connect(), delay)
  }

  // ── Message dispatcher ────────────────────────────────────────────────────
  function handleMessage(msg: any) {
    switch (msg.type) {
      case 'sync':
        callbacks.onSync?.(
          msg.elements ?? [],
          msg.appState ?? {},
          msg.online_users ?? [],
          msg.is_editor ?? true
        )
        break

      case 'update':
        callbacks.onUpdate?.(msg.elements ?? [], msg.appState ?? {}, msg.from ?? '')
        break

      case 'cursor':
        callbacks.onCursor?.(msg.email, msg.color, msg.x, msg.y)
        break

      case 'presence':
        callbacks.onPresence?.(msg.action, msg.user, msg.online_users ?? [])
        break

      case 'restore':
        callbacks.onRestore?.(msg.elements ?? [], msg.appState ?? {}, msg.label ?? '')
        break

      case 'pong':
        break
    }
  }

  // ── Send helpers ──────────────────────────────────────────────────────────
  function _send(data: object) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function sendUpdate(elements: any[], appState: any) {
    _send({ type: 'update', elements, appState })
  }

  function sendCursor(x: number, y: number) {
    _send({ type: 'cursor', x, y })
  }

  function sendAutosave(elements: any[], appState: any) {
    _send({ type: 'autosave', elements, appState })
  }

  function ping() {
    _send({ type: 'ping' })
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    ws = null
    isConnected.value = false
  }

  // ── Keepalive ping every 25s ──────────────────────────────────────────────
  const pingInterval = setInterval(() => {
    if (isConnected.value) ping()
  }, 25_000)

  onUnmounted(() => {
    clearInterval(pingInterval)
    disconnect()
  })

  // Auto-connect immediately
  connect()

  return {
    isConnected,
    isReconnecting,
    sendUpdate,
    sendCursor,
    sendAutosave,
    disconnect,
  }
}
