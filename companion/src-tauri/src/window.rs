use tauri::{AppHandle, Emitter, Manager};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum WindowState {
    Idle,   // Compact bar: 400x80
    Active, // Full chat: 400x600
}

const IDLE_WIDTH: u32 = 400;
const IDLE_HEIGHT: u32 = 80;
const ACTIVE_WIDTH: u32 = 400;
const ACTIVE_HEIGHT: u32 = 600;

/// Toggle window visibility and state
pub fn toggle_window(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    match window.is_visible() {
        Ok(true) => hide_window(app),
        _ => show_window(app),
    }
}

/// Show the window in its current state
pub fn show_window(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    let _ = window.show();
    let _ = window.set_focus();

    // Update state
    app.emit("window-shown", ()).ok();
}

/// Hide the window (minimize to tray)
pub fn hide_window(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    let _ = window.hide();
    app.emit("window-hidden", ()).ok();
}

/// Switch to idle (compact) mode
pub fn set_idle_mode(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize {
        width: IDLE_WIDTH,
        height: IDLE_HEIGHT,
    }));

    if let Some(state) = app.try_state::<crate::AppState>() {
        if let Ok(mut ws) = state.window_state.lock() {
            *ws = WindowState::Idle;
        }
    }

    app.emit("mode-changed", "idle").ok();
}

/// Switch to active (full chat) mode
pub fn set_active_mode(app: &AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };

    let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize {
        width: ACTIVE_WIDTH,
        height: ACTIVE_HEIGHT,
    }));

    if let Some(state) = app.try_state::<crate::AppState>() {
        if let Ok(mut ws) = state.window_state.lock() {
            *ws = WindowState::Active;
        }
    }

    app.emit("mode-changed", "active").ok();
}

/// Toggle between idle and active modes
pub fn toggle_mode(app: &AppHandle) {
    let current = if let Some(state) = app.try_state::<crate::AppState>() {
        state.window_state.lock().map(|g| *g).unwrap_or(WindowState::Idle)
    } else {
        WindowState::Idle
    };

    match current {
        WindowState::Idle => set_active_mode(app),
        WindowState::Active => set_idle_mode(app),
    }
}
