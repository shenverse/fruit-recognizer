# 使用文档

## 环境要求

- Windows 10 / 11（毛玻璃效果仅在 Windows 上生效）
- Python 3.10+
- 可用摄像头（USB 或内置）
- 可访问互联网（识别接口需要联网）

## 安装

```bash
git clone https://github.com/Du5896/fruit-recognizer.git
cd fruit-recognizer
pip install -r requirements.txt
```

## 配置 API Key

应用使用智谱 GLM-4V 视觉模型。首次使用前需要：

1. 前往 https://open.bigmodel.cn/ 注册并创建 API Key
2. 设置环境变量（推荐）：

```powershell
setx FRUIT_API_KEY "你的Key"
```

3. 或直接在 `app/fruit_app.py` 顶部修改 `API_KEY` 常量。

## 运行

```bash
python app/fruit_app.py
```

## 操作说明

1. 启动后自动打开摄像头画面
2. 把水果对准镜头
3. 点击「识别画面」按钮
4. 等待 1-3 秒，结果卡片弹出：
   - 是水果：绿色卡片显示水果名 + emoji + 趣味说明
   - 不是水果：红色卡片提示「这不是水果」
5. 右上角月亮图标切换深色/浅色主题

## 作为库调用

```python
from core.recognizer import recognize_frame
import cv2

frame = cv2.imread("test.jpg")
result = recognize_frame(frame, api_key="你的Key")
# result = {
#   "is_fruit": True,
#   "name": "苹果",
#   "emoji": "🍎",
#   "desc": "脆甜多汁"
# }
```

## 打包 EXE

```bash
pyinstaller --noconfirm --windowed -F --name fruit-recognizer app/fruit_app.py
```

产物在 `dist/fruit-recognizer.exe`。
