# 太和殿 3D 构成分析交互原型

作者：虾老大

这是一个偏教学科普方向的中国古代建筑 3D 交互展示原型。页面以太和殿为例，用 Three.js 加载 Tripo3D 生成并优化后的 GLB 模型，结合 AI 图解、构件说明、图层切换、爆炸分解、夜游和演示模式，展示古建筑构件的基本关系。

当前版本以“技术模型展示”为目标，不追求建筑结构学术精确复原。

## 功能

- 太和殿主题浅色文博展陈风 UI
- 7 个构件条目：整体建筑、屋顶系统、斗拱层、柱梁系统、台基系统、脊兽装饰、彩画纹样
- Three.js WebGL 交互场景
- Tripo3D 生成模型接入
- 网页级轻量模型：单模型约 6 MB，约 25 万三角面
- 点击目录或模型热点切换构件说明
- 探索、分层、爆炸、夜游、演示模式
- 本地启动器与 PowerShell 兜底服务
- CDN 失败时的 2D canvas 兜底渲染

## 快速开始

推荐在 Windows 上双击：

```bat
start-taihe-hall.bat
```

启动器会开启本地静态服务并自动打开：

```text
http://127.0.0.1:4173/taihe-hall-3d-prototype.html
```

不要直接双击 `taihe-hall-3d-prototype.html`，浏览器可能会因为本地文件安全策略拦截 Three.js 模块或 GLB 模型。

## 目录结构

```text
.
├── taihe-hall-3d-prototype.html          # 主交互页面
├── start-taihe-hall.bat                  # Windows 一键启动器
├── start-taihe-hall.ps1                  # PowerShell 本地服务兜底
├── 打开说明.txt                          # 面向使用者的本地打开说明
├── assets/
│   ├── ai/                               # AI 图解与纹理资产
│   └── models/tripo/
│       └── taihe-components-optimized/   # GitHub 发布用轻量 GLB
└── vendor/
    └── three/                            # 本地 Three.js 运行依赖
```

## GitHub 发布建议

建议提交：

- `taihe-hall-3d-prototype.html`
- `assets/ai/`
- `assets/models/tripo/taihe-components-optimized/`
- `vendor/three/`
- `start-taihe-hall.bat`
- `start-taihe-hall.ps1`
- `打开说明.txt`
- `README.md`
- `DEVELOPMENT.md`
- `SECURITY.md`
- `.gitignore`
- `.gitattributes`
- `LICENSE`

不要提交：

- `.env`
- `release/`
- `assets/models/tripo/ab-dougong/`
- `assets/models/tripo/taihe-components/`
- `node_modules/`
- Tripo3D API key 或任何临时下载链接

## 资产说明

AI 图解与纹理位于 `assets/ai/`。

Tripo3D 原始标准模型较重，已优化为网页展示版本：

```text
assets/models/tripo/taihe-components-optimized/
```

主页面默认引用优化后的 `*_web.glb`，原始标准模型仅用于本地备份与后续再优化，不建议提交到 GitHub。

## 许可

代码使用 MIT License。AI/3D 生成资产由项目作者用于本展示原型。
