use std::io::Cursor;

/// Play WAV or MP3 audio bytes through the default speakers.
pub fn play_audio(data: &[u8]) -> Result<(), String> {
    let (_stream, handle) = rodio::OutputStream::try_default().map_err(|e| e.to_string())?;
    let cursor = Cursor::new(data.to_vec());
    let source = rodio::Decoder::new(cursor).map_err(|e| e.to_string())?;
    let sink = rodio::Sink::try_new(&handle).map_err(|e| e.to_string())?;
    sink.append(source);
    sink.sleep_until_end();
    Ok(())
}

/// Play audio in a background thread (non-blocking for the caller).
pub fn play_audio_async(data: Vec<u8>) {
    std::thread::spawn(move || {
        if let Err(e) = play_audio(&data) {
            eprintln!("Audio playback error: {}", e);
        }
    });
}

/// Stop any currently playing audio.
pub fn stop_audio() {
    // Rodio sinks auto-drop when done. To support explicit stop,
    // we'd need a shared sink reference. For now, audio plays to completion.
}
