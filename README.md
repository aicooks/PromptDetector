# PromptDetector

PromptDetector 是一个用于**防护与测试**的提示注入/越狱检测演示台（Playground）。它不会提供攻击教程，仅用于帮助开发者在真实工程中识别高风险提示输入。
![Webpage](./image/Webpage.png)
## 功能亮点

- 输入 prompt/对话 → 输出风险分数、命中规则与建议处置（允许/二次确认/拒绝）
- 内置 50 条 benign/attack 测试样例
- 规则引擎可扩展，便于接入更复杂检测器（如 Guardrails）
- 支持上传文档（.txt / .pdf / .docx）直接检测
- 支持上传语音（.wav / .mp3 / .m4a）转写后检测

## 快速开始

1) 安装依赖

```bash
pip install -r requirements.txt
```

2) 启动可视化演示

```bash
streamlit run app.py
```

你也可以在页面中上传 .txt / .pdf / .docx 文件（支持多选），自动加载内容检测。

你还可以上传语音文件（.wav / .mp3 / .m4a，支持多选），系统会使用 faster-whisper 转写并检测。

如需启用 Guardrails 检测：

```bash
PROMPTDETECTOR_USE_GUARDRAILS=1 streamlit run app.py
```

## 语音转写模型说明（faster-whisper）

- 默认使用 `small` 模型，首次运行会自动从 Hugging Face 下载并缓存到：
  - `~/.cache/huggingface/hub`
- 如需指定模型或下载目录，可设置环境变量：
  - `PROMPTDETECTOR_WHISPER_MODEL`（例如 `small`、`medium`）
  - `PROMPTDETECTOR_WHISPER_MODEL_DIR`（自定义模型下载目录）
- 若转写失败，请确认系统已安装 `ffmpeg`（faster-whisper 依赖）。

## 目录结构

```
PromptDetector/
  app.py
  requirements.txt
  README.md
  src/
    prompt_detector/
      detector.py
      rules.py
      data/
        samples.json
  tests/
    test_detector.py
```

## 说明与免责声明

- 本项目**仅用于防护与测试**，帮助识别潜在注入/越狱风险。
- 请勿将本项目用于任何攻击行为。

## 可选：接入 Guardrails

当前版本默认使用规则匹配。如果你希望接入 Guardrails 的 Jailbreak Detection：

1) 安装依赖（可选）

```bash
pip install guardrails-ai
```

2) 在 `src/prompt_detector/detector.py` 中增加自定义检测逻辑并融合评分。

> 注意：Guardrails 可能需要额外模型或配置，请参考其官方文档。当前项目不包含任何模型权重文件。
