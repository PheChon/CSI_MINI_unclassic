#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"

// -- กำหนดค่า Wi-Fi --
#define WIFI_SSID           "Error404_2.4G"
#define WIFI_PASS           "URL/ee64"
#define WIFI_MAXIMUM_RETRY  5

// -- กำหนดค่าสำหรับ Log-Distance Path Loss Model --
// !!! สำคัญ: คุณต้องทำการสอบเทียบ (Calibrate) ค่าเหล่านี้ในสภาพแวดล้อมจริง !!!
#define CAL_RSSI_AT_1M      -45.0 // (A) ค่า RSSI เฉลี่ยที่วัดได้ ณ ระยะ 1 เมตร (dBm)
#define PATH_LOSS_N         2.5   // (n) ค่าคงที่การลดทอนของสัญญาณ

static const char *TAG = "WIFI_CSI_APP";
static int s_retry_num = 0;
static bool wifi_connected = false;

// --- ฟังก์ชันคำนวณระยะทางจาก RSSI ---
float estimate_distance_from_rssi(int rssi) {
    // สูตร: d = 10^((A - RSSI) / (10 * n))
    float distance = pow(10, (CAL_RSSI_AT_1M - (float)rssi) / (10.0 * PATH_LOSS_N));
    return distance;
}

// --- Callback Function สำหรับรับข้อมูล CSI ---
void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *info) {
    if (!info || !info->buf || !wifi_connected) {
        return;
    }

    printf("CSI_DATA,");
    int8_t *csi_buf = (int8_t *)info->buf;
    for (int i = 0; i < info->len; i += 2) {
        float amplitude = sqrt(pow(csi_buf[i], 2) + pow(csi_buf[i+1], 2));
        printf("%.2f%s", amplitude, (i < info->len - 2) ? "," : "");
    }
    printf("\n");
}

// --- Task สำหรับแสดงค่า RSSI และระยะทางเป็นระยะ ---
void display_info_task(void *pvParameters) {
    while(1) {
        if (wifi_connected) {
            wifi_ap_record_t ap_info;
            if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
                int rssi = ap_info.rssi;
                float dist_rssi = estimate_distance_from_rssi(rssi);

                printf("RSSI,%d\n", rssi);
                printf("DISTANCE_RSSI,%.2f\n", dist_rssi);
                printf("---\n");
            }
        }
        vTaskDelay(pdMS_TO_TICKS(2000)); // แสดงผลทุก 2 วินาที
    }
}


// --- Event Handler สำหรับจัดการ Wi-Fi Events ---
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_connected = false;
        // ปิด CSI เมื่อหลุดจากการเชื่อมต่อ
        esp_wifi_set_csi(false);
        if (s_retry_num < WIFI_MAXIMUM_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "Retry to connect to the AP (%d/%d)", s_retry_num, WIFI_MAXIMUM_RETRY);
        } else {
            ESP_LOGE(TAG, "Failed to connect to Wi-Fi after %d attempts", WIFI_MAXIMUM_RETRY);
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "CONNECTED! IP: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        wifi_connected = true;

        // *** เปิดใช้งาน CSI หลังจากเชื่อมต่อ Wi-Fi สำเร็จแล้ว ***
        ESP_LOGI(TAG, "Enabling CSI...");
        ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
        wifi_csi_config_t csi_config = {
            .lltf_en = true, .htltf_en = true, .stbc_htltf2_en = true,
            .ltf_merge_en = true, .channel_filter_en = true, .manu_scale = false
        };
        ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
        ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(wifi_csi_rx_cb, NULL));
        ESP_ERROR_CHECK(esp_wifi_set_csi(true));
    }
}


void app_main(void)
{
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize Network Stack
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    
    // Initialize Wi-Fi driver
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    // Register event handlers
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, NULL));
    
    // Set Wi-Fi configuration
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config));
    
    // Start Wi-Fi
    ESP_ERROR_CHECK(esp_wifi_start());
    
    // สร้าง Task สำหรับแสดงผลข้อมูล RSSI และระยะทาง
    xTaskCreate(&display_info_task, "display_info_task", 4096, NULL, 5, NULL);
}