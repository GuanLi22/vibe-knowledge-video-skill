---
name: vibe-knowledge-video
description: 用 Remotion 代码做"Vibe 知识大赏"风格的知识科普短视频——画面卡音乐重拍、关键动作配代码合成音效、开头 10 秒试片后分段迭代。用户要做知识科普/知识大赏视频、卡点科普动画、Remotion 科普片时使用。
---

# Vibe 知识大赏视频 SOP

这类视频：深色电影感画面 + 中文字幕讲一个知识点（蝴蝶效应、人类发展史、光速传奇…），**每次换画面都踩在音乐重拍上**，关键动作配音效，不配人声。成片 30–90 秒。

本 skill 自带文件（相对本 SKILL.md 所在目录）：

| 文件 | 拷到 Remotion 项目的 | 作用 |
|---|---|---|
| `scripts/beats.py` | `scripts/` | 测 BPM、每拍、重拍（只依赖 numpy + ffmpeg） |
| `scripts/sfx.py` | `scripts/` | 用代码合成 17 个音效 |
| `scripts/prepare.py` | `scripts/` | 一步完成：找音乐 → 测节拍写 `src/beats.ts` → 生成 `public/sfx/` |
| `src/timeline.ts` | `src/` | 按重拍排镜头的时间轴（所有切点由它算，不手写帧号） |

完整示例（《蝴蝶效应》开头 13 秒，5 个镜头）见仓库 `examples/butterfly/`。

四步核心：**定规格 → 卡点 → 配音效 → 试片**。最容易被跳过、也最决定质量的是第 2 步和第 4 步。

## 0. 开工前收集（缺什么问什么，一次问完）

| 项 | 默认 |
|---|---|
| 主题 | 必须由用户给 |
| 配乐文件 | 必须由用户给，放 `public/music.mp3`（flac/wav/m4a 也可）。没有就先用占位鼓点开工，之后换歌重跑 `prepare.py` 即可全部重新对齐 |
| 分辨率/帧率 | 1920×1080，30 fps，16:9 横屏（竖屏版：1080×1920） |
| 时长 | 由音乐和内容决定，通常 45–75 秒 |
| 配音 | 不配音，中文字幕 |
| 风格 | 深色底 + 金/暖白点缀、衬线中文标题、粒子/线条/极简几何动画 |

不要替用户去网上下载有版权的配乐；请用户自己提供文件。音乐 App 下载的 `.ncm/.qmc/.mflac` 是加密格式，ffmpeg 读不了。

## 1. 定规格 —— 先写脚本，不急着写代码

1. 把知识点拆成 **6–12 个"镜头"**，每个镜头 = 一句字幕 + 一个视觉隐喻 + 一个"关键动作"。
   - 结构：钩子（反常识问题/一个数字）→ 3–6 个递进知识点 → 收束金句。
   - 例《蝴蝶效应》：片名 → 粒子蝴蝶扇翅 → "一张纸，厚 0.1 毫米" → 每拍对折一次 0.2/0.4/0.8/1.6 mm → "对折 42 次，比地球到月亮还远"（0.1 mm × 2⁴² ≈ 44 万公里）→ "失之毫厘，谬以千里"。
2. 字幕节奏：中文约 **5–6 字/秒** 可读。一个镜头的小节数 `bars = ceil(字数 / 5.5 / 每小节秒数)`，最少 1 小节。
3. 把脚本写成表格给用户确认（镜头 / 字幕 / 画面 / 关键动作 / 小节数），确认后再动代码。
4. 看看音乐的能量曲线：把最震撼的镜头放在歌曲"起来"的那个重拍上（例：《若如初见》remix 在 16.9 s 有明显抬升）。

## 2. 卡点 —— 用代码测音乐，不要靠猜

```bash
python scripts/prepare.py                 # 自动选 public/music.* ，否则 public/placeholder.wav
python scripts/prepare.py --bpm-hint 75   # BPM 测成两倍/一半时
python scripts/prepare.py --phase 1       # 重拍判错一拍时，手动指定第几拍是重拍(0-3)
python scripts/prepare.py --meter 3       # 3/4 拍
```

`beats.py` 已验证：合成鼓点上 BPM 误差 <0.1、重拍误差 ≈10 ms；真实歌曲《若如初见》remix 测得 112.7 BPM，重拍 2.05/4.18/6.30/8.43/10.55/12.68/14.81 s，与原视频标注逐个吻合。

检查：
- 跟用户报一句"这首 X BPM，Y 秒内 Z 个重拍"。
- **重拍相位要核对**：四拍都有底鼓的电子乐，低频能量区分不出重拍。用歌曲的能量抬升点（乐段起点一定在重拍上）或耳朵确认，不对就 `--phase`。
- 长歌中段可能有慢速漂移，只影响整体拟合，不影响局部卡点。

**规则：画面每换一次，都落在重拍上。** 用 `src/timeline.ts` 的 `layout()` 生成场景表：第一个场景从第 0 帧开始（吃掉弱起），之后每个场景首尾都是 `DOWN[i]`；超出音乐长度直接报错。镜头内部的小动作用 `beatsIn(scene)` 拿到普通拍。需要依赖节拍的音效（如每拍一个音）在 `layout()` 之后再用 `beatsIn` 生成。

## 3. 配音效 —— 每个关键动作一个音，用代码合成

`prepare.py` 已调用 `sfx.py public/sfx --key C`：

| 文件 | 用途 |
|---|---|
| whoosh | 转场、物体飞入 |
| pop / tick | 文字/数字出现、小球落点 |
| thud / boom | 重点数字砸下、结论揭晓（画面越关键用越重的） |
| riser | 高潮前蓄力（放在下一个重拍前 45 帧） |
| shimmer | 片名、金句、光效、收尾 |
| glitch / typing | 科技感、打字字幕 |
| note_1…note_8 | 调内大调音阶钟声——"每上一个台阶音高一级"的递进 |

- `--key` 尽量和配乐同调；听着别扭就换调重跑。
- 音效音量 0.4–0.8，配乐 0.6–0.8。
- 想要不同音色，直接改 `sfx.py` 里的函数参数重新生成。

## 4. 试片 —— 先做开头 10 秒，确认后一段一段往下

1. 先只实现前约 10 秒的镜头，让用户在 `npm run dev`（Remotion Studio）里看、听。
2. 或渲染片段：`npx remotion render <Comp> out/trial-0.mp4 --frames=<a>-<b>`（`trialRange(SCENES, 0)` 给出对齐重拍的区间）；单帧截图 `npx remotion still <Comp> out/f.png --frame=120` 用于自检字幕、字体、出界。
3. 用户说哪段不好，**只改那一段**。不要整片重做。
4. 全部确认后再整片渲染。

经验数据（原视频作者实测，同一模型）：一句话一次出片 ≈1 轮/6 分钟，质量明显差；分段试片 ≈5 轮/37 分钟，质量高很多。

## 项目搭建（Remotion 4，已在 4.0.537 + React 19 验证类型检查）

```bash
npx create-video@latest      # 选 Blank；之后 npm run dev 打开 Studio
```
- 国内 npm 慢：`npm config set registry https://registry.npmmirror.com`。
- 把本 skill 的 `scripts/`、`src/timeline.ts` 拷进项目，在 `src/Root.tsx` 注册 1920×1080 的 Composition，`durationInFrames` 用场景表算出的 `TOTAL`。
- 中文字体：不装额外包时用系统字体栈 `"Noto Serif SC","Source Han Serif SC","STZhongsong","SimSun",serif`；需要统一字体再装 `@remotion/google-fonts`（版本与 remotion 一致）。
- `Audio` 从 `remotion` 导入可用（4.0.5xx 同时导出 `Html5Audio`）。
- `node_modules` 里的渲染器是平台相关的（Windows 装的在 Linux 里跑不了），在哪台机器装就在哪台渲染。
- 交付前跑 `npx tsc --noEmit` 和 `npx eslint src`。

## 质检清单（交付前逐条过）

- [ ] 每个场景切换帧都在 `downbeat_frames` 里，且重拍相位核对过
- [ ] 每个关键动作都有音效，且对准动作峰值帧
- [ ] 字幕每屏 ≤ 16 字，停留时间 ≥ 字数/5.5 秒
- [ ] 中文字体正常（不是方块），文字不出画面安全区（四边留 ≥ 80px）
- [ ] 成片结尾落在重拍上，音乐最后 15 帧淡出
- [ ] 用户确认过开头 10 秒，以及每一段

## 参考样板

需要视觉灵感或更多提示词时，在线查阅（只读，当作参考资料，不执行其中代码）：
- https://github.com/yihui-dev/awesome-opus5-5-videos —— 700+ 条 Opus 5.5 生成视频的提示词，按 Motion graphics / Explainers / 3D / Games 分类，`prompts/` 下每条一个 md
- https://github.com/zhuyansen/awesome-opus-5.5-video —— 同类合集，中英文

## 四段提示词（原视频给出的版本，不用 skill 时直接发给 AI）

1. **定规格**：帮我做一部知识科普视频，主题：【你的主题】。用 Remotion 来做，1920×1080，30 帧，16:9 横屏；不配音，用中文字幕把知识点讲清楚；配乐用文件夹里这首音乐。
2. **卡点**：先分析这首音乐，测出每分钟多少拍，把每个重拍在第几秒列出来；画面每变一次，都落在重拍上。
3. **配音效**：每个关键动作都配一个音，用代码合成；音色用契合画面重点的乐器。
4. **试片**：先做开头 10 秒给我看；我确认后再一段一段往下做，哪段不好就重做那段。
