# vibe-knowledge-video

一个 Claude skill：用 [Remotion](https://www.remotion.dev/) 代码做 **"Vibe 知识大赏"** 风格的知识科普短视频——深色电影感画面、中文字幕、**每次切画面都踩在音乐重拍上**、每个关键动作配一个代码合成的音效。

> A Claude skill for making beat-synced, code-generated science explainer videos (Chinese subtitles, cinematic dark style) with Remotion.

## 四步 SOP

| 步骤 | 做什么 | 工具 |
|---|---|---|
| 1 定规格 | 主题拆成 6–12 个镜头，按字数算每个镜头占几小节 | — |
| 2 卡点 | 测 BPM 和每个重拍的秒数/帧号，镜头切点全部落在重拍 | `scripts/beats.py`、`src/timeline.ts` |
| 3 配音效 | 每个关键动作一个音，用代码合成 | `scripts/sfx.py` |
| 4 试片 | 先做开头 10 秒，确认后一段一段往下，哪段不好只改哪段 | Remotion Studio |

详细流程见 [`vibe-knowledge-video/SKILL.md`](vibe-knowledge-video/SKILL.md)。

## 安装

**Claude Code**：把 `vibe-knowledge-video/` 文件夹复制到 `~/.claude/skills/`（或项目的 `.claude/skills/`）。

**claude.ai**：把 `vibe-knowledge-video/` 打包成 zip，在 claude.ai 的 Skills 设置里上传。

然后对 Claude 说："帮我做一条【主题】的知识大赏视频，配乐是 public/music.mp3"。

## 不用 Claude 也能用的脚本

```bash
npx create-video@latest            # 选 Blank
cp -r vibe-knowledge-video/scripts my-video/ && cp vibe-knowledge-video/src/timeline.ts my-video/src/
cd my-video && python scripts/prepare.py   # 需要 Python3 + numpy + ffmpeg
npm run dev
```

`prepare.py` 会：找到 `public/music.*` → 测节拍写入 `src/beats.ts` → 合成 17 个音效到 `public/sfx/`。

- BPM 测成两倍/一半：`--bpm-hint 75`
- 重拍判错一拍：`--phase 0..3`
- 3/4 拍：`--meter 3`

## 示例

[`examples/butterfly/`](examples/butterfly/)：《蝴蝶效应》开头 13 秒（片名 → 粒子蝴蝶 → 0.1 mm 的纸 → 每拍对折一次 → 对折 42 次到月球），5 个镜头全部卡在重拍上。配乐请自备（仓库不含任何音乐文件）。

## 致谢

方法来自抖音创作者 **小冯不意why（@nowhy_feng）** 的教程视频，"四段提示词"为其原文。本仓库把这套方法整理成 SOP，并补上了可运行的节拍检测、音效合成和时间轴代码。

## License

MIT
