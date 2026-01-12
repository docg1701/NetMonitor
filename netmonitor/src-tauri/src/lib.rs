use tauri::{Manager, State};
use std::time::Instant;

struct AppState {
    client: reqwest::Client,
}

#[derive(serde::Serialize)]
pub struct PingResult {
    pub success: bool,
    pub latency_ms: u64,
}

// Whitelist of allowed ping targets (IPs and domains)
const ALLOWED_TARGETS: [&str; 6] = [
    "8.8.8.8",
    "1.1.1.1",
    "9.9.9.9",
    "208.67.222.222",
    "www.google.com",
    "www.cloudflare.com"
];

#[tauri::command]
async fn ping(url: String, state: State<'_, AppState>) -> Result<PingResult, String> {
    // Security Check: Validate that the requested URL is in the whitelist
    if !ALLOWED_TARGETS.contains(&url.as_str()) {
        return Err(format!("Target '{}' not in whitelist", url));
    }

    // Construct full URL with https scheme
    let full_url = format!("https://{}", url);

    let start = Instant::now();
    // Use the shared client from AppState
    let response = state.client.head(&full_url).send().await;
    let latency_ms = start.elapsed().as_millis() as u64;

    match response {
        Ok(resp) => {
            Ok(PingResult {
                success: resp.status().is_success(),
                latency_ms,
            })
        }
        Err(_e) => {
            Ok(PingResult {
                success: false,
                latency_ms: 0,
            })
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  // Disable DMA-BUF renderer to fix blank screen on Linux with NVIDIA GPUs
  std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");

  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_store::Builder::default().build())
    .plugin(tauri_plugin_sql::Builder::new().build())
    .invoke_handler(tauri::generate_handler![ping])
    .setup(|app| {
      // Initialize the reqwest client once and manage it in AppState
      // Force HTTP/1 only and disable all connection pooling/reuse
      // to ensure each ping measures full connection latency (DNS + TCP + TLS + HTTP)
      let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .http1_only()
        .pool_max_idle_per_host(0)
        .pool_idle_timeout(std::time::Duration::ZERO)
        .tcp_keepalive(None)
        .build()
        .map_err(|e| Box::new(e) as Box<dyn std::error::Error>)?;

      app.manage(AppState { client });

      // Open DevTools for debugging
      if let Some(window) = app.get_webview_window("main") {
        window.open_devtools();
      }

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
