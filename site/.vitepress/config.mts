import path from "node:path";
import type { DefaultTheme } from "vitepress";
import { defineConfig } from "vitepress";
import { withMermaid } from "vitepress-plugin-mermaid";

// Hand-written user pages live in content/. sync-docs.mjs copies the repository's developer Markdown
// into content/ at the same relative paths, so those pages keep their own URLs and relative links.
const REPO = "https://github.com/guanqin-123/ACT-GUI";
const WORKBENCH = "https://app.act-online.au";

// Relative links to source files (not Markdown pages) point to the file on GitHub.
function sourceLinksToGitHub(md: any) {
  md.core.ruler.push("source_links_to_github", (state: any) => {
    const from = path.posix.dirname(state.env.relativePath ?? "");
    for (const block of state.tokens) {
      for (const token of block.children ?? []) {
        if (token.type !== "link_open") continue;
        const href: string = token.attrGet("href") ?? "";
        if (!href || /^([a-z]+:|#|\/)/i.test(href)) continue;
        const [file, hash] = href.split("#");
        if (/\.(md|html)$/.test(file)) continue;
        const target = path.posix.normalize(path.posix.join(from, file));
        const kind = file.endsWith("/") ? "tree" : "blob";
        token.attrSet("href", `${REPO}/${kind}/main/${target}${hash ? `#${hash}` : ""}`);
      }
    }
  });
}

type DeveloperLabels = {
  docs: string;
  task: string;
  rules: string;
  docsGuide: string;
  architecture: string;
  plan: string;
  website: string;
  overview: string;
};

const ENGLISH_DEVELOPER: DeveloperLabels = {
  docs: "Developer docs (English)",
  task: "Choose a development task",
  rules: "Contributor rules",
  docsGuide: "Documentation guide",
  architecture: "Architecture",
  plan: "Development plan",
  website: "Website",
  overview: "Overview",
};

// Developer docs are the repository's English Markdown in every locale; only the sidebar labels are translated.
function developerSidebar(l: DeveloperLabels): DefaultTheme.SidebarItem[] {
  return [
    {
      text: l.docs,
      collapsed: true,
      items: [
        { text: l.task, link: "/README" },
        { text: l.rules, link: "/AGENTS" },
        { text: l.docsGuide, link: "/docs/README" },
        { text: l.architecture, link: "/docs/design" },
        { text: l.plan, link: "/docs/plan" },
        { text: l.website, link: "/site/README" },
      ],
    },
    {
      text: "visual_bench",
      collapsed: true,
      items: [
        { text: l.overview, link: "/visual_bench/README" },
        ...["workspace", "model_spec", "verification", "fuzzing", "engine", "analysis", "bab", "assistant", "records"].map(
          (m) => ({ text: m, link: `/visual_bench/${m}/README` }),
        ),
      ],
    },
    {
      text: "engine_bridge",
      collapsed: true,
      items: [
        { text: l.overview, link: "/engine_bridge/README" },
        ...["engine_session", "model_spec", "execution", "inspection", "events"].map((m) => ({
          text: m,
          link: `/engine_bridge/${m}/README`,
        })),
      ],
    },
  ];
}

type Labels = {
  guide: string;
  whatIs: string;
  installation: string;
  howItWorks: string;
  modes: string;
  configuration: string;
  developers: string;
  openWorkbench: string;
};

function locale(prefix: string, l: Labels, d = ENGLISH_DEVELOPER): DefaultTheme.Config {
  return {
    nav: [
      { text: l.guide, link: `${prefix}/guide/` },
      { text: l.developers, link: "/README" },
      { text: l.openWorkbench, link: WORKBENCH },
    ],
    sidebar: [
      {
        text: l.guide,
        items: [
          { text: l.whatIs, link: `${prefix}/guide/` },
          { text: l.installation, link: `${prefix}/guide/installation` },
          { text: l.howItWorks, link: `${prefix}/guide/how-it-works` },
          { text: l.modes, link: `${prefix}/guide/modes` },
          { text: l.configuration, link: `${prefix}/guide/configuration` },
        ],
      },
      ...developerSidebar(d),
    ],
  };
}

export default withMermaid(
  defineConfig({
    title: "ACT-GUI",
    description: "The visual workbench for ACT neural network verification.",
    srcDir: "content",
    cleanUrls: true,
    appearance: "dark",
    markdown: { config: sourceLinksToGitHub },
    themeConfig: {
      socialLinks: [{ icon: "github", link: REPO }],
      search: { provider: "local" },
      outline: "deep",
    },
    locales: {
      root: {
        label: "English",
        lang: "en-US",
        themeConfig: locale("", {
          guide: "Guide",
          whatIs: "What is ACT-GUI?",
          installation: "Installation",
          howItWorks: "How it works",
          modes: "Working modes",
          configuration: "Configuration",
          developers: "Developers",
          openWorkbench: "Open Workbench",
        }),
      },
      zh: {
        label: "简体中文",
        lang: "zh-CN",
        description: "ACT 神经网络验证的可视化工作台。",
        themeConfig: locale("/zh", {
          guide: "指南",
          whatIs: "ACT-GUI 是什么？",
          installation: "安装",
          howItWorks: "工作原理",
          modes: "工作模式",
          configuration: "配置",
          developers: "开发者",
          openWorkbench: "打开工作台",
        }, {
          docs: "开发者文档（英文）",
          task: "选择开发任务",
          rules: "贡献者规则",
          docsGuide: "文档指南",
          architecture: "架构",
          plan: "开发计划",
          website: "网站",
          overview: "概览",
        }),
      },
      fr: {
        label: "Français",
        lang: "fr-FR",
        description: "L'atelier visuel de vérification de réseaux de neurones ACT.",
        themeConfig: locale("/fr", {
          guide: "Guide",
          whatIs: "Qu'est-ce qu'ACT-GUI ?",
          installation: "Installation",
          howItWorks: "Fonctionnement",
          modes: "Modes de travail",
          configuration: "Configuration",
          developers: "Développeurs",
          openWorkbench: "Ouvrir l'atelier",
        }),
      },
    },
  }),
);
