# vibe-knowledge-video

一个 Claude skill：用 [Remotion](https://www.remotion.dev/) 代码做 **"Vibe 知识大赏"** 风格的知识科普短视频——深色电影感画面、中文字幕、**每次切画面都踩在音乐重拍上**、每个关键动作配一个代码合成的音效，还能**用代码原创配乐**。

> A Claude skill for making beat-synced, code-generated science explainer videos (Chinese subtitles, cinematic dark style) with Remotion — including original, code-composed background music.

## 流程

| 步骤 | 做什么 | 工具 |
|---|---|---|
| 0 选题与事实 | 选题三问；建 facts.md，每个数字有出处 | — |
| 1 定规格 | 拆镜头，按字数算每个镜头占几小节；定视觉语言 | — |
| 2 卡点 | 测 BPM 和重拍，镜头切点全部落在重拍 | `scripts/prepare.py`、`src/timeline.ts` |
| 配乐 | 自己的曲子 / AI 生成（Suno、海绵音乐、ElevenLabs）/ **代码原创** | `scripts/compose.py` |
| 3 配音效 | 每个关键动作一个音，用代码合成 | `scripts/sfx.py` |
| 4 试片 | 先做开头 10 秒，确认后一段一段往下 | Remotion Studio |
| 5 成片质检 | 规格、bt709、响度 -14 LUFS、亮度、静帧、缩略图总览 | `scripts/qa.py` |
| 6 发布包 | 标题、简介（含出处）、标签、单独封面 | — |

详细流程见 [`vibe-knowledge-video/SKILL.md`](vibe-knowledge-video/SKILL.md)。

## 安装

**Claude Code**：把 `vibe-knowledge-video/` 文件夹复制到 `~/.claude/skills/`（或项目的 `.claude/skills/`）。

**claude.ai**：把 `vibe-knowledge-video/` 打包成 zip，在 claude.ai 的 Skills 设置里上传。

然后对 Claude 说："帮我做一条【主题】的知识大赏视频，配乐是 public/music.mp3"（或"配乐你原创一首"）。

## 不用 Claude 也能用的脚本

需要 Python3 + numpy + ffmpeg。

```bash
npx create-video@latest            # 选 Blank
cp -r vibe-knowledge-video/scripts my-video/ && cp vibe-knowledge-video/src/timeline.ts my-video/src/
cd my-video

# 配乐二选一：
#   a) 自备曲子放 public/music.mp3
#   b) 代码原创（每个 seed 一首新曲，drop 落在第 8 小节）
python scripts/compose.py public/music.wav --bpm 112 --bars 24 --drop 8 --key A --mode minor --seed 7

python scripts/prepare.py          # 写 src/beats.ts + 生成 public/sfx/
npm run dev

# 渲染后质检
npx remotion render <CompId> out/final.mp4 --codec=h264 --color-space=bt709
python scripts/qa.py out/final.mp4 --sheet out/contact_sheet.jpg
```

- BPM 测成两倍/一半：`prepare.py --bpm-hint 75`；重拍判错一拍：`--phase 0..3`；3/4 拍：`--meter 3`
- `compose.py` 会同时写出 `public/music.grid.json`，`prepare.py` 看到它就直接用精确节拍网格，不再检测；换成别的曲子时删掉它
- 安静版配乐：`compose.py ... --bpm 77 --mode major --style calm`

## 示例

[`examples/butterfly/`](examples/butterfly/)：《蝴蝶效应》开头 13 秒（片名 → 粒子蝴蝶 → 0.1 mm 的纸 → 每拍对折一次 → 对折 42 次到月球），5 个镜头全部卡在重拍上。配乐请自备或用 `compose.py` 生成（仓库不含任何音乐文件）。

## 更新记录

- **v5**：`compose.py` 代码原创配乐（seed 换曲、drop 精确对齐、-14 LUFS）；`prepare.py` 支持 `.grid.json` 精确网格；配乐三条路线（自备 / AI 生成 / 代码原创）
- **v4**：`qa.py` 成片质检；选题与事实核查（facts.md）；视觉语言、无旁白文案规则、发布包
- **v1**：四步 SOP + 节拍检测、音效合成、时间轴

## 致谢

方法来自抖音创作者 **小冯不意why（@nowhy_feng）** 的教程视频，"四段提示词"为其原文。本仓库把这套方法整理成 SOP，并补上了可运行的节拍检测、音效合成、原创配乐、成片质检和时间轴代码。

## License

MIT
