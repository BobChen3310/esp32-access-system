# ESP32 智慧門禁系統

一套基於 ESP32 的門禁系統，整合後端 API、前端管理介面、PostgreSQL 資料庫、MQTT 通訊與 Telegram Bot 遠端控制機制。後端與機器人程式均使用 uv 進行套件管理，ESP32 採用 MicroPython 實作 RFID 門禁邏輯。

## 功能特色

- 使用 ESP32 搭配 RC522、LCD1602、蜂鳴器、電磁閥與 LED 完成門禁控制
- 支援卡片感應、門禁事件上報、警示提示
- 後端採 FastAPI，使用 uv 進行依賴管理與執行
- 使用 PostgreSQL 儲存學生資料、設備紀錄與刷卡事件
- 刷卡驗證採 HTTP Request，遠端解鎖透過 MQTT
- 前端採 React，提供設備管理、學生管理、紀錄查詢等功能
- 提供 Telegram Bot 遠端解鎖能力
- 模組化架構，具備可維護性與延展性

## 專案結構

```
esp32-access-system/
├── backend/                    # 後端 API
│   ├── app/
│   │   ├── routers/            # 路由
│   │   ├── auth.py             # API 安全設定
│   │   ├── database.py         # 資料庫建立程式
│   │   ├── email_utils.py      # 驗證信發送程式
│   │   └── models.py           # ORM 模型
│   ├── pyproject.toml          # 專案配置與依賴
│   ├── main.py                 # 入口程式
│   └── .env.example            # 環境變數範例
├── bot/                        # Telegram Bot
│   ├── bot.py                  # 主程式
│   ├── pyproject.toml          # 專案配置與依賴
│   └── .env.example            # 環境變數範例
├── frontend/                   # React 前端
├── esp32/                      # ESP32 MicroPython 程式
│   ├── modules/
│   ├── esp32_door.py
│   ├── mfrc522.py
│   └── lcd1602.py
└── README.md                   # 說明文件
```

## 快速開始

### 1. **環境需求**
* Python 3.12+
* Node.js 20+
* PostgreSQL 17+

### 2. **後端設定**

1. **進入專案目錄**
    ```bash
    cd esp32-access-system/backend
    ```

2. **安裝依賴**
    ```bash
    uv sync
    ```

3. **設定環境變數**

    複製 `.env.example` 為 `.env` 並填入以下資訊：
    ```bash
    cp .env.example .env
    ```

    ```
    # Database Setting
    DATABASE_URL=postgresql+asyncpg://db_admin:db_passwd@localhost:5432/db_name

    # JWT Setting
    SECRET_KEY=your-secret-key
    ALGORITHM=HS256

    BOT_API_SECRET=your-bot-api-secret

    # MQTT Setting
    MQTT_BROKER=your-broker-ip
    MQTT_PORT=your-broker-port
    MQTT_USERNAME=username
    MQTT_PASSWORD=password

    # Email Setting
    MAIL_USERNAME=your-email
    MAIL_PASSWORD=your-passwd
    MAIL_FROM=your-email
    MAIL_FROM_NAME=your-email-sender
    MAIL_SERVER=your-smtp-server-ip
    MAIL_PORT=your-smtp-server-port
    ```

4. **啟動後端**
    ```bash
    # 啟動後端
    uv run main.py
    
    # 建立管理員帳號
    uv run create_admin.py
    ```
    之後就可透過 Nginx 進行反向代理部署了。

### 3. **前端設定**

1. **進入專案目錄**
    ```bash
    cd esp32-access-system/frontend
    ```

2. **安裝依賴**
    ```bash
    pnpm install
    ```

3. **API 連線設定**

    修改 `src/api/client.js` 中的 `baseURL` 指向正確的後端位址。
    ```js
    import axios from 'axios';

    const apiClient = axios.create({
        baseURL: '將這裡改成你後端 API 的位址',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    ```

4. **編譯打包**
    ```bash
    pnpm build
    ```
    編譯後的檔案位於 `dist/` 目錄，可透過 Nginx 進行反向代理部署。

### 4. 機器人設定

1. **進入專案目錄**
    ```bash
    cd esp32-access-system/bot
    ```

2. **安裝依賴**
    ```bash
    uv sync
    ```

3. **設定環境變數**

    複製 `.env.example` 為 `.env` 並填入以下資訊：
    ```bash
    cp .env.example .env
    ```

    ```
    TELEGRAM_BOT_TOKEN=your-bot-token
    BACKEND_API_URL=you-backend-api-url
    BOT_API_SECRET=your-bot-api-secret
    ```

4. **啟動 Bot**
    ```bash
    uv run bot.py
    ```

### 5. ESP32 程式

將 `esp32-access-system/esp32` 資料夾中的所有檔案上傳到 ESP32，安裝 `umqtt.simple` 套件，修改 `esp32_door.py` 中的 `CONFIG`

```python
CONFIG = {
    "WIFI_SSID": "your-wifi-ssid",
    "WIFI_PASS": "your-wifi-password",
    "API_URL": "your-api-url", 
    "DEVICE_TOKEN": "your-device-token",
    "DEVICE_ID": "your-device-id",
    "MQTT_BROKER": "your-mqtt-broker-ip",
    "MQTT_USER": "your-mqtt-broker-username",
    "MQTT_PASS": "your-mqtt-broker-password",
    "MQTT_PORT": "your-mqtt-broker-port"            # Port Number 記得把雙引號刪除
}
```

之後執行 `esp32_door.py` 即可。

## 外部連結

可以到我的 Blog，查看實際的 Demo 影片與接線

- [Bob's Blog](https://blog.bob0623.net/posts/esp32-access-system-demo/)