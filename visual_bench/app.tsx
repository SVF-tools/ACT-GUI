// Composition root: selection and props connect otherwise independent feature slices.
import { useEffect, useReducer, useState } from "react";
import { AssistantView } from "./assistant/AssistantView";
import { ModelGraph } from "./model_spec/ModelGraph";
import { LoadPanel } from "./model_spec/LoadPanel";
import { ModelList } from "./model_spec/ModelList";
import { SpecPanel } from "./model_spec/SpecPanel";
import { RebuildNotice } from "./model_spec/RebuildNotice";
import { ApiError } from "./shared/http";
import { useModels, useModel } from "./model_spec/hooks";
import { RecordsView } from "./records/RecordsView";
import { RunsPanel } from "./verification/RunsPanel";
import { RunHistory } from "./verification/RunHistory";
import { useLiveRuns } from "./verification/hooks";
import { EngineBadge } from "./engine/EngineBadge";
import { EngineView } from "./engine/EngineView";
import { useCapabilities } from "./engine/hooks";
import { GurobiBadge } from "./engine/GurobiBadge";
import { FuzzSettings } from "./fuzzing/FuzzSettings";
import { useFuzzConfiguration } from "./fuzzing/hooks";
import { initialSelection, selectionReducer } from "./workspace/selection";
import { modes, defaultMode, modeForId, modeForMethod, type ModeId } from "./workspace/modes";
import { ContextBar } from "./workspace/layout";
import { ThemeToggle } from "./workspace/theme";
import { Tour } from "./workspace/tour";
import { PresenceBar } from "./workspace/Presence";
import { markTourDone, tourPending } from "./workspace/tourSteps";
import { Empty } from "./shared/ui/Empty";

const TABS = ["Engine", "Records", "Assistant"] as const;
type Tab = (typeof TABS)[number];
export function App() {
  const [sel, dispatch] = useReducer(selectionReducer, initialSelection);
  const [mode, setMode] = useState<ModeId>(defaultMode);
  const [tab, setTab] = useState<Tab>("Engine");
  const [touring, setTouring] = useState(tourPending);
  const models = useModels();
  const model = useModel(sel.modelId);
  const fuzz = useFuzzConfiguration();
  const activeMode = modeForId(mode);
  const lacks = useCapabilities();
  // After an ACT switch, leave a mode the new checkout cannot run.
  const fallbackMode = lacks(activeMode.capability) ? modes.find((m) => !lacks(m.capability))?.id : undefined;
  useEffect(() => { if (fallbackMode) setMode(fallbackMode); }, [fallbackMode]);
  useLiveRuns();
  const current = models.status === "success" ? models.data.find((m) => m.model_id === sel.modelId) ?? null : null;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="logo">ACT</span>
          <span>GUI Workbench</span>
        </div>
        <ContextBar sel={sel} />
        <EngineBadge />
        <GurobiBadge onOpen={() => setTab("Engine")} />
        <button type="button" className="themetoggle" data-tour="guide" onClick={() => setTouring(true)}
          title="Show the guided tour">? Guide</button>
        <ThemeToggle />
      </header>
      {touring && <Tour modelReady={model.status === "success"} onClose={() => { markTourDone(); setTouring(false); }} />}
      <aside className="sidebar">
        <div data-tour="load">
          <LoadPanel current={current}
            onLoaded={(m) => { dispatch({ type: "selectModel", modelId: m.model_id }); }} />
        </div>
        <div data-tour="models">
          <ModelList models={models} selected={sel.modelId} onSelect={(id) => dispatch({ type: "selectModel", modelId: id })} />
        </div>
      </aside>
      <main className="center">
        {sel.modelId === null && <Empty title="Select a model" text="Models are real ACT networks pinned by commit and sha256." />}
        {sel.modelId !== null && model.status === "pending" && <Empty title="Loading model through ACT…" text="" />}
        {model.status === "error" && (current && (current.source ?? "catalog") !== "catalog" && model.error instanceof ApiError
          && model.error.code === "model_load_failed"
          ? <RebuildNotice model={current} message={model.error.message}
              onRebuilt={(m) => dispatch({ type: "selectModel", modelId: m.model_id })} />
          : <div className="error">Model load failed: {model.error.message}</div>)}
        {model.status === "success" && (
          <>
            <section className="panel" data-tour="network">
                <h2>Network <small>{model.data.layers.length} layers · ACT {model.data.act_commit?.slice(0, 8)}</small></h2>
                <ModelGraph model={model.data} selectedLayer={sel.layerId}
                  onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })} />
            </section>
            <div data-tour="runs">
            <RunsPanel
              modelId={model.data.model_id}
              method={activeMode.method}
              fuzzOptions={fuzz.value}
              fuzzSettings={<>
                {fuzz.query.isError && <div className="error">Fuzz defaults unavailable: {fuzz.query.error.message}</div>}
                {fuzz.value && fuzz.defaults && <FuzzSettings value={fuzz.value} defaults={fuzz.defaults} onChange={fuzz.setValue} />}
              </>}
              onMethod={(m) => setMode(modeForMethod(m).id)}
              onSelect={(runId) => dispatch({ type: "selectRun", runId, modelId: model.data.model_id })}
            />
            </div>
            <section className="panel modes" data-tour="modes">
              <nav className="tabs" role="tablist" aria-label="run mode">
                {modes.map((m) => (
                  <button key={m.id} role="tab" aria-selected={mode === m.id} className={mode === m.id ? "tab active" : "tab"}
                    disabled={lacks(m.capability) !== null} title={lacks(m.capability) ?? undefined}
                    onClick={() => setMode(m.id)}>{m.label}</button>
                ))}
              </nav>
              <div className="modebody">
                {lacks(activeMode.capability) && <div className="banner warn"><b>Disabled on this ACT checkout.</b> {lacks(activeMode.capability)}</div>}
                <activeMode.View sel={sel} model={model.data}
                  onSelectLayer={(layerId) => dispatch({ type: "selectLayer", layerId })}
                  onSelectNeuron={(neuron) => dispatch({ type: "selectNeuron", neuron })} />
              </div>
            </section>
            <div data-tour="spec">
              <SpecPanel model={model.data} selectedLayer={sel.layerId} />
            </div>
          </>
        )}
      </main>
      <section className="inspector">
        <div className="insptop" data-tour="inspector">
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
          {tab === "Records" && <RecordsView runId={sel.runId} />}
          {tab === "Engine" && (
            <EngineView />
          )}
        </div>
        </div>
        {model.status === "success" && (
          <div className="insphistory" data-tour="history">
            <RunHistory
              modelId={model.data.model_id}
              method={activeMode.method}
              selectedRun={sel.runId}
              onSelect={(runId) => dispatch({ type: "selectRun", runId, modelId: model.data.model_id })}
            />
          </div>
        )}
        <PresenceBar />
      </section>
    </div>
  );
}

