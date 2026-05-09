use tauri::{
    Emitter, Manager,
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
};

pub fn setup_tray(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let handle = app.handle();
    let quit_i = MenuItem::with_id(handle, "quit", "Quit", true, None::<&str>)?;
    let show_i = MenuItem::with_id(handle, "show", "Show / Hide", true, None::<&str>)?;
    let jarvis_i = MenuItem::with_id(handle, "jarvis", "Voice: Jarvis", true, None::<&str>)?;
    let friday_i = MenuItem::with_id(handle, "friday", "Voice: Friday", true, None::<&str>)?;
    let settings_i = MenuItem::with_id(handle, "settings", "Settings", true, None::<&str>)?;

    let menu = Menu::with_items(
        handle,
        &[
            &show_i,
            &jarvis_i,
            &friday_i,
            &settings_i,
            &quit_i,
        ],
    )?;

    TrayIconBuilder::new()
        .menu(&menu)
        .show_menu_on_left_click(true)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "quit" => {
                app.exit(0);
            }
            "show" => {
                crate::window::toggle_window(app);
            }
            "jarvis" => {
                if let Some(state) = app.try_state::<crate::AppState>() {
                    if let Ok(mut p) = state.voice_persona.lock() {
                        *p = "jarvis".to_string();
                    }
                }
                let _ = app.emit("persona-changed", "jarvis");
            }
            "friday" => {
                if let Some(state) = app.try_state::<crate::AppState>() {
                    if let Ok(mut p) = state.voice_persona.lock() {
                        *p = "friday".to_string();
                    }
                }
                let _ = app.emit("persona-changed", "friday");
            }
            "settings" => {
                crate::window::show_window(app);
                crate::window::set_active_mode(app);
                let _ = app.emit("show-settings", ());
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let tauri::tray::TrayIconEvent::Click { button, .. } = event {
                if button == tauri::tray::MouseButton::Left {
                    let app = tray.app_handle();
                    crate::window::toggle_window(&app);
                }
            }
        })
        .build(app)?;

    Ok(())
}
