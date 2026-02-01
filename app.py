import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

import streamlit as st

try:
    from docx import Document
except Exception:  # pragma: no cover - optional dependency
    Document = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from prompt_detector.detector import analyze  # noqa: E402

SAMPLES_PATH = os.path.join(
    PROJECT_ROOT, "src", "prompt_detector", "data", "samples.json"
)
WHISPER_MODEL_NAME = os.getenv("PROMPTDETECTOR_WHISPER_MODEL", "small")
WHISPER_MODEL_DIR = os.getenv("PROMPTDETECTOR_WHISPER_MODEL_DIR")


def load_samples() -> List[Dict[str, str]]:
    with open(SAMPLES_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_txt(uploaded) -> str:
    return uploaded.getvalue().decode("utf-8", errors="ignore")


def _read_pdf(uploaded) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(uploaded)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_docx(uploaded) -> str:
    if Document is None:
        return ""
    doc = Document(uploaded)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def extract_text_from_upload(uploaded) -> Optional[str]:
    if not uploaded:
        return None
    name = uploaded.name.lower()
    if name.endswith(".txt"):
        return _read_txt(uploaded)
    if name.endswith(".pdf"):
        return _read_pdf(uploaded)
    if name.endswith(".docx"):
        return _read_docx(uploaded)
    return None


@st.cache_resource(show_spinner=False)
def get_whisper_model() -> Optional[Any]:
    if WhisperModel is None:
        return None
    if WHISPER_MODEL_DIR:
        return WhisperModel(WHISPER_MODEL_NAME, download_root=WHISPER_MODEL_DIR)
    return WhisperModel(WHISPER_MODEL_NAME)


def transcribe_audio(uploaded) -> Optional[str]:
    if WhisperModel is None:
        return None
    model = get_whisper_model()
    if model is None:
        return None

    suffix = os.path.splitext(uploaded.name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    try:
        segments, _info = model.transcribe(tmp_path)
        return " ".join(segment.text.strip() for segment in segments if segment.text)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def main() -> None:
    st.set_page_config(page_title="PromptDetector", page_icon="🛡️", layout="wide")
    st.title("🛡️ PromptDetector：注入/越狱检测演示台")
    st.caption("仅用于防护与测试，请勿用于攻击行为。")

    samples = load_samples()
    sample_options = [f"{sample['id']:02d} · {sample['title']}" for sample in samples]

    if "prompt_text" not in st.session_state:
        st.session_state.prompt_text = ""
    if "doc_uploader_key" not in st.session_state:
        st.session_state.doc_uploader_key = 0
    if "audio_uploader_key" not in st.session_state:
        st.session_state.audio_uploader_key = 0

    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("输入区域")
        selected = st.selectbox("选择测试样例", options=sample_options)
        if st.button("加载样例", use_container_width=True):
            index = sample_options.index(selected)
            st.session_state.prompt_text = samples[index]["text"]

        uploaded_docs = st.file_uploader(
            "上传文档（支持 .txt / .pdf / .docx，可多选）",
            type=["txt", "pdf", "docx"],
            accept_multiple_files=True,
            key=f"doc_uploader_{st.session_state.doc_uploader_key}",
        )
        uploaded_audio = st.file_uploader(
            "上传语音（支持 .wav / .mp3 / .m4a，可多选）",
            type=["wav", "mp3", "m4a"],
            accept_multiple_files=True,
            key=f"audio_uploader_{st.session_state.audio_uploader_key}",
        )

        if uploaded_docs or uploaded_audio:
            combined_chunks: List[str] = []

            if uploaded_docs:
                for uploaded in uploaded_docs:
                    extracted = extract_text_from_upload(uploaded)
                    if extracted is None:
                        st.warning(f"{uploaded.name} 无法读取。")
                    elif not extracted.strip():
                        st.warning(f"{uploaded.name} 内容为空。")
                    else:
                        combined_chunks.append(f"[文档:{uploaded.name}]\n{extracted}")

            if uploaded_audio:
                for audio in uploaded_audio:
                    with st.spinner(f"正在转写语音：{audio.name} …"):
                        transcript = transcribe_audio(audio)
                    if transcript is None:
                        st.warning(f"{audio.name} 转写不可用，请确认已安装 faster-whisper 与依赖。")
                    elif not transcript.strip():
                        st.warning(f"{audio.name} 未识别出内容。")
                    else:
                        combined_chunks.append(f"[语音:{audio.name}]\n{transcript}")

            if combined_chunks:
                st.session_state.prompt_text = "\n\n".join(combined_chunks)
                st.success("文件内容已合并并加载到输入框。")

        st.session_state.prompt_text = st.text_area(
            "Prompt / 对话内容",
            height=240,
            value=st.session_state.prompt_text,
            placeholder="在此输入 prompt 或对话内容…",
        )

        col_run, col_clear = st.columns([1, 1])
        run = col_run.button("运行检测", type="primary", use_container_width=True)
        if col_clear.button("清空输入与文件", use_container_width=True):
            st.session_state.prompt_text = ""
            st.session_state.doc_uploader_key += 1
            st.session_state.audio_uploader_key += 1
            st.rerun()

    with right:
        st.subheader("检测结果")
        if run:
            result = analyze(st.session_state.prompt_text)
            score = result["risk_score"]
            action = result["action"]
            st.metric("风险分数", f"{score}/100")
            st.progress(score / 100)

            if action == "拒绝":
                st.error("建议处置：拒绝")
            elif action == "二次确认":
                st.warning("建议处置：二次确认")
            else:
                st.success("建议处置：允许")

            st.write(result["summary"])

            guardrails_detail = result.get("guardrails", {"enabled": False})
            if guardrails_detail.get("enabled"):
                with st.expander("Guardrails 检测详情", expanded=False):
                    st.json(guardrails_detail)

            if result["matched_rules"]:
                st.markdown("### 命中规则")
                st.dataframe(
                    [
                        {
                            "规则": rule["name"],
                            "权重": rule["weight"],
                            "标签": ", ".join(rule["tags"]),
                            "片段": rule["snippet"],
                        }
                        for rule in result["matched_rules"]
                    ],
                    use_container_width=True,
                )
            else:
                st.info("未命中规则，可能是正常输入。")
        else:
            st.info("选择样例或输入内容后点击“运行检测”。")


if __name__ == "__main__":
    main()
