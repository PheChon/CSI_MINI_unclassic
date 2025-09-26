#include <stdio.h>
#include "esp_wifi.h"
#include "esp_mac.h" // For ESP-IDF v5.x
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"


void app_main(void) {
    // --- Initialization required for Wi-Fi functions ---
    nvs_flash_init();
    esp_netif_init();
    esp_event_loop_create_default();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_wifi_start();
    // ---------------------------------------------------

    uint8_t mac_addr[6];

    // ดึงค่า MAC Address ของ Wi-Fi Station Interface
    esp_wifi_get_mac(WIFI_IF_STA, mac_addr);

    printf("\n============================================\n");
    printf("Board MAC Address: %02X:%02X:%02X:%02X:%02X:%02X\n",
           mac_addr[0], mac_addr[1], mac_addr[2],
           mac_addr[3], mac_addr[4], mac_addr[5]);
    printf("============================================\n\n");
}