use tauri::{Manager, State};
use std::time::Instant;

struct AppState {
    client: reqwest::Client,
}

#[derive(serde::Serialize)]
pub struct PingResult {
    pub success: bool,
    pub latency: u64,
}

// Hardcoded allowed domain for security (QA requirement)
const ALLOWED_DOMAIN: &str = "www.google.com";

#[tauri::command]
async fn ping(url: String, state: State<'_, AppState>) -> Result<PingResult, String> {
    // Security Check: Validate that the requested URL matches the allowed domain
    if !url.contains(ALLOWED_DOMAIN) {
        return Err(format!("Security Violation: URL must target {}", ALLOWED_DOMAIN));
    }

    let start = Instant::now();
    // Use the shared client from AppState
    let response = state.client.head(&url).send().await;
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
    .plugin(tauri_plugin_sql::Builder::new().build())
    .invoke_handler(tauri::generate_handler![ping])
    .setup(|app| {
      // Initialize the reqwest client once and manage it in AppState
      let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| Box::new(e) as Box<dyn std::error::Error>)?;

      app.manage(AppState { client });

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
