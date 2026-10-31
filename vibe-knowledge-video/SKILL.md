---
name: vibe-knowledge-video
description: 用 Remotion 代码做"Vibe 知识大赏"风格的知识科普短视频——画面卡音乐重拍、关键动作配代码合成音效、可代码原创配乐、开头 10 秒试片后分段迭代。用户要做知识科普/知识大赏视频、卡点科普动画、Remotion 科普片时使用。
---

# Vibe 知识大赏视频 SOP

这类视频：深色电影感画面 + 中文字幕讲一个知识点（蝴蝶效应、人类发展史、光速传奇…），**每次换画面都踩在音乐重拍上**，关键动作配音效，不配人声。

本 skill 自带文件（相对本 SKILL.md 所在目录）：

| 文件 | 拷到 Remotion 项目的 | 作用 |
|---|---|---|
| `scripts/beats.py` | `scripts/` | 测 BPM、每拍、重拍（只依赖 numpy + ffmpeg） |
| `scripts/sfx.py` | `scripts/` | 用代码合成 17 个音效 |
| `scripts/prepare.py` | `scripts/` | 一步完成：找音乐 → 写 `src/beats.ts`（有 `.grid.json` 就用精确网格）→ 生成 `public/sfx/` |
| `scripts/compose.py` | `scripts/` | 代码原创配乐：每个 seed 一首新曲，drop 精确落在指定小节，-14 LUFS |
| `scripts/qa.py` | `scripts/` | 成片质检：规格、色彩标注、音轨、响度、亮度、静帧 + 缩略图总览 |
| `src/timeline.ts` | `src/` | 按重拍排镜头的时间轴（所有切点由它算，不手写帧号） |

完整示例（《蝴蝶效应》开头 13 秒，5 个镜头）见仓库 `examples/butterfly/`。

流程：**选题与事实 → 定规格 → 卡点 → 配音效 → 试片 → 成片质检 → 发布包**。最容易被跳过、也最决定质量的是事实核查、卡点和试片。

## 0. 开工前收集（缺什么问什么，一次问完）

| 项 | 默认 |
|---|---|
| 主题 | 必须由用户给 |
| 时长 | **短版 45–75 s**（单一论点的卡点片）或 **标准版 130–160 s**（原片规格：爆款原片实测 2:00–2:45）。用户没说就问 |
| 配乐文件 | 放 `public/music.mp3`（flac/wav/m4a 也可）。没有就先用占位鼓点 `public/placeholder.wav` 开工，换歌后重跑 `prepare.py` 全部重新对齐。也可以走下文「配乐」：AI 生成，或用 `compose.py` 代码原创（每片换 seed，不撞常见曲库） |
| 分辨率/帧率 | 1920×1080，30 fps，16:9 横屏（竖屏版：1080×1920） |
| 配音 | 不配音，中文（可中英双语）字幕 |
| 风格 | 深蓝黑底（原片实测 #0A0A1E）+ 金/暖白点缀、衬线中文、粒子/线条/极简几何；或从「参考样板」里换一种 |

不要替用户去网上下载有版权的配乐；请用户自己提供文件。音乐 App 下载的 `.ncm/.qmc/.mflac` 是加密格式，ffmpeg 读不了。

## 0.5 选题与事实 —— 先算后写

**选题三问**（答不上就换题或换切入点）：
1. 3 秒内能不能让人先猜 / 先选 / 先代入？（例：“从小到大，你被打过多少次分？”）
2. 有没有一个**贯穿全片的道具/主角**？（例：一粒叫“你”的暖光、一张被对折的纸）
3. 有没有**反转**？

**facts.md**：写脚本前先建事实表，每个数字、人名、年份、引文一行：`事实 | 原始出处（论文/机构/链接）| 适用范围（如"仅美国数据"）`。
- **取不到数值就不写**；屏幕上的计数器必须是算出来的真值（例：0.1 mm × 2⁴² ≈ 439,804 km，用代码算）。
- 出处有分歧就并列两种说法；转述观点不加引号，只有原话才加。
- 历史复原图、示意动画标注「示意图」。
- **每条证据都要和主旨方向一致**：加一条数据前，把前后字幕连读一遍，确认它支撑的是你的结论而不是反方（反例：片子批评"唱分数论"，却用"同分不同录取率"做证据——这其实在为分数辩护）。敏感话题（家境、地域…）用户不想碰就整段删，用一个不依赖数据的类比补上推理缺口。
- 专业术语（零和/正和、古德哈特定律…）不进字幕主句，换成大白话（"排名有名额，变好没有"），术语最多做小字标注。

## 1. 定规格 —— 先写脚本，不急着写代码

0. 先看下文「参考样板」，选定视觉风格（告诉用户参考了哪个）。
1. **叙事结构**
   - 短版：钩子 → 定义 → 让步（先承认对方的合理性）→ 转折（放在音乐能量抬升的重拍上）→ 论证 → 立论 → 落点金句。
   - 标准版（原片六段式）：冷开场钩子 → 历史锚点（真实文献复原）→ 机制模拟动画 → 反直觉转折 → 现实落地 → 引文与声明收尾。
   - 每个主题重新设计叙事形式：侦探查案、尺度旅行、拆解、闯关、两难选择、猜谜……只有品牌风格和配乐固定。
   - 情绪曲线要有起伏：先压后放。想让人"看完被鼓励"，前半段就要有压抑感，释放留给结尾。
2. 拆成镜头：每个镜头 = 一句字幕 + 一个视觉隐喻 + 一个"关键动作"。短版 6–14 个，标准版 30–45 个功能拍。
   - 例《蝴蝶效应》：片名 → 粒子蝴蝶扇翅 → "一张纸，厚 0.1 毫米" → 每拍对折一次 → "对折 42 次，比地球到月亮还远" → "失之毫厘，谬以千里"。
3. **无旁白文案规则**（文字是唯一信息通道）：
   - 核心句一句都不能丢；一屏一个中心意思，辅助信息降为小字标注而不是删掉。
   - 1080p 下正文 ≥ 52 px、标注 ≥ 28 px；腾地方靠把旧文字调暗，不靠缩字。
   - 阅读时间：中文约 5–6 字/秒，每行至少停留约 2.2 s（含 0.8–1.0 s 入场）。一个镜头的小节数 `bars = ceil(字数 / 5.5 / 每小节秒数)`，最少 1 小节。
   - 约五分之一的句子故意不配画面，留白当呼吸；全片至少一处放慢的"喘息镜头"。
4. 把脚本写成表格给用户确认（镜头 / 字幕 / 画面 / 关键动作 / 小节数 / 论证作用），并把全部字幕连成一段话读一遍，检查自洽。确认后再动代码。
5. 看音乐能量曲线：把最震撼的镜头放在歌曲"起来"的那个重拍上（例：《若如初见》remix 在 16.9 s 有明显抬升）。

**视觉语言（比特效更重要）**：用户说"素"、"不惊艳"时，问题通常不在特效不够，而在"每镜各画各的图标拼盘"。更有效的做法：
- 全片一套连续的素材（如同一片光粒子在重拍上变形成文字/人群/尺子/笼子），一镜到底，用素材自身做转场。
- 用**两种质感映射论点两方**（例：暖金、自由流动、会呼吸的圆粒子 = 优秀/成长；冷白、吸附网格、静止的方像素 = 分数/排名），不用解释观众就懂。
- 给观众一个代入对象（主角/道具），让它全程受压、最后解放——这是"看完被鼓励"的来源。
- 画面主体占画面高度 ≥ 1/3；主体不压字幕带（底部约 85–91% 高度）。
- 运镜至少 4 种（推、拉、重拍瞬间推近+衰减震动、荷兰角、平移）；动作有预备-动作-回弹；关键重击用横向镜头光晕、闪白、色散；金属字 + 扫光；数字先乱码再从右往左锁定。
- 价值观类主题结尾落在人文关怀上。

## 2. 卡点 —— 用代码测音乐，不要靠猜

```bash
python scripts/prepare.py                 # 自动选 public/music.* ，否则 public/placeholder.wav
python scripts/prepare.py --bpm-hint 75   # BPM 测成两倍/一半时
python scripts/prepare.py --phase 1       # 重拍判错一拍时，手动指定第几拍是重拍(0-3)
python scripts/prepare.py --meter 3       # 3/4 拍
```

配乐是 `compose.py` 原创的（`public/music.grid.json` 存在）时，`prepare.py` 直接用精确网格，以下检测相关的检查都可跳过。

`prepare.py` 写出 `src/beats.ts`（字段：`bpm`、`beats_s`/`beat_frames`、`downbeats_s`/`downbeat_frames`、`accents_s`、`bpm_alternatives`、`audio`）并生成 `public/sfx/`。

`beats.py` 已验证：合成鼓点上 BPM 误差 <0.1、重拍误差 ≈10 ms；真实歌曲《若如初见》remix 测得 112.7 BPM，重拍 2.05/4.18/6.30/8.43/10.55/12.68/14.81 s，与原视频标注逐个吻合。

检查：
- 跟用户报一句"这首 X BPM，Y 秒内 Z 个重拍"。
- **重拍相位要核对**：四拍都有底鼓的电子乐，低频能量区分不出重拍。用歌曲的能量抬升点（乐段起点一定在重拍上）或耳朵确认，不对就 `--phase`。
- 长歌中段可能有慢速漂移，只影响整体拟合，不影响局部卡点。
- 音乐恰好从第 0 秒起拍时首拍可能漏检，不影响（时间轴从第 0 帧开始）。

**规则：画面每换一次，都落在重拍上；但不是每个重拍都要切。** 一个动作、一个声音、一次切，留时间看。用 `src/timeline.ts` 的 `layout()` 生成场景表，不要手写帧号：第一个场景从第 0 帧开始（吃掉弱起），之后每个场景首尾都是 `DOWN[i]`；超出音乐长度直接报错。镜头内部的小动作用 `beatsIn(scene)` 拿到普通拍。依赖节拍的音效在 `layout()` 之后再用 `beatsIn` 生成。大瞬间（爆炸、揭晓、唯一的全彩镜头）对准歌曲 drop。

## 3. 配音效 —— 每个关键动作一个音，用代码合成

`prepare.py` 已调用 `sfx.py public/sfx --key C`（纯 numpy，0.2 秒出 17 个 wav）：

| 文件 | 用途 |
|---|---|
| whoosh | 转场、物体飞入 |
| pop / tick | 文字/数字出现、小球落点 |
| thud / boom | 重点数字砸下、结论揭晓（画面越关键用越重的） |
| riser | 高潮前蓄力（放在下一个重拍前 45 帧） |
| shimmer | 片名、金句、光效、收尾 |
| glitch / typing | 科技感、打字字幕 |
| note_1…note_8 | 调内大调音阶钟声——"每上一个台阶音高一级"的递进 |

- `--key` 尽量和配乐同调；听着别扭就换调重跑 `prepare.py --key G` 等。想要不同音色，直接改 `sfx.py` 参数；想要真实拟音可用 CC0 素材库（如 Kenney）。
- **声音只标记动作和强调**：同一时刻最多 2 个音效；全片峰值重音只用 3 次左右；静音观看也必须看得懂。
- 音效音量 0.4–0.8，配乐 0.6–0.8；重拍上同时有鼓点时音效收一点。
- 音乐不要淡出到全静音再接（持续低音会断），用 60–150 ms 交叉淡入淡出。
- 用手机 + 耳机听一遍：听得到的高频嘶声就是问题。

## 配乐 —— 三条路线

常见曲库配乐大家都听腻了。开工时问用户选哪条（默认按下表推荐）：

| 路线 | 什么时候用 | 做法 |
|---|---|---|
| A. 用户自己的曲子 | 已有固定"账号曲" | 放 `public/music.*` → `prepare.py` 测节拍 |
| B. **AI 生成（日常推荐）** | 要"像真歌"的质感 | 用下方八段公式写提示词 → **Suno** 或 **海绵音乐/豆包**（中文提示词）生成 → 下载放 `public/music.mp3` → `prepare.py` 测节拍 |
| B+. ElevenLabs Music | 更在意**画面和音乐结构严丝合缝** | 用 composition plan 按秒指定每段（intro/build/drop/outro）时长，drop 秒数 = 片子高潮镜头的起点 |
| C. **代码原创（本地、免费、独一份）** | 想要谁都没听过的配乐；或片子先定、音乐后配 | `compose.py` 直接写谱合成，重拍网格精确，见下 |

### C. compose.py 原创配乐

```bash
python scripts/compose.py public/music.wav --bpm 112 --bars 24 --drop 8 --key A --mode minor --seed 7            # 卡点版
python scripts/compose.py public/music.wav --bpm 77  --bars 16 --drop 6 --key D --mode major --seed 5 --style calm # 安静版
python scripts/prepare.py   # 自动读取 public/music.grid.json，用精确网格，不再检测（输出带 "(grid)"）
```
- 结构：intro（pad）→ build（琶音 + riser）→ **drop 在第 `--drop` 小节的重拍上**（鼓、贝斯、主动机进来）→ 最后 2 小节收束回主和弦。
- **先定片子再写谱**：`--bars` = 脚本总小节数 + 1；`--drop` = 高潮/转折镜头所在小节（`layout()` 里它前面所有镜头 bars 之和）。时长 ≈ bars × 240 / BPM 秒。
- **每条片子换一个 `--seed`**（和声进行、动机、节奏型、琶音顺序都会变）；同一个账号想要统一"声音品牌"就固定 key/mode/style 只换 seed。多生成 2–3 个 seed 发给用户试听再定。
- 情绪：小调 = 克制/悬念，大调 = 温暖/鼓励；`pulse` 适合卡点，`calm` 适合沉思/喘息。
- 输出已做两步响度归一到 -14 LUFS、真峰值 ≤ -1.5 dBTP，并写出 `music.grid.json`（bpm、bars、drop_s 等）。换歌时记得删掉旧的 `.grid.json`，否则 prepare.py 会继续用旧网格。
- 局限：合成音色偏电子氛围，不是真乐器录音；要"像真歌"走路线 B。

**配乐提示词八段公式**（路线 B/B+）：用途画面 / 时长 / 情绪 / 调性 / 速度拍子 / 乐器 / 结构和时间点 / 负面清单。情绪影响从大到小：调式（大/小调）→ BPM → 音区与力度 → 断奏/连奏 → 音色。知识大赏型参考：
> 无旁白知识短片，{时长} 秒；前段克制悬念、转折处打开、结尾温暖有力量；小调起、结尾转关系大调；安静版 76–78 BPM（原片实测）、卡点版 105–120 BPM；合成器 pad + 钢琴 + 细碎琶音；第 {转折秒数} 秒一个 drop；4/4 拍、重拍清晰；不要人声、不要主旋律抢戏、不要突然的鼓点。

AI 生成的曲子同样要核对重拍相位（drop 一定落在重拍上，用它校准 `--phase`）。响度目标：整轨约 -14 LUFS（抖音/B 站常用），真峰值 ≤ -1 dBTP；由 `qa.py` 检查。AI 生成内容使用前确认平台的商用授权条款（免费档常不含商用）。

## 4. 试片 —— 先做开头，确认后一段一段往下

1. 先做一屏原型（或前约 10–20 秒），让用户在 `npm run dev`（Remotion Studio）里看、听；风格确认前不铺开全片。
2. 或渲染片段：`npx remotion render <CompId> out/trial-0.mp4 --frames=<a>-<b>`（`trialRange(SCENES, 0)` 给出对齐重拍的区间）；单帧截图 `npx remotion still <CompId> out/f.png --frame=120` 用于自检。
3. 自检单帧：在 Studio 页面里可用 `window.remotion_setFrame(frame, 'CompId')` 跳帧后截图，比点时间轴可靠。
4. 用户说哪段不好，**只改那一段**。用户说整体方向不对时，另建一个 Composition 重做，保留旧版方便对比。
5. 全部确认后再整片渲染：`npx remotion render <CompId> out/final.mp4 --codec=h264 --color-space=bt709`。

经验数据（原视频作者实测，同一模型）：一句话一次出片 ≈1 轮/6 分钟，质量明显差；分段试片 ≈5 轮/37 分钟，质量高很多。

## 5. 成片质检 —— 不过不出门

```bash
python scripts/qa.py out/final.mp4 --sheet out/contact_sheet.jpg
```

| 关卡 | 标准 | 为什么 |
|---|---|---|
| specs | 1920×1080 / 30 fps / yuv420p / H.264 | 平台兼容 |
| color | primaries/transfer/matrix 都是 bt709 | 未标注在手机上可能显得暗一半 |
| audio | AAC，音轨长度 = 视频长度 | 无声/短一截会被当作未完成 |
| loudness | ≈ -14 LUFS（±1.5），真峰值 ≤ -1 dBTP | 平台响度标准 |
| brightness | 平均亮度 YAVG 30–60，任何 1 秒窗口 ≥ 25 | 近黑画面 + 细光线容易被判低质量限流；深色风格尤其要查 |
| freeze | 无 ≥ 2 s 的静止段（故意留白除外） | 防止动画卡住 |

脚本对每个失败项给出修复命令（重标色彩、`loudnorm` 响度归一化、提亮建议），并输出 24 帧缩略图总览，一眼看全片。另外人工过一遍：
- [ ] 每个场景切换帧都在 `downbeat_frames` 里，且重拍相位核对过
- [ ] 每个关键动作都有音效，且对准动作峰值帧
- [ ] 字幕停留时间够，屏上文字和 facts.md 一致
- [ ] 中文字体正常（不是方块），文字不出安全区（四边留 ≥ 80px）
- [ ] tsc / eslint 通过
- [ ] 用户确认过开头，以及每一段

## 6. 发布包

标题（问句或数字）、简介（含数据出处）、话题标签、**单独的**封面图（封面不要嵌进视频开头，会把音画同步推偏）。封面文字在最终像素上核对。先发布，再根据真实反馈改具体句子。

## 项目搭建（Remotion 4，已在 4.0.537 + React 19 通过 tsc/eslint）

```bash
npx create-video@latest      # 选 Blank；之后 npm run dev 打开 Studio
```
- 国内 npm 慢：`npm config set registry https://registry.npmmirror.com`。
- 把 `scripts/`、`src/timeline.ts` 放进项目，在 `src/Root.tsx` 注册 1920×1080 的 Composition，`durationInFrames` 用场景表算出的 `TOTAL`（在场景文件里算，避免循环引用）。
- 中文字体：不装额外包时用系统字体栈 `"Noto Serif SC","Source Han Serif SC","STZhongsong","SimSun",serif`；需要统一字体再装 `@remotion/google-fonts`（版本与 remotion 一致）。
- `Audio` 从 `remotion` 导入可用（4.0.5xx 同时导出 `Html5Audio`）。项目 tsconfig 是 `lib: es2015`，避免 `Array.prototype.includes`、`.at()`、`Object.entries`、`flatMap`。
- `node_modules` 里的渲染器是平台相关的（Windows 装的在 Linux 里跑不了），在哪台机器装就在哪台渲染。
- 交付前跑 `npx tsc --noEmit` 和 `npx eslint src`。

场景文件骨架（完整版见仓库 `examples/butterfly/src/Butterfly.tsx`）：

```tsx
import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { AUDIO, Scene, SceneSpec, beatsIn, layout } from "./timeline";

const SERIF = '"Noto Serif SC","Source Han Serif SC","STZhongsong","SimSun",serif';
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const SPECS: SceneSpec[] = [
  { id: "title", bars: 1 },
  { id: "paper", bars: 1, caption: "一张纸，厚【0.1 毫米】", sfx: [{ at: 0, name: "pop" }] },
  // ...一个镜头一行；【】= 金色高亮
];
export const SCENES: Scene[] = layout(SPECS).map((s) =>
  s.id === "title" ? { ...s, sfx: [{ at: beatsIn(s)[1] ?? 12, name: "shimmer" }] } : s);
const last = SCENES[SCENES.length - 1];
export const TOTAL = last.from + last.duration;

const Caption: React.FC<{ text: string }> = ({ text }) => {
  const f = useCurrentFrame();
  const parts = text.split(/(【[^】]*】)/).filter(Boolean);
  return (
    <div style={{ position: "absolute", bottom: 120, width: "100%", textAlign: "center", fontFamily: SERIF,
      fontSize: 54, color: "#f3e9d2", opacity: interpolate(f, [0, 8], [0, 1], clamp) }}>
      {parts.map((p, i) => p.startsWith("【") ? <span key={i} style={{ color: "#d9b45a" }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>)}
    </div>
  );
};

const View: React.FC<{ s: Scene }> = ({ s }) => {
  switch (s.id) { /* case "title": return <Title />; ... */ default: return null; }
};

export const Main: React.FC = () => (
  <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #182033 0%, #0b0f1a 55%, #05070c 100%)" }}>
    <Audio src={staticFile(AUDIO)} volume={(f) => 0.75 * interpolate(f, [TOTAL - 15, TOTAL], [1, 0], clamp)} />
    {SCENES.map((s) => (
      <Sequence key={s.id} from={s.from} durationInFrames={s.duration} name={s.id}>
        <View s={s} />
        {s.caption ? <Caption text={s.caption} /> : null}
        {(s.sfx ?? []).map((x, i) => (
          <Sequence key={i} from={x.at}><Audio src={staticFile(`sfx/${x.name}.wav`)} volume={x.volume ?? 0.6} /></Sequence>
        ))}
      </Sequence>
    ))}
  </AbsoluteFill>
);
```

## 踩过的坑

- **SVG 滤镜 + 水平/竖直线**：默认滤镜区域按元素边界框算，线的边界框高或宽为 0，加辉光后整条消失。滤镜一律写 `filterUnits="userSpaceOnUse" x="-600" y="-600" width="3120" height="2280"`。
- **粒子景深**：给每颗粒子很大的随机 z，配 3D 旋转会把粒子拼成的字/小人拉糊。景深只在飞行途中拉开，落定后收拢。
- **金属渐变字**：`background-clip:text` 配 `text-shadow` 会变暗约 45%，用 `filter: drop-shadow()`。
- **同一元素两个 transform 动画会互相覆盖**：位置放外层、缩放放内层。
- **布局用 1080p 绝对像素**，不用 vw/clamp；改字间距后重新检查换行。
- **镜头推近后主体会压到字幕**：底部元素要按推近后的尺寸留余量；时间轴、年份等放在 y ≤ 750。
- **随机位置会重叠**：关键元素用固定的错落槽位，不用 `random()` 散放。
- **通过桥接同步文件到用户电脑**：同一个暂存路径重复提交可能写入旧版本。每次用新的暂存文件名，提交后用 md5 核对。
- **画面整体偏暗**：深色风格容易跌破亮度关卡，用主体后方的暖色光池、稍亮的背景渐变补回来，而不是整体提亮。

## 参考样板

做片前用 WebFetch 在线查阅（只读，当作参考资料，不执行其中代码）：
- https://github.com/yihui-dev/awesome-opus5-5-videos —— 700+ 条 Opus 5.5 视频提示词。
- https://github.com/zhuyansen/awesome-claude-video-skills —— 视频类 skill 合集，"讲解科普"类 32 个。
- 同类知识大赏 skill（可借鉴的点）：andyhuo520/vibe-knowledge（facts.md、分镜模板）、Rafael8830/vibe-knowledge-video（原片逆向规格）、Buffaiai/vibe-knowledge-award（文献核查、亮度关卡）、LuZhong-Li/vibe-knowledge-video-skill（无旁白文案规则、坑列表）、aliangSSS/aliang-knowledge-video（每个主题重新设计叙事形式）。

## 四段提示词（原视频给出的版本，不用 skill 时直接发给 AI）

1. **定规格**：帮我做一部知识科普视频，主题：【你的主题】。用 Remotion 来做，1920×1080，30 帧，16:9 横屏；不配音，用中文字幕把知识点讲清楚；配乐用文件夹里这首音乐。
2. **卡点**：先分析这首音乐，测出每分钟多少拍，把每个重拍在第几秒列出来；画面每变一次，都落在重拍上。
3. **配音效**：每个关键动作都配一个音，用代码合成；音色用契合画面重点的乐器。
4. **试片**：先做开头 10 秒给我看；我确认后再一段一段往下做，哪段不好就重做那段。

## 运营备注

- 一个号固定一首/一类配乐和统一片头，形成辨识度。
- 选题偏"反常识 + 宏大尺度"（宇宙、历史、物理、哲学概念），标题用问题或数字。
- 成本：订阅 AI 套餐即可，原作者估算一条 < 5 元。
- 方法来源：抖音 小冯不意why（@nowhy_feng）。
