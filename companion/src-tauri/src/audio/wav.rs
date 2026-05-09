use byteorder::{LittleEndian, WriteBytesExt};
use std::io::Write;

/// Encode 16-bit PCM mono samples into a standard WAV file (in-memory bytes).
pub fn encode_wav(samples: &[i16], sample_rate: u32, channels: u16) -> Result<Vec<u8>, String> {
    let mut buf = Vec::new();

    let data_size = (samples.len() * 2) as u32;
    let file_size = 36 + data_size;
    let byte_rate = sample_rate * 2 * channels as u32;
    let block_align = 2 * channels;

    // RIFF header
    buf.write_all(b"RIFF").map_err(|e| e.to_string())?;
    buf.write_u32::<LittleEndian>(file_size)
        .map_err(|e| e.to_string())?;
    buf.write_all(b"WAVE").map_err(|e| e.to_string())?;

    // fmt chunk
    buf.write_all(b"fmt ").map_err(|e| e.to_string())?;
    buf.write_u32::<LittleEndian>(16).map_err(|e| e.to_string())?; // chunk size
    buf.write_u16::<LittleEndian>(1).map_err(|e| e.to_string())?; // PCM
    buf.write_u16::<LittleEndian>(channels)
        .map_err(|e| e.to_string())?;
    buf.write_u32::<LittleEndian>(sample_rate)
        .map_err(|e| e.to_string())?;
    buf.write_u32::<LittleEndian>(byte_rate)
        .map_err(|e| e.to_string())?;
    buf.write_u16::<LittleEndian>(block_align)
        .map_err(|e| e.to_string())?;
    buf.write_u16::<LittleEndian>(16).map_err(|e| e.to_string())?; // bits per sample

    // data chunk
    buf.write_all(b"data").map_err(|e| e.to_string())?;
    buf.write_u32::<LittleEndian>(data_size)
        .map_err(|e| e.to_string())?;

    for sample in samples {
        buf.write_i16::<LittleEndian>(*sample)
            .map_err(|e| e.to_string())?;
    }

    Ok(buf)
}
