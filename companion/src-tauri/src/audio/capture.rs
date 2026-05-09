use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter};

static RECORDING: AtomicBool = AtomicBool::new(false);
static AUDIO_BUFFER: Mutex<Vec<i16>> = Mutex::new(Vec::new());

/// Start recording from the default microphone.
/// Returns WAV bytes ready for base64 encoding.
pub fn start(app: &AppHandle) -> Result<String, String> {
    if RECORDING.load(Ordering::SeqCst) {
        return Err("Already recording".to_string());
    }

    // Clear buffer
    {
        let mut buf = AUDIO_BUFFER.lock().map_err(|e| e.to_string())?;
        buf.clear();
    }

    // Emit recording-start event to UI
    let _ = app.emit("audio-recording-started", ());
    RECORDING.store(true, Ordering::SeqCst);

    // Spawn audio capture thread
    let app_handle = app.clone();
    std::thread::spawn(move || {
        if let Err(e) = capture_thread(&app_handle) {
            let _ = app_handle.emit("audio-recording-error", e.to_string());
        }
    });

    Ok("Recording started".to_string())
}

/// Stop recording and return the WAV-encoded bytes.
pub fn stop(app: &AppHandle) -> Result<Vec<u8>, String> {
    if !RECORDING.load(Ordering::SeqCst) {
        return Err("Not recording".to_string());
    }

    RECORDING.store(false, Ordering::SeqCst);

    // Small delay to let the capture thread finish its last buffer flush
    std::thread::sleep(std::time::Duration::from_millis(100));

    let samples = {
        let buf = AUDIO_BUFFER.lock().map_err(|e| e.to_string())?;
        buf.clone()
    };

    // Encode to in-memory WAV
    let wav_bytes = super::wav::encode_wav(&samples, 16000, 1)?;

    let _ = app.emit("audio-recording-stopped", ());

    Ok(wav_bytes)
}

/// Check if currently recording
pub fn is_recording() -> bool {
    RECORDING.load(Ordering::SeqCst)
}

fn capture_thread(app: &AppHandle) -> Result<(), String> {
    use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};

    let host = cpal::default_host();
    let device = host
        .default_input_device()
        .ok_or("No default input device found")?;

    let config = device
        .default_input_config()
        .map_err(|e| e.to_string())?;

    let _sample_rate = config.sample_rate().0;
    let channels = config.channels();

    let app_handle = app.clone();
    let stream = device
        .build_input_stream(
            &config.into(),
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                if !RECORDING.load(Ordering::SeqCst) {
                    return;
                }

                // Convert f32 interleaved to i16 mono (downmix if stereo)
                let mut samples = Vec::with_capacity(data.len() / channels as usize);
                for chunk in data.chunks(channels as usize) {
                    let mono: f32 = chunk.iter().sum::<f32>() / channels as f32;
                    let clamped = mono.clamp(-1.0, 1.0);
                    let pcm16 = (clamped * 32767.0) as i16;
                    samples.push(pcm16);
                }

                if let Ok(mut buf) = AUDIO_BUFFER.lock() {
                    buf.extend_from_slice(&samples);
                }

                // Emit VU meter level periodically (every ~100ms worth of samples)
                if !samples.is_empty() {
                    let peak = samples
                        .iter()
                        .map(|s| s.abs())
                        .max()
                        .unwrap_or(0) as f32
                        / 32767.0;
                    let _ = app_handle.emit("audio-level", peak);
                }
            },
            move |err| {
                eprintln!("Audio capture error: {}", err);
            },
            None,
        )
        .map_err(|e| e.to_string())?;

    stream.play().map_err(|e| e.to_string())?;

    // Keep the stream alive while recording
    while RECORDING.load(Ordering::SeqCst) {
        std::thread::sleep(std::time::Duration::from_millis(50));
    }

    // Stream will be dropped here, stopping capture
    Ok(())
}
