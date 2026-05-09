// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use daily_jarvis_companion_lib::run;

fn main() {
    run();
}
