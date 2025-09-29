#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"

static const char *TAG = "GATEWAY_NODE";

// MAC Address ของ Receiver (Reference Node)
static uint8_t reference_node_mac[] = {0x98, 0xA3, 0x16, 0xEB, 0xE6, 0xCC}; // <-- MAC Address ของ Receiver ถูกแก้ไขที่นี่

typedef struct {
    double distance;
} response_data_t;

// Callback เมื่อได้รับข้อมูลตอบกลับ
static void esp_now_recv_cb(const esp_now_recv_info_t *recv_info, const uint8_t *data, int len) {
    if (len == sizeof(response_data_t)) {
        response_data_t *response = (response_data_t *)data;
        // ส่งข้อมูลออกทาง Serial Port ทันที
        printf("Distance:%.2f\n", response->distance);
    }
}

// Task สำหรับส่ง Poll Packet แบบต่อเนื่อง
void send_poll_task(void *pvParameter) {
    const uint8_t poll_msg[] = "POLL";
    while (100) {
        esp_err_t result = esp_now_send(reference_node_mac, poll_msg, sizeof(poll_msg));
        
        // --- การจัดการข้อผิดพลาดสำหรับความเร็วสูง ---
        // ถ้า Buffer ของ ESP-NOW เต็ม (ส่งเร็วเกินไป) ให้หน่วงเวลาสั้นๆ
        if (result == ESP_ERR_ESPNOW_NO_MEM) {
            vTaskDelay(pdMS_TO_TICKS(100)); // หน่วง 2ms เพื่อให้ Buffer ว่าง
        }
        // ไม่มีการ delay ในกรณีปกติ เพื่อให้ส่งได้เร็วที่สุด
    }
}

void app_main(void) {
    nvs_flash_init();
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_wifi_set_storage(WIFI_STORAGE_RAM);
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();
    esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);

    esp_now_init();
    esp_now_register_recv_cb(esp_now_recv_cb);

    esp_now_peer_info_t peer_info = {};
    memcpy(peer_info.peer_addr, reference_node_mac, 6);
    peer_info.channel = 1;
    peer_info.encrypt = false;
    if (esp_now_add_peer(&peer_info) != ESP_OK){
        ESP_LOGE(TAG, "Failed to add peer");
        return;
    }

    xTaskCreate(send_poll_task, "send_poll_task", 2048, NULL, 5, NULL);
    ESP_LOGI(TAG, "Gateway Node Initialized. Polling at maximum speed.");
}