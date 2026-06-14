# 安全说明

## API Key

Tripo3D API key 只能保存在本地 `.env` 中，不要提交到 GitHub，不要放入 zip，不要写入 HTML。

本项目的 `.gitignore` 已排除：

```text
.env
.env.*
```

并保留 `.env.example` 作为配置模板。

## 发布前检查

发布到 GitHub 前建议运行：

```powershell
git status --short
Select-String -Path . -Pattern "TRIPO_API_KEY|tsk_|tcli_" -Recurse
```

确认没有 API key、临时签名下载链接或 `.env` 文件进入提交。

## 资源包

`release/` 是本地打包目录，默认不进入 Git。展示包中不需要任何 API key。
