---
layout: home

hero:
  name: ACT
  text: 抽象约束变换
  tagline: 面向神经网络的测试与验证框架。加载模型和规约，搜索反例，并用可靠的抽象解释和分支定界证明性质。
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/guide/
    - theme: alt
      text: 在线试用
      link: https://app.act-online.au
    - theme: alt
      text: GitHub
      link: https://github.com/SVF-tools/ACT

features:
  - title: 所有模型共用一种中间表示
    details: PyTorch 模型、ONNX 网络和 VNN-LIB 性质都会转换成同一种 ACT Net，输入和输出规约作为层嵌入其中，因此每个后端验证的都是同一个问题。
  - title: 三种抽象域
    details: 用区间、HybridZ 带形（zonotope）或线性松弛对偶界在 MLP、CNN、RNN 和 Transformer 层中传播上下界。
  - title: 分支定界
    details: 对尚未判定的性质拆分神经元或输入继续细化，支持批量子问题、多种分支启发式，以及 LP、对偶或 MILP 定界。
  - title: 白盒模糊测试
    details: ACTFuzzer 在 GPU 上搜索违例，使用梯度引导变异、自适应扰动缩放和神经元覆盖率。
  - title: 经过检查的反例
    details: 无论来自模糊测试还是验证，每个反例在报告前都会在具体模型上按同一份输入和输出规约检查。
  - title: 验证器校验
    details: 用具体反例交叉检查结论，并逐层检查抽象上下界是否包含所有具体激活值。
---

<div class="home-demo">

![在线工作台中的 ACT 模糊测试](../fuzzingGuide.gif)

</div>
