"""AIPLPhMTools 自检入口。

自检代码集中在本目录，不从主包自动导入，避免影响正常绘图：

- ``general_tools.py``：构建全部公共器件，检查端口/几何/图层/关键行为；
- ``soitools.py``：SOITools 子库几何与层号自检；
- ``run_all.py``：依次运行以上两组自检。
"""
