use tauri::AppHandle;
use std::time::Instant;

#[derive(serde::Serialize)]
pub struct PingResult {
    pub success: bool,
    pub latency: u64,
}

// Hardcoded allowed domain for security (QA requirement)
const ALLOWED_DOMAIN: &str = "www.google.com";

#[tauri::command]
async fn ping(url: String) -> Result<PingResult, String> {
    // Security Check: Validate that the requested URL matches the allowed domain
    if !url.contains(ALLOWED_DOMAIN) {
        return Err(format!("Security Violation: URL must target {}", ALLOWED_DOMAIN));
    }

    let start = Instant::now();
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    let response = client.head(&url).send().await;
    let latency = start.elapsed().as_millis() as u64;

    match response {
        Ok(resp) => {
             if resp.status().is_success() {
                 Ok(PingResult {
                     success: true,
                     latency,
                 })
             } else {
                  Ok(PingResult {
                     success: true,
                     latency,
                 })
             }
        }
        Err(_e) => {
             Ok(PingResult {
                 success: false,
                 latency: 0,
             })
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_store::Builder::default().build())
    .invoke_handler(tauri::generate_handler![ping])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
