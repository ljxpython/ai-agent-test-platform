import os
import sys

# 确保作为脚本直接运行时能找到 src 目录（用于导入 llms 等模块）
_CURR_DIR = os.path.dirname(__file__)
_SRC_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in (_SRC_DIR, _ROOT_DIR):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

import base64
import io
import mimetypes
import re
import uuid
from pathlib import Path
from typing import Any, List, Tuple

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentState,
    ModelRequest,
    ModelResponse,
    after_model,
    before_model,
    dynamic_prompt,
    wrap_model_call,
)
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.runtime import Runtime
from llms import get_default_model, get_doubao_model
from tools import (
    get_chrome_devtools_mcp_tools,
    get_chrome_mcp_tools,
    get_mcp_server_chart_tools,
    get_playwright_mcp_tools,
    get_tavily_search_tools,
    get_weather,
    get_zhipu_search_mcp_tools,
    save_test_cases_to_excel,
    toolSearch,
)


def process_attachments_in_state(state: dict) -> dict[str, Any] | None:
    """核心处理：扫描并处理消息中的附件（PDF、图片等）。

    Expected incoming user message content example (LangChain multimodal content list):
      [
        {"type": "text", "text": "总结一下"},
        {"type": "file", "source_type": "base64", "mime_type": "application/pdf", "data": "JVBERi0x...", "metadata": {"filename": "llm_course.pdf"}}
      ]

    This hook will:
      1) Decode the base64 PDF into a file.
      2) Extract text with PyMuPDF4LLM (preferred) or fallbacks.
      3) Extract page images and attach them as multimodal inputs.
      4) Replace the original file entry with the extracted text + image content parts.
    """
    # 避免打印超长 base64 内容，这里仅打印数量
    try:
        _msgs = state.get("messages", []) if hasattr(state, "get") else []
        print(f"About to call model with {len(_msgs)} messages.")
    except Exception:
        pass

    # 读取传入消息
    try:
        incoming_messages = state.get("messages", [])
    except Exception:
        return None
    if not incoming_messages:
        return None

    def _safe_filename(name: str) -> str:
        name = os.path.basename(name)
        # Remove potentially unsafe characters
        return re.sub(r"[^\w\-\.]+", "_", name)

    def _ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def _write_pdf_from_base64(data_b64: str, target_path: str) -> None:
        # Remove whitespace/newlines that may be present
        clean = re.sub(r"\s+", "", data_b64)
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(clean))

    def _extract_with_pymupdf4llm(
        pdf_path: str, images_dir: str
    ) -> Tuple[str, List[str]]:
        """优先使用 LangChain 的 PyMuPDF4LLMLoader 提取文本与图片。

        返回 (markdown_text, image_file_paths)
        """
        md_text = ""
        image_paths: List[str] = []

        # 1) 首选：官方集成包 langchain-pymupdf4llm 的加载器
        try:
            from langchain_pymupdf4llm import PyMuPDF4LLMLoader  # type: ignore

            loader = PyMuPDF4LLMLoader(
                pdf_path,
                text_kwargs={
                    "write_images": True,
                    "image_dir": images_dir,
                    "embed_images": False,
                },
            )
            docs = loader.load()
            md_text = "\n\n".join(d.page_content for d in docs)
            if os.path.isdir(images_dir):
                for fn in os.listdir(images_dir):
                    if fn.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
                    ):
                        image_paths.append(os.path.join(images_dir, fn))
            return md_text, image_paths
        except Exception:
            pass

        # 2) 次选：LangChain 社区版加载器（若存在该别名）
        try:
            from langchain_community.document_loaders import (
                PyMuPDF4LLMLoader,  # type: ignore
            )

            loader = PyMuPDF4LLMLoader(
                pdf_path,
                text_kwargs={
                    "write_images": True,
                    "image_dir": images_dir,
                    "embed_images": False,
                },
            )
            docs = loader.load()
            md_text = "\n\n".join(d.page_content for d in docs)
            if os.path.isdir(images_dir):
                for fn in os.listdir(images_dir):
                    if fn.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
                    ):
                        image_paths.append(os.path.join(images_dir, fn))
            return md_text, image_paths
        except Exception:
            pass

        # 3) 退路：直接调用底层 pymupdf4llm
        try:
            import pymupdf4llm  # type: ignore

            try:
                md_text = pymupdf4llm.to_markdown(
                    pdf_path,
                    write_images=True,
                    image_dir=images_dir,
                    embed_images=False,
                )
            except TypeError:
                md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
            if os.path.isdir(images_dir):
                for fn in os.listdir(images_dir):
                    if fn.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
                    ):
                        image_paths.append(os.path.join(images_dir, fn))
            else:
                default_dir = f"{pdf_path}-images"
                if os.path.isdir(default_dir):
                    for fn in os.listdir(default_dir):
                        if fn.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
                        ):
                            image_paths.append(os.path.join(default_dir, fn))
        except Exception:
            md_text = ""
            image_paths = []
        return md_text, image_paths

    def _extract_text_fallback_langchain(pdf_path: str) -> str:
        """Fallback to a generic PyMuPDF loader via LangChain if available."""
        text = ""
        try:
            # Community loader (text only)
            from langchain_community.document_loaders import (
                PyMuPDFLoader,  # type: ignore
            )

            docs = PyMuPDFLoader(pdf_path).load()
            text = "\n\n".join(d.page_content for d in docs)
        except Exception:
            pass
        return text

    def _extract_images_fallback_pymupdf(pdf_path: str, images_dir: str) -> List[str]:
        """Fallback image extraction using PyMuPDF directly if available."""
        paths: List[str] = []
        try:
            import fitz  # type: ignore

            doc = fitz.open(pdf_path)
            _ensure_dir(images_dir)
            for page_index in range(len(doc)):
                page = doc[page_index]
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    out_path = os.path.join(
                        images_dir, f"page{page_index+1}_img{img_index+1}.png"
                    )
                    if pix.n < 5:
                        pix.save(out_path)
                    else:
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        pix1.save(out_path)
                        pix1 = None  # type: ignore
                    pix = None  # type: ignore
                    paths.append(out_path)
            doc.close()
        except Exception:
            paths = []
        return paths

    def _file_to_data_uri(path: str) -> str:
        mime = "image/png"
        lower = path.lower()
        if lower.endswith(".jpg") or lower.endswith(".jpeg"):
            mime = "image/jpeg"
        elif lower.endswith(".webp"):
            mime = "image/webp"
        elif lower.endswith(".gif"):
            mime = "image/gif"
        elif lower.endswith(".bmp"):
            mime = "image/bmp"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    updated_messages = []
    changed = False

    def _sanitize_blocks(blocks: list) -> list:
        """仅保留模型支持的块结构，清理多余字段。
        - text: 保留 {type,text}
        - image_url: 保留 {type,image_url:{url}}
        - video_url: 保留 {type,video_url:{url}}（目前不生成，仅兜底）
        其它类型全部丢弃。
        """
        sanitized = []
        for blk in blocks:
            if not isinstance(blk, dict):
                continue
            t = blk.get("type")
            if t == "text" and isinstance(blk.get("text"), str):
                sanitized.append({"type": "text", "text": blk.get("text")})
            elif t == "image_url" and isinstance(blk.get("image_url"), dict):
                url = blk["image_url"].get("url")
                if isinstance(url, str) and url:
                    sanitized.append({"type": "image_url", "image_url": {"url": url}})
            elif t == "video_url" and isinstance(blk.get("video_url"), dict):
                url = blk["video_url"].get("url")
                if isinstance(url, str) and url:
                    sanitized.append({"type": "video_url", "video_url": {"url": url}})
        return sanitized

    # 根据你的要求：仅当出现 PDF 时做提取；否则保持原始消息

    for msg in incoming_messages:
        is_human = (HumanMessage is None) or isinstance(msg, HumanMessage)
        content = getattr(msg, "content", None)

        if not is_human or not isinstance(content, list):
            # Keep as-is
            updated_messages.append(msg)
            continue

        # Prepare new content list for this human message
        new_content_parts = []
        pdf_found = False

        # 仅当存在 PDF 文件时做处理；否则保持原始内容
        pdf_items = []
        for part in content:
            if not isinstance(part, dict):
                new_content_parts.append(part)
                continue

            if part.get("type") == "file":
                # 判断是否为 PDF Base64（支持 data/base64 两种字段，或 data: URL）
                mime = str(part.get("mime_type") or part.get("mimeType") or "").lower()
                raw_b64 = None
                data_val = (
                    part.get("data") if isinstance(part.get("data"), str) else None
                )
                is_data_url = False
                if isinstance(data_val, str):
                    if data_val.startswith("data:") and "," in data_val:
                        is_data_url = True
                        try:
                            raw_b64 = data_val.split(",", 1)[1]
                            mime_hdr = data_val.split(",", 1)[0]
                            if ":" in mime_hdr:
                                mime = mime_hdr.split(":", 1)[1].split(";", 1)[0]
                        except Exception:
                            raw_b64 = None
                    else:
                        raw_b64 = data_val
                elif isinstance(part.get("base64"), str):
                    raw_b64 = part.get("base64")

                if mime.startswith("application/pdf") and raw_b64:
                    pdf_items.append(
                        {
                            "raw_b64": raw_b64,
                            "meta": part.get("metadata") or {},
                        }
                    )
                    # 不把原始 file 块加入 new_content_parts，避免 400
                    continue

                # 若是图片类型且有 base64，则转为 image_url
                if mime.startswith("image/") and raw_b64:
                    try:
                        if is_data_url and isinstance(data_val, str):
                            data_uri = data_val
                        else:
                            data_uri = f"data:{mime};base64,{raw_b64}"
                        new_content_parts.append(
                            {"type": "image_url", "image_url": {"url": data_uri}}
                        )
                        changed = True
                        continue
                    except Exception:
                        pass

                # 其它文件类型：替换成说明性文本
                meta = part.get("metadata") or {}
                fname = meta.get("filename") or meta.get("name") or "未命名文件"
                new_content_parts.append(
                    {
                        "type": "text",
                        "text": f"收到文件: {fname} ({mime or '未知类型'})。模型不直接接收文件，已忽略原始文件内容。",
                    }
                )
                changed = True
            else:
                # 其它类型一律保持
                new_content_parts.append(part)

        if not pdf_items:
            # 不包含 PDF：返回清理后的消息（无 file 类型, 清理多余字段）
            cleaned = _sanitize_blocks(new_content_parts)
            try:
                if HumanMessage is not None:
                    new_msg = HumanMessage(content=cleaned)
                else:
                    msg.content = cleaned  # type: ignore
                    new_msg = msg
            except Exception:
                new_msg = msg
            updated_messages.append(new_msg)
            continue

        # Process each PDF file
        uploads_root = os.path.join(os.getcwd(), "data", "uploads")
        _ensure_dir(uploads_root)

        all_images: List[str] = []
        accumulated_texts: List[str] = []

        for file_part in pdf_items:
            pdf_found = True
            raw_b64 = file_part.get("raw_b64") or ""
            meta = file_part.get("meta") or {}
            original_name = _safe_filename(meta.get("filename") or "upload.pdf")

            unique_id = uuid.uuid4().hex[:8]
            pdf_path = os.path.join(uploads_root, f"{unique_id}_{original_name}")
            images_dir = os.path.join(
                uploads_root,
                f"{os.path.splitext(os.path.basename(pdf_path))[0]}_images",
            )

            try:
                _write_pdf_from_base64(raw_b64, pdf_path)
            except Exception as e:
                # If decoding fails, skip this file but keep the message text
                accumulated_texts.append(f"[PDF 解码失败: {original_name} — {e}]")
                continue

            # Preferred: extract via pymupdf4llm
            md_text, image_paths = _extract_with_pymupdf4llm(pdf_path, images_dir)

            # Fallbacks if needed
            if not md_text:
                md_text = _extract_text_fallback_langchain(pdf_path)
            if not image_paths:
                image_paths = _extract_images_fallback_pymupdf(pdf_path, images_dir)

            if md_text:
                accumulated_texts.append(md_text)
            if image_paths:
                all_images.extend(image_paths)

        if pdf_found:
            changed = True
            # Insert extracted text as a text part
            final_text = "\n\n".join(accumulated_texts).strip()
            if final_text:
                # Optionally truncate to avoid extremely large prompts
                max_chars = 150_000  # generous cap
                if len(final_text) > max_chars:
                    final_text = final_text[:max_chars] + "\n\n[内容过长，已截断]"
                new_content_parts.append(
                    {
                        "type": "text",
                        "text": f"以下为PDF提取内容（含Markdown）：\n\n{final_text}",
                    }
                )

            # Attach images as multimodal inputs (data URLs)
            # Limit count to prevent excessive token usage
            max_images = 24
            for img_path in all_images[:max_images]:
                try:
                    data_uri = _file_to_data_uri(img_path)
                    new_content_parts.append(
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    )
                except Exception:
                    continue

            # 移除所有 file 类型块，并做最终清洗（仅保留 text/image_url/video_url 标准字段）
            new_content_parts = [
                blk
                for blk in new_content_parts
                if not (isinstance(blk, dict) and blk.get("type") == "file")
            ]
            new_content_parts = _sanitize_blocks(new_content_parts)

            # Recreate the message with updated content
            try:
                if HumanMessage is not None:
                    new_msg = HumanMessage(content=new_content_parts)
                else:
                    # Fallback: attempt to mutate in-place structure
                    msg.content = new_content_parts  # type: ignore
                    new_msg = msg
            except Exception:
                new_msg = msg
            updated_messages.append(new_msg)
        else:
            updated_messages.append(msg)

    if changed:
        state["messages"][-1].content = updated_messages[-1].content
        # 返回覆盖后的 messages，确保发送给模型的不含 file 块
        print(
            f"Processed attachments. Using cleaned messages: {len(updated_messages)} items."
        )
        return state

    # 无 PDF，原样返回
    return None


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Intercept messages to process uploaded PDF content from base64.
    仅作包装器，调用核心处理函数。
    """
    # 避免打印超长 base64 内容，这里仅打印数量
    try:
        _msgs = state.get("messages", []) if hasattr(state, "get") else []
        print(f"About to call model with {len(_msgs)} messages.")
    except Exception:
        pass
    return process_attachments_in_state(state)  # 委托核心处理


model = get_doubao_model()

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
    middleware=[log_before_model],
)


def file_to_base64_block(file_path: str) -> dict:
    """将本地文件转为前端使用的 base64 文件块。

    返回结构示例：
    {
      'type': 'file',
      'source_type': 'base64',
      'mime_type': 'application/pdf',
      'data': 'JVBERi0xLjc...',
      'metadata': {'filename': 'xxx.pdf'}
    }
    """
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    mime, _ = mimetypes.guess_type(str(p))
    if not mime:
        # 兜底处理常见扩展名
        suf = p.suffix.lower()
        if suf == ".pdf":
            mime = "application/pdf"
        elif suf in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif suf == ".png":
            mime = "image/png"
        elif suf == ".webp":
            mime = "image/webp"
        elif suf == ".gif":
            mime = "image/gif"
        else:
            mime = "application/octet-stream"

    with open(p, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 按你的要求：图片 → image_url(data URI)，PDF → file(base64)
    if mime.startswith("image/"):
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{data_b64}",
                "metadata": {"name": p.name},
            },
        }

    if mime == "application/pdf":
        return {
            "type": "file",
            "source_type": "base64",
            "mime_type": mime,
            "data": data_b64,
            "metadata": {"filename": p.name},
        }

    # 其他类型：按文件块返回，便于后续中间件或前端自行处理
    return {
        "type": "file",
        "source_type": "base64",
        "mime_type": mime,
        "data": data_b64,
        "metadata": {"filename": p.name},
    }


if __name__ == "__main__":
    # # 自测：构造一个包含文本 + PDF(base64) + 图片(base64) 的 HumanMessage
    # test_pdf = os.path.join(os.path.dirname(__file__), "滴滴出行行程报销单.pdf")
    # test_img = os.path.join(os.path.dirname(__file__), "6e4b5457aba12bcd507361d9d20d5914.jpeg")
    #
    # content_blocks = [{"type": "text", "text": "总结一下这份材料里的要点，并识别图片中的关键信息。"}]
    #
    # try:
    #     content_blocks.append(file_to_base64_block(test_pdf))
    #     print(f"已加载 PDF: {test_pdf}")
    # except Exception as e:
    #     print(f"PDF 自测文件不可用: {e}")
    #
    # try:
    #     content_blocks.append(file_to_base64_block(test_img))
    #     print(f"已加载 图片: {test_img}")
    # except Exception as e:
    #     print(f"图片 自测文件不可用: {e}")
    #
    # messages = [HumanMessage(content=content_blocks)]
    # print("自测：即将发送的原始消息内容块（不含二进制，仅结构）：")
    # response = agent.invoke({"messages": messages})
    # print("自测：模型返回的消息（中间件已完成解析后送入模型）")
    # for i in response["messages"]:
    #     i.pretty_print()
    pass
