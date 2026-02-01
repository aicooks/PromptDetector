from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    description: str
    weight: int
    tags: List[str]
    patterns: List[str]


def get_rules() -> List[Rule]:
    return [
        Rule(
            id="override-system",
            name="系统指令覆盖",
            description="试图忽略或覆盖系统/开发者指令。",
            weight=25,
            tags=["injection", "override"],
            patterns=[
                r"ignore\s+(all|previous|earlier)\s+instructions",
                r"忽略.*指令",
                r"forget\s+the\s+system\s+prompt",
                r"override\s+the\s+system",
            ],
        ),
        Rule(
            id="reveal-system",
            name="系统提示泄露",
            description="试图获取系统提示或隐藏规则。",
            weight=22,
            tags=["exfiltration", "system"],
            patterns=[
                r"reveal\s+the\s+system\s+prompt",
                r"show\s+me\s+the\s+system\s+message",
                r"你的系统提示是什么",
                r"内部指令",
            ],
        ),
        Rule(
            id="policy-evasion",
            name="政策规避",
            description="请求绕过限制或提供被禁止内容。",
            weight=20,
            tags=["evasion"],
            patterns=[
                r"bypass\s+policy",
                r"without\s+restrictions",
                r"no\s+rules\s+apply",
                r"绕过.*限制",
            ],
        ),
        Rule(
            id="roleplay-dan",
            name="角色扮演越狱",
            description="使用 DAN/开发者模式等角色扮演引导越狱。",
            weight=18,
            tags=["jailbreak"],
            patterns=[
                r"DAN\b",
                r"developer\s+mode",
                r"do\s+anything\s+now",
                r"越狱模式",
            ],
        ),
        Rule(
            id="prompt-injection",
            name="提示注入",
            description="试图插入新的指令覆盖上下文。",
            weight=18,
            tags=["injection"],
            patterns=[
                r"\[\s*system\s*\]",
                r"\[\s*developer\s*\]",
                r"new\s+instructions",
                r"这里有新的指令",
            ],
        ),
        Rule(
            id="tool-abuse",
            name="工具滥用",
            description="试图滥用工具/插件执行危险操作。",
            weight=16,
            tags=["tooling"],
            patterns=[
                r"use\s+the\s+tool\s+to",
                r"call\s+the\s+plugin",
                r"run\s+shell\s+command",
                r"执行\s*命令",
            ],
        ),
        Rule(
            id="data-exfiltration",
            name="数据外泄",
            description="试图获取密钥、凭据或敏感数据。",
            weight=20,
            tags=["exfiltration"],
            patterns=[
                r"api\s*key",
                r"secret\s+token",
                r"password",
                r"/etc/passwd",
                r"数据库凭据",
            ],
        ),
        Rule(
            id="chain-of-thought",
            name="推理过程诱导",
            description="要求暴露详细推理过程或隐藏 reasoning。",
            weight=12,
            tags=["exfiltration", "policy"],
            patterns=[
                r"show\s+your\s+chain\s+of\s+thought",
                r"reveal\s+your\s+reasoning",
                r"把你的思考过程写出来",
            ],
        ),
        Rule(
            id="stealth-instruction",
            name="隐蔽指令",
            description="使用分隔符或编码隐藏攻击指令。",
            weight=14,
            tags=["injection"],
            patterns=[
                r"```.*instruction.*```",
                r"base64",
                r"\bencode\b",
                r"隐藏指令",
            ],
        ),
        Rule(
            id="social-engineering",
            name="社会工程",
            description="利用紧急/权威等话术诱导越权。",
            weight=10,
            tags=["social"],
            patterns=[
                r"urgent",
                r"as\s+your\s+admin",
                r"紧急",
                r"我是你的管理员",
            ],
        ),
        Rule(
            id="scope-escape",
            name="任务边界逃逸",
            description="要求改变任务或访问无关系统。",
            weight=12,
            tags=["override"],
            patterns=[
                r"switch\s+tasks",
                r"ignore\s+the\s+user\s+request",
                r"不再回答用户问题",
            ],
        ),
        Rule(
            id="multi-step-exploit",
            name="多步攻击引导",
            description="请求分步执行潜在攻击链。",
            weight=15,
            tags=["jailbreak"],
            patterns=[
                r"step\s+by\s+step\s+exploit",
                r"一步一步入侵",
                r"逐步越狱",
            ],
        ),
    ]
