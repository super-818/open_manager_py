# 🚀 Open Manager

> **一键管理你的AI技能和开源项目** | 智能去重 · 批量更新 · 多平台分发

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/super-818/open_manager_py)

---

## 💡 3秒了解

你是否也有这样的困扰？
- 🤯 AI技能散落各处，找不到、用不上
- 😵 GitHub项目越来越多，不知道哪个是最新版
- 🤔 想分发技能到不同AI工具，只能手动复制粘贴

**Open Manager 一键解决所有问题！**

---

## ✨ 核心卖点

### 🎯 **智能扫描 + 自动去重**
```
扫描 D:\skills 和 D:\github
→ 自动识别所有技能和项目
→ 基于内容哈希智能去重
→ 一目了然的管理界面
```

### 🔄 **一键更新所有项目**
```
点击"更新全部"
→ git clone --depth 1 获取最新版
→ 失败自动恢复备份
→ 批量更新，省时省力
```

### 📤 **一键分发到多个AI工具**
```
选择技能 + 选择目标工具
→ Trae / Claude Code / OpenClaw
→ 自定义路径也支持
→ 批量分发，效率翻倍
```

---

## 🚀 快速开始

### 方式一：一键安装（Windows）
```powershell
.\install.ps1
```
桌面自动创建快捷方式，双击即可使用！

### 方式二：手动启动
```bash
pip install -r requirements.txt
python run.py
```

访问 http://127.0.0.1:5000 开始使用！

---

## 🎬 功能演示

### 📊 资源管理
- ✅ 自动扫描本地技能和GitHub项目
- ✅ 显示大小、更新时间、GitHub链接
- ✅ 自定义分类和标签
- ✅ 添加备注说明

### 🔄 项目更新
- ✅ 单个项目一键更新
- ✅ 批量更新所有项目
- ✅ 更新失败自动回滚
- ✅ 保留本地修改（备份机制）

### 📤 技能分发
- ✅ 支持多工具同时分发
- ✅ 按类别批量分发
- ✅ 自定义目标路径
- ✅ 自动覆盖旧版本

---

## 🎯 使用场景

| 场景 | 痛点 | 解决方案 |
|------|------|----------|
| **AI开发者** | 技能太多，管理混乱 | 统一管理 + 一键分发 |
| **开源爱好者** | 项目更新频繁，手动更新慢 | 批量更新 + 自动备份 |
| **团队协作** | 资源分散，难以共享 | 统一资源库 + 分类管理 |

---

## 🏗️ 技术栈

- **后端**: Flask + SQLite
- **前端**: 原生JavaScript + CSS3
- **跨平台**: Windows / macOS / Linux

---

## 📝 配置

默认配置：
- 技能目录: `D:\skills` (Windows) 或 `~/skills` (macOS/Linux)
- 项目目录: `D:\github` (Windows) 或 `~/github` (macOS/Linux)
- 数据库: `~/.open_manager/open_manager.db`

可在 `config.py` 中自定义。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by [super-818](https://github.com/super-818)

</div>
