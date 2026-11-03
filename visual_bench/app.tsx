// Thin composition root: owns the shared selection and wires module views together.
import { useReducer, useState } from "react";
import { api } from "./api";
import { AnalysisView } from "./analysis/AnalysisView";
import { AssistantView } from "./assistant/AssistantView";
import { BabView } from "./bab/BabView";
import { ModelGraph } from "./model_spec/ModelGraph";
import { LoadPanel } from "./model_spec/LoadPanel";
import { ModelList } from "./model_spec/ModelList";
import { SpecPanel } from "./model_spec/SpecPanel";
import { RecordsView } from "./records/RecordsView";
import { RunHistory, RunsPanel } from "./verification/RunsPanel";
import { EngineBadge } from "./verification/EngineBadge";
import { EngineView } from "./verification/EngineView";
import { FuzzView } from "./verification/FuzzView";
import { GurobiBadge } from "./verification/GurobiBadge";
import { VerdictBanner } from "./verification/VerdictBanner";
import { initialSelection, selectionReducer } from "./workspace/selection";
import { Empty } from "./workspace/Empty";
import { ThemeToggle } from "./workspace/theme";
import { useQuery } from "./workspace/useQuery";
import type { RunRequest } from "./generated/wire";

type Method = RunRequest["method"];

// Run modes share the center column with the network; one is shown at a time.
const MODES = ["Verification", "BaB", "Fuzzing"] as const;
type Mode = (typeof MODES)[number];
const TABS = ["Assistant", "Records", "Engine"] as const;
type Tab = (typeof TABS)[number];
// Each mode runs one ACT method; the runs panel follows the selected mode.
const METHOD_OF_MODE: Record<Mode, Method> = { Verification: "interval", BaB: "bab", Fuzzing: "fuzz" };
const MODE_OF_METHOD: Record<Method, Mode> = { interval: "Verification", bab: "BaB", fuzz: "Fuzzing" };

export function App() {
  const [sel, dispatch] = useReducer(selectionReducer, initialSelection);
  const [mode, setMode] = useState<Mode>("Verification");
  const [tab, setTab] = useState<Tab>("Assistant");
  const [runsVersion, setRunsVersion] = useState(0);
  const [licenseVersion, setLicenseVersion] = useState(0);
  const [modelsVersion, setModelsVersion] = useState(0);
  const models = useQuery("models", api.models, modelsVersion);
  const model = useQuery(sel.modelId, () => api.model(sel.modelId!));
  const current = models.status === "ok" ? models.data.find((m) => m.model_id === sel.modelId) ?? null : null;

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
        <LoadPanel current={current}
          onLoaded={(m) => { setModelsVersion((v) => v + 1); dispatch({ type: "selectModel", modelId: m.model_id }); }} />
        <ModelList models={models} selected={sel.modelId} onSelect={(id) => dispatch({ type: "selectModel", modelId: id })} />
      </aside>
      <main className="center">
        {model.status === "idle" && <Empty title="Select a model" text="Models are real ACT networks pinned by commit and sha256." />}
        {model.status === "loading" && <Empty title="Loading model through ACT…" text="" />}
        {model.status === "error" && <div className="error">Model load failed: {model.message}</div>}
        {model.status === "ok" && (
          <>
            <div className="netrow">
              <section className="panel">
                <h2>Network <small>{model.data.layers.length} layers · ACT {model.data.act_commit?.slice(0, 8)}</small></h2>
                <ModelGraph model={model.data} selectedLayer={sel.layerId}
                  onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })} />
              </section>
              <RunsPanel
                modelId={model.data.model_id}
                method={METHOD_OF_MODE[mode]}
                onMethod={(m) => setMode(MODE_OF_METHOD[m])}
                onChanged={() => setRunsVersion((v) => v + 1)}
                onSelect={(runId) => dispatch({ type: "selectRun", runId, modelId: model.data.model_id })}
              />
            </div>
            <section className="panel modes">
              <nav className="tabs" role="tablist" aria-label="run mode">
                {MODES.map((m) => (
                  <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? "tab active" : "tab"} onClick={() => setMode(m)}>{m}</button>
                ))}
              </nav>
              <div className="modebody">
                {(mode === "Verification" || mode === "BaB") && (
                  <VerdictBanner runId={sel.runId} version={runsVersion} model={model.data}
                    onStopped={() => setRunsVersion((v) => v + 1)} />
                )}
                {mode === "Verification" && (
                  <AnalysisView sel={sel} version={runsVersion} model={model.data}
                    onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })}
                    onSelectNeuron={(neuron) => dispatch({ type: "selectNeuron", neuron })} />
                )}
                {mode === "BaB" && <BabView runId={sel.runId} version={runsVersion} />}
                {mode === "Fuzzing" && <FuzzView runId={sel.runId} version={runsVersion} model={model.data} />}
              </div>
            </section>
            <SpecPanel model={model.data} selectedLayer={sel.layerId} />
          </>
        )}
      </main>
      <section className="inspector">
        <div className="insptop">
        <nav className="tabs" role="tablist">
          {TABS.map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>{t}</button>
          ))}
        </nav>
        <div className="tabbody">
          {tab === "Assistant" && (
            <AssistantView sel={sel}
              onNavigate={(layerId, neuron) => {
                dispatch({ type: "selectLayer", layerId });
                if (neuron !== null) dispatch({ type: "selectNeuron", neuron });
                setMode("Verification");
              }} />
          )}
          {tab === "Records" && <RecordsView runId={sel.runId} version={runsVersion} />}
          {tab === "Engine" && (
            <EngineView licenseVersion={licenseVersion} onLicenseChanged={() => setLicenseVersion((v) => v + 1)} />
          )}
        </div>
        </div>
        {model.status === "ok" && (
          <div className="insphistory">
            <RunHistory
              modelId={model.data.model_id}
              method={METHOD_OF_MODE[mode]}
              selectedRun={sel.runId}
              version={runsVersion}
              onChanged={() => setRunsVersion((v) => v + 1)}
              onSelect={(runId) => dispatch({ type: "selectRun", runId, modelId: model.data.model_id })}
            />
          </div>
        )}
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

