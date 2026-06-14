# 开发说明

作者：虾老大

## 本地运行

方式一：双击启动器。

```bat
start-taihe-hall.bat
```

方式二：手动启动静态服务。

```bash
python -m http.server 4173
```

然后访问：

```text
http://127.0.0.1:4173/taihe-hall-3d-prototype.html
```

## Git 初始化与发布

如果本机 Git 提示 `dubious ownership`，可以把当前目录加入安全目录：

```bash
git config --global --add safe.directory "C:/Users/aaa/Documents/Interactive Website"
```

发布前建议检查候选文件：

```bash
git add -n .
git status --short --ignored
```

确认 `.env`、`release/`、原始模型目录和 A/B 测试目录没有进入提交。

## 技术栈

- HTML/CSS/JavaScript 单文件主页面
- Three.js + OrbitControls + GLTFLoader
- Tripo3D image-to-model 生成 GLB
- glTF Transform 用于模型降面、清理和量化
- 本地 `vendor/three/` 依赖，避免运行时依赖 CDN

## 模型接入策略

主页面中的 `components` 数据包含：

- `modelUrl`
- `generatedModelUrl`
- `provider`
- `assetStatus`

当前页面引用：

```text
assets/models/tripo/taihe-components-optimized/{id}/{id}_web.glb
```

模型采用懒加载：

- 首屏只加载整体建筑
- 点击构件后加载对应模型
- 探索模式只保留当前模型，离开时释放显存
- 分层/爆炸模式按需加载可见层

这样可以避免一次性加载所有 GLB 导致 WebGL 卡顿。

## 模型优化流程

原始 Tripo3D 标准模型约 40 MB / 140 万三角面，网页运行压力较大。发布版使用 glTF Transform 优化到约 6 MB / 25 万三角面。

示例命令：

```bash
npx gltf-transform optimize input.glb output.glb \
  --compress quantize \
  --simplify true \
  --simplify-ratio 0.18 \
  --simplify-error 0.002 \
  --texture-compress auto \
  --texture-size 1024
```

优化后放入：

```text
assets/models/tripo/taihe-components-optimized/
```

## 交互注意点

构件选择不能绑在 `pointerdown`，否则拖拽旋转时会误触发切换。当前逻辑为：

- `pointerdown` 记录起点和命中对象
- `pointerup` 判断移动距离和按住时间
- 移动超过 6px 或按住超过 450ms 时视为拖拽，不触发构件选择

## 打包

发布包只需要包含：

- 主 HTML
- `assets/ai/`
- `assets/models/tripo/taihe-components-optimized/`
- `vendor/three/`
- 启动器和说明文件

不要把 `.env`、原始模型、测试模型或 API key 打包进去。
