use tauri::AppHandle;
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

const DEFAULT_SHORTCUT: &str = "Ctrl+Shift+Space";

fn parse_shortcut(s: &str) -> Option<Shortcut> {
    Shortcut::try_from(s).ok()
}

pub fn register_default(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let shortcut_str = get_shortcut_setting(app.handle());
    let shortcut = parse_shortcut(&shortcut_str)
        .ok_or(format!("Invalid shortcut: {}", shortcut_str))?;

    let shortcut_manager = app.global_shortcut();
    shortcut_manager.on_shortcut(shortcut, move |app, _shortcut, event| {
        if event.state == tauri_plugin_global_shortcut::ShortcutState::Pressed {
            crate::window::toggle_window(app);
        }
    })?;

    Ok(())
}

fn get_shortcut_setting(handle: &AppHandle) -> String {
    let store = tauri_plugin_store::StoreBuilder::new(handle, "settings.json")
        .build();

    if let Ok(store) = store {
        if let Some(val) = store.get("shortcut") {
            if let Some(s) = val.as_str() {
                return s.to_string();
            }
        }
    }

    DEFAULT_SHORTCUT.to_string()
}

pub fn update_shortcut(app: &AppHandle, shortcut_str: &str) -> Result<(), String> {
    let shortcut = parse_shortcut(shortcut_str)
        .ok_or(format!("Invalid shortcut: {}", shortcut_str))?;
    let shortcut_manager = app.global_shortcut();

    // Unregister old
    let old_str = get_shortcut_setting(app);
    if let Some(old) = parse_shortcut(&old_str) {
        shortcut_manager.unregister(old).map_err(|e| e.to_string())?;
    }

    // Register new
    shortcut_manager
        .on_shortcut(shortcut, |app, _shortcut, event| {
            if event.state == tauri_plugin_global_shortcut::ShortcutState::Pressed {
                crate::window::toggle_window(app);
            }
        })
        .map_err(|e| e.to_string())?;

    // Save to store
    let store = tauri_plugin_store::StoreBuilder::new(app, "settings.json")
        .build()
        .map_err(|e| e.to_string())?;
    store.set("shortcut", serde_json::json!(shortcut_str));

    Ok(())
}
