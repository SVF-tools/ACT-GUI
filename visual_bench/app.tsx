// Thin composition root: owns the shared selection and wires module views together.
import { useReducer, useState } from "react";
import { api } from "./api";
import { AnalysisView } from "./analysis/AnalysisView";
import { AssistantView } from "./assistant/AssistantView";
import { BabView } from "./bab/BabView";
import { ModelGraph } from "./model_spec/ModelGraph";
import { ModelList } from "./model_spec/ModelList";
import { SpecPanel } from "./model_spec/SpecPanel";
import { RecordsView } from "./records/RecordsView";
import { RunsPanel } from "./verification/RunsPanel";
import { EngineBadge } from "./verification/EngineBadge";
import { EngineView } from "./verification/EngineView";
import { FuzzView } from "./verification/FuzzView";
import { GurobiBadge } from "./verification/GurobiBadge";
import { initialSelection, selectionReducer } from "./workspace/selection";
import { Empty } from "./workspace/Empty";
import { ThemeToggle } from "./workspace/theme";
import { useQuery } from "./workspace/useQuery";

const TABS = ["Propagation", "BaB", "Fuzzing", "Assistant", "Records", "Engine"] as const;
type Tab = (typeof TABS)[number];

export function App() {
  const [sel, dispatch] = useReducer(selectionReducer, initialSelection);
  const [tab, setTab] = useState<Tab>("Propagation");
  const [runsVersion, setRunsVersion] = useState(0);
  const [licenseVersion, setLicenseVersion] = useState(0);
  const model = useQuery(sel.modelId, () => api.model(sel.modelId!));

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="logo">ACT</span>
          <span>GUI Workbench</span>
        </div>
        <div className="context" aria-label="research context">
          <Ctx label="model" value={sel.modelId} />
          <Ctx label="run" value={sel.runId} />
          <Ctx label="layer" value={sel.layerId} />
          <Ctx label="index" value={sel.neuron} />
        </div>
        <EngineBadge />
        <GurobiBadge version={licenseVersion} onOpen={() => setTab("Engine")} />
        <ThemeToggle />
      </header>
      <aside className="sidebar">
        <ModelList selected={sel.modelId} onSelect={(id) => dispatch({ type: "selectModel", modelId: id })} />
        {sel.modelId && (
          <RunsPanel
            modelId={sel.modelId}
            selectedRun={sel.runId}
            version={runsVersion}
            onChanged={() => setRunsVersion((v) => v + 1)}
            onSelect={(runId) => dispatch({ type: "selectRun", runId, modelId: sel.modelId! })}
            onStarted={(method) => method === "fuzz" && setTab("Fuzzing")}
          />
        )}
      </aside>
      <main className="center">
        {model.status === "idle" && <Empty title="Select a model" text="Models are real ACT networks pinned by commit and sha256." />}
        {model.status === "loading" && <Empty title="Loading model through ACT…" text="" />}
        {model.status === "error" && <div className="error">Model load failed: {model.message}</div>}
        {model.status === "ok" && (
          <>
            <section className="panel">
              <h2>Network <small>{model.data.layers.length} layers · ACT {model.data.act_commit?.slice(0, 8)}</small></h2>
              <ModelGraph model={model.data} selectedLayer={sel.layerId}
                onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })} />
            </section>
            <SpecPanel model={model.data} selectedLayer={sel.layerId} />
          </>
        )}
      </main>
      <section className="inspector">
        <nav className="tabs" role="tablist">
          {TABS.map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>{t}</button>
          ))}
        </nav>
        <div className="tabbody">
          {tab === "Propagation" && (
            <AnalysisView sel={sel} version={runsVersion} model={model.status === "ok" ? model.data : null}
              onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })}
              onSelectNeuron={(neuron) => dispatch({ type: "selectNeuron", neuron })} />
          )}
          {tab === "BaB" && <BabView runId={sel.runId} version={runsVersion} />}
          {tab === "Fuzzing" && <FuzzView runId={sel.runId} version={runsVersion} model={model.status === "ok" ? model.data : null} />}
          {tab === "Assistant" && (
            <AssistantView sel={sel}
              onNavigate={(layerId, neuron) => {
                dispatch({ type: "selectLayer", layerId });
                if (neuron !== null) dispatch({ type: "selectNeuron", neuron });
                setTab("Propagation");
              }} />
          )}
          {tab === "Records" && <RecordsView runId={sel.runId} version={runsVersion} />}
          {tab === "Engine" && (
            <EngineView licenseVersion={licenseVersion} onLicenseChanged={() => setLicenseVersion((v) => v + 1)} />
          )}
        </div>
      </section>
    </div>
  );
}

function Ctx({ label, value }: { label: string; value: string | number | null }) {
  return (
    <span className={value === null ? "ctx unset" : "ctx"}>
      <b>{label}</b> {value === null ? "—" : String(value)}
    </span>
  );
}

