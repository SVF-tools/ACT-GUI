---
layout: home

hero:
  name: ACT-GUI
  text: 看见神经网络形式化验证的内部过程
  tagline: 面向 ACT 验证器的浏览器工作台。加载网络、进行模糊测试和验证，并检查 ACT 计算出的每个界。由 ACT 作出判断，工作台展示其中依据。
  actions:
    - theme: brand
      text: 打开工作台
      link: https://app.act-online.au
    - theme: alt
      text: 开始使用
      link: /zh/guide/
    - theme: alt
      text: GitHub
      link: https://github.com/guanqin-123/ACT-GUI

features:
  - title: 实时模糊测试
    details: 运行 ACT 的模糊测试器，观察它搜索过程中原始图像、变异图像和差分图像的实时更新。运行期间可以暂停、恢复、停止或重新调整参数。
  - title: 验证与 BaB
    details: 使用区间、对偶或 HybridZ 抽象域运行 ACT 的单遍验证，或运行批量分支定界。最终结论始终由 ACT 给出。
  - title: 逐层上下界
    details: 逐步查看 ACT 在每一层记录的上下界，比较变换前后的结果，并投影为二维区间盒。
  - title: 可复用的反例
    details: ACT 接受的每个违反样例都会随运行保存，并导出为 VNN-COMP 见证文件或图像。
  - title: 可复现记录
    details: 每次运行都保留清单、仅追加事件日志和经过 sha256 封存的工件。可以将完整记录导出为 zip 文件。
  - title: 任意 ACT 分支
    details: 将引擎切换到固定基线或任意 ACT 派生仓库的分支。当前引擎不支持的功能会被禁用，并显示原因。
---

<div class="home-demo">

![ACT-GUI 模糊测试演示](../fuzzingGuide.gif)

</div>
