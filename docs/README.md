# AIPLPhMTools 版图手册（静态站点）

这个目录是可直接发布的静态网站：每个器件一页，展示默认版图、端口、参数含义，
以及关键参数的预渲染版图对比。图像由 `build_site.py` 实际调用器件、写出 GDS、
再用 KLayout + Matplotlib 渲染，不是手绘示意图。

## 本地生成

在包含 `AIPLPhMTools` 的目录下（依赖 gdsfactory / klayout / matplotlib）：

```bash
python AIPLPhMTools/docs/build_site.py
```

产物会写到本目录：

```text
docs/
├── index.html                 # 概览（按功能分类 + 按模块浏览）
├── guide.html                 # 安装、目录结构、参数约定、图层、自检
├── modules.html               # 模块层级：Core / Devices / Assemblies / TestStructures / Electrical / Platforms/SOI
├── gdsmerge.html              # GDS 原位合并：PDK cell 指纹比对 / 复用 / 冲突报告
├── platforms_soi.html         # Platforms/SOI 平台子库（原 soitools.html）
├── soitools.html              # 旧地址跳转到 platforms_soi.html
├── heaters3d.html             # 加热器 3D 层叠图（可拖动旋转）
├── components/<器件>.html     # 每个器件一页（顶部「模块」链回 modules.html）
├── categories/<分类>.html     # 分类索引
└── assets/
    ├── site.css / site.js
    ├── img/                   # 默认参数版图
    ├── img/variants/          # 参数对比图
    ├── gds/                   # 默认参数 GDS（gzip）
    ├── view3d/                # 每个器件一份 3D 层叠数据
    ├── component3d.js         # 器件页 3D 查看器（可调每层厚度）
    ├── heaters3d-data.js      # 加热器对比页 3D 数据
    ├── heaters3d.js           # 3D 查看器（canvas，无外部依赖）
    ├── csv/                   # CSV DBR 的演示数据
    └── platforms_soi/         # Platforms/SOI 子库演示图
```

## 本地预览

静态页面不依赖后端，但请用 HTTP 服务打开（不要直接双击 `file://`）：

```bash
python -m http.server 8000 -d AIPLPhMTools/docs
# 浏览器打开 http://127.0.0.1:8000/
```

## 发布到 GitHub Pages

### 方式 A：仓库根目录就是本库

如果仓库结构是 `repo/docs/...`（即本 `docs/` 在仓库根目录）：

1. 生成并提交 `docs/`；
2. GitHub 仓库 → Settings → Pages；
3. Source 选 **Deploy from a branch**，Branch 选 `main`，Folder 选 **`/docs`**；
4. 保存后访问 `https://<user>.github.io/<repo>/`。

### 方式 B：本库在更大工程的子目录

如果 `docs/` 位于 `AIPLPhMTools/docs/`（例如当前芯片工程），GitHub Pages
不能直接把子目录当站点根。两种做法：

1. 把 `AIPLPhMTools/docs` 的内容复制到仓库根的 `docs/` 再发布；
2. 或用 GitHub Actions 上传 `AIPLPhMTools/docs` 作为 Pages artifact：

```yaml
name: Deploy handbook
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e . matplotlib klayout numpy
      - run: python AIPLPhMTools/docs/build_site.py
      - uses: actions/upload-pages-artifact@v3
        with:
          path: AIPLPhMTools/docs
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

`docs/.nojekyll` 已包含，避免 GitHub Pages 的 Jekyll 处理下划线文件。

## 注意

- 页面中的 GDS 下载是 **默认参数** 的压缩 GDS；参数对比图只生成 PNG。
- CSV 驱动的 DBR 使用 `assets/csv/` 里的演示数据，只用于展示结构；
  实际使用时传入你自己的 `CSVName`，或设置 `AIPL_DBR_CSV_DIR`。
- 重新生成会覆盖 `assets/` 下的图像；如果手工改过图片，请先备份。
