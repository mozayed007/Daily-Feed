use std::sync::Mutex;
use tauri::{Manager, AppHandle};

pub mod audio;
pub mod commands;
pub mod shortcut;
pub mod tray;
pub mod window;
pub mod ws_client;

use window::WindowState;

/// Shared app state across threads
pub struct AppState {
    pub window_state: Mutex<WindowState>,
    pub backend_url: Mutex<String>,
    pub voice_persona: Mutex<String>,
    pub ws_connected: Mutex<bool>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            window_state: Mutex::new(WindowState::Idle),
            backend_url: Mutex::new("http://localhost:8000".to_string()),
            voice_persona: Mutex::new("jarvis".to_string()),
            ws_connected: Mutex::new(false),
        }
    }
}

/// Initialize the Tauri application
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_positioner::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .manage(AppState::new())
        .setup(|app| {
            // Load settings from store
            load_settings(app.handle());

            // Set up system tray
            tray::setup_tray(app)?;

            // Register global shortcut
            shortcut::register_default(app)?;

            // Hide window initially (it shows only on tray click or shortcut)
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.hide();
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::toggle_window,
            commands::show_window,
            commands::hide_window,
            commands::set_idle_mode,
            commands::set_active_mode,
            commands::start_recording,
            commands::stop_recording,
            commands::send_text_command,
            commands::send_audio,
            commands::get_settings,
            commands::set_settings,
            commands::get_status,
            commands::connect_websocket,
            commands::open_dashboard,
            commands::disconnect_websocket,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn load_settings(handle: &AppHandle) {
    let store_result = tauri_plugin_store::StoreBuilder::new(handle, "settings.json")
        .build();

    if let Ok(store) = store_result {
        if let Some(state) = handle.try_state::<AppState>() {
            if let Some(url) = store.get("backend_url") {
                if let Some(url_str) = url.as_str() {
                    let mut backend = state.backend_url.lock().unwrap();
                    *backend = url_str.to_string();
                }
            }
            if let Some(persona) = store.get("voice_persona") {
                if let Some(p_str) = persona.as_str() {
                    let mut p = state.voice_persona.lock().unwrap();
                    *p = p_str.to_string();
                }
            }
        }
    }
}
