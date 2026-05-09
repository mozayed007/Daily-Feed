use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use once_cell::sync::Lazy;
use tauri::{AppHandle, Emitter};
use tokio::sync::mpsc;

static WS_CONNECTED: AtomicBool = AtomicBool::new(false);
static WS_SENDER: Lazy<Mutex<Option<mpsc::UnboundedSender<String>>>> = Lazy::new(|| Mutex::new(None));

/// Connect to the backend voice WebSocket.
pub async fn connect(app: &AppHandle, backend_url: &str) -> Result<(), String> {
    if WS_CONNECTED.load(Ordering::SeqCst) {
        return Ok(());
    }

    let ws_url = backend_url
        .replace("http://", "ws://")
        .replace("https://", "wss://")
        + "/api/v1/ws/voice";

    let (tx, mut rx) = mpsc::unbounded_channel::<String>();
    {
        let mut sender = WS_SENDER.lock().map_err(|e| e.to_string())?;
        *sender = Some(tx);
    }

    let app_handle = app.clone();

    tokio::spawn(async move {
        let app = app_handle.clone();

        loop {
            if !WS_CONNECTED.load(Ordering::SeqCst) {
                break;
            }

            let ws_stream = match tokio_tungstenite::connect_async(&ws_url).await {
                Ok((ws, _)) => ws,
                Err(e) => {
                    eprintln!("WebSocket connect error: {}", e);
                    let _ = app.emit("ws-error", e.to_string());
                    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                    continue;
                }
            };

            let (mut write, mut read) = ws_stream.split();

            let _ = app.emit("ws-connected", ());
            WS_CONNECTED.store(true, Ordering::SeqCst);

            // Forward outbound messages from the channel
            let outbound = async {
                while let Some(msg) = rx.recv().await {
                    let ws_msg = tokio_tungstenite::tungstenite::Message::Text(msg);
                    if let Err(e) = write.send(ws_msg).await {
                        eprintln!("WebSocket send error: {}", e);
                        break;
                    }
                }
            };

            // Read inbound messages
            let inbound = async {
                while let Some(msg) = read.next().await {
                    match msg {
                        Ok(tokio_tungstenite::tungstenite::Message::Text(text)) => {
                            handle_inbound_message(&app, &text);
                        }
                        Ok(tokio_tungstenite::tungstenite::Message::Close(_)) => {
                            break;
                        }
                        Err(e) => {
                            eprintln!("WebSocket read error: {}", e);
                            break;
                        }
                        _ => {}
                    }
                }
            };

            futures_util::pin_mut!(outbound, inbound);
            futures_util::future::select(outbound, inbound).await;

            WS_CONNECTED.store(false, Ordering::SeqCst);
            let _ = app.emit("ws-disconnected", ());

            // Reconnect delay
            tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
        }
    });

    Ok(())
}

/// Disconnect from the WebSocket.
pub fn disconnect(_app: &AppHandle) {
    WS_CONNECTED.store(false, Ordering::SeqCst);
    {
        let mut sender = WS_SENDER.lock().unwrap();
        *sender = None;
    }
}

/// Send a message over the WebSocket.
pub fn send_message(payload: &str) -> Result<(), String> {
    let sender = WS_SENDER.lock().map_err(|e| e.to_string())?;
    if let Some(tx) = sender.as_ref() {
        tx.send(payload.to_string())
            .map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("WebSocket not connected".to_string())
    }
}

/// Send a text command (no audio) to the assistant.
pub async fn send_text(_app: &AppHandle, _backend_url: &str, text: &str) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({
        "type": "text",
        "text": text,
    });

    send_message(&payload.to_string())?;

    // We rely on the async websocket listener to emit events back to the UI.
    // Return an ack so the frontend knows it was sent.
    Ok(serde_json::json!({"sent": true}))
}

/// Send recorded audio WAV bytes to the backend for STT + processing.
pub fn send_audio(wav_bytes: &[u8], sample_rate: u32) -> Result<(), String> {
    use base64::{Engine as _, engine::general_purpose::STANDARD};
    let b64 = STANDARD.encode(wav_bytes);
    let payload = serde_json::json!({
        "type": "audio",
        "data": b64,
        "sample_rate": sample_rate,
    });
    send_message(&payload.to_string())
}

fn handle_inbound_message(app: &AppHandle, text: &str) {
    let msg: serde_json::Value = match serde_json::from_str(text) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Invalid WS message JSON: {}", e);
            return;
        }
    };

    let msg_type = msg.get("type").and_then(|t| t.as_str()).unwrap_or("unknown");

    match msg_type {
        "transcription" => {
            let _ = app.emit("ws-transcription", msg.get("text").unwrap_or(&serde_json::Value::Null));
        }
        "response" => {
            let _ = app.emit("ws-response", msg.clone());

            // Handle action: open_dashboard
            if let Some(action) = msg.get("action").and_then(|a| a.as_str()) {
                if action == "open_dashboard" {
                    let _ = app.emit("action-open-dashboard", ());
                }
            }
        }
        "audio" => {
            // Backend sent TTS audio (base64 MP3 or WAV)
            let _ = app.emit("ws-audio", msg.clone());
        }
        "error" => {
            let _ = app.emit("ws-error", msg.get("message").unwrap_or(&serde_json::Value::Null));
        }
        _ => {
            let _ = app.emit("ws-raw", msg);
        }
    }
}

use futures_util::{SinkExt, StreamExt};
