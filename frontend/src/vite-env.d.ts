/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEBSOCKET_BASE_URL?: string;
  readonly VITE_WEBSOCKET_CONNECT_TIMEOUT_SECONDS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

