use tauri::{AppHandle, State, Manager};
use crate::{AppState, window, audio, ws_client};

// ── Window Commands ──────────────────────────────────────────────────────────

#[tauri::command]
pub fn toggle_window(_state: State<'_, AppState>, app: AppHandle) {
    window::toggle_window(&app);
}

#[tauri::command]
pub fn show_window(app: AppHandle) {
    window::show_window(&app);
}

#[tauri::command]
pub fn hide_window(app: AppHandle) {
    window::hide_window(&app);
}

#[tauri::command]
pub fn set_idle_mode(app: AppHandle) {
    window::set_idle_mode(&app);
}

#[tauri::command]
pub fn set_active_mode(app: AppHandle) {
    window::set_active_mode(&app);
}

// ── Audio Commands ───────────────────────────────────────────────────────────

#[tauri::command]
pub fn start_recording(app: AppHandle) -> Result<String, String> {
    audio::capture::start(&app)
}

#[tauri::command]
pub fn stop_recording(app: AppHandle) -> Result<Vec<u8>, String> {
    audio::capture::stop(&app)
}

// ── Text / WebSocket Commands ────────────────────────────────────────────────

#[tauri::command]
pub async fn send_text_command(
    app: AppHandle,
    state: State<'_, AppState>,
    text: String,
) -> Result<serde_json::Value, String> {
    let url = state.backend_url.lock().map_err(|e| e.to_string())?.clone();
    ws_client::send_text(&app, &url, &text).await
}

#[tauri::command]
pub fn send_audio(
    _app: AppHandle,
    base64_data: String,
    sample_rate: u32,
) -> Result<(), String> {
    use base64::{Engine as _, engine::general_purpose::STANDARD};
    let wav_bytes = STANDARD.decode(base64_data).map_err(|e| e.to_string())?;
    ws_client::send_audio(&wav_bytes, sample_rate)
}

#[tauri::command]
pub async fn connect_websocket(
    app: AppHandle,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let url = state.backend_url.lock().map_err(|e| e.to_string())?.clone();
    ws_client::connect(&app, &url).await
}

#[tauri::command]
pub fn disconnect_websocket(app: AppHandle) {
    ws_client::disconnect(&app);
}

// ── Settings Commands ────────────────────────────────────────────────────────

#[derive(serde::Serialize, serde::Deserialize)]
pub struct CompanionSettings {
    pub backend_url: String,
    pub voice_persona: String,
    pub shortcut: String,
}

#[tauri::command]
pub fn get_settings(app: AppHandle) -> Result<CompanionSettings, String> {
    let store = tauri_plugin_store::StoreBuilder::new(&app, "settings.json")
        .build()
        .map_err(|e| e.to_string())?;

    let default = CompanionSettings {
        backend_url: "http://localhost:8000".to_string(),
        voice_persona: "jarvis".to_string(),
        shortcut: "Ctrl+Shift+Space".to_string(),
    };

    let backend_url = store
        .get("backend_url")
        .and_then(|v| v.as_str().map(|s| s.to_string()))
        .unwrap_or(default.backend_url);

    let voice_persona = store
        .get("voice_persona")
        .and_then(|v| v.as_str().map(|s| s.to_string()))
        .unwrap_or(default.voice_persona);

    let shortcut = store
        .get("shortcut")
        .and_then(|v| v.as_str().map(|s| s.to_string()))
        .unwrap_or(default.shortcut);

    Ok(CompanionSettings {
        backend_url,
        voice_persona,
        shortcut,
    })
}

#[tauri::command]
pub fn set_settings(app: AppHandle, settings: CompanionSettings) -> Result<(), String> {
    let store = tauri_plugin_store::StoreBuilder::new(&app, "settings.json")
        .build()
        .map_err(|e| e.to_string())?;

    store.set("backend_url", serde_json::json!(settings.backend_url));
    store.set("voice_persona", serde_json::json!(settings.voice_persona));
    store.set("shortcut", serde_json::json!(settings.shortcut));

    // Update in-memory state
    if let Some(state) = app.try_state::<AppState>() {
        if let Ok(mut url) = state.backend_url.lock() {
            *url = settings.backend_url;
        }
        if let Ok(mut persona) = state.voice_persona.lock() {
            *persona = settings.voice_persona;
        }
    }

    // Update shortcut if changed
    crate::shortcut::update_shortcut(&app, &settings.shortcut).ok();

    Ok(())
}

// ── Dashboard / Shell Commands ───────────────────────────────────────────────

#[tauri::command]
pub async fn open_dashboard(state: State<'_, AppState>) -> Result<String, String> {
    let url = state.backend_url.lock().map_err(|e| e.to_string())?.clone();
    let full_url = if url.ends_with('/') { url } else { format!("{}/", url) };
    Ok(full_url)
}

// ── Status Command ─────────────────────────────────────────────────────────

#[derive(serde::Serialize)]
pub struct CompanionStatus {
    pub ws_connected: bool,
    pub voice_persona: String,
    pub recording: bool,
}

#[tauri::command]
pub fn get_status(state: State<'_, AppState>) -> Result<CompanionStatus, String> {
    let ws_connected = *state.ws_connected.lock().map_err(|e| e.to_string())?;
    let voice_persona = state.voice_persona.lock().map_err(|e| e.to_string())?.clone();
    let recording = audio::capture::is_recording();

    Ok(CompanionStatus {
        ws_connected,
        voice_persona,
        recording,
    })
}
