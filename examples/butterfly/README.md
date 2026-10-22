# 示例：《蝴蝶效应》开头

把 `src/Butterfly.tsx`、`src/Root.tsx` 放进 Remotion 项目的 `src/`（同时需要 skill 里的 `src/timeline.ts` 和 `scripts/`），然后：

```bash
python scripts/prepare.py   # 生成 src/beats.ts 和 public/sfx/
npm run dev                 # 在 Studio 里打开 Butterfly
```

| 镜头 | 小节 | 内容 | 音效 |
|---|---|---|---|
| title | 1 | 片名逐字去模糊，金线在拍点展开 | shimmer |
| wings | 1 | 蝴蝶曲线粒子，第 2 拍扇翅 + 涟漪 | whoosh |
| paper | 1 | 金色纸片，标注 0.1 mm | pop |
| fold | 1 | 每拍对折一次 0.2→1.6 mm | note_1–4 升调 + riser |
| moon | 2 | 数字对数滚动到 439,804 km，月亮出现 | boom + shimmer |

镜头和字幕都在 `SPECS` 里改；换歌后重跑 `prepare.py`，所有切点自动重新对齐。
