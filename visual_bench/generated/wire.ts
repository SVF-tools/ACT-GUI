/* Generated from visual_bench/schemas.py by scripts/gen_types.mjs. Do not edit. */

export type Evidence = string[]
export type Kind = ("observation" | "interpretation" | "hypothesis" | "missing")
export type Text = string
export type Availability = ("available" | "pending" | "not_recorded" | "unsupported")
export type Name = string
export type Source = string
export type Dataset = string
export type Description = string
export type Onnx = string
export type SourceId = string
export type FinalSummary = ("available" | "pending" | "not_recorded" | "unsupported")
export type NodeEvents = ("available" | "pending" | "not_recorded" | "unsupported")
export type Reason = string
export type RunId = string
export type Summary = ({
[k: string]: string | number | boolean | null
} | null)
export type WaveEvents = ("available" | "pending" | "not_recorded" | "unsupported")
export type Code = string
export type Message = string
export type Severity = ("info" | "warning" | "error")
export type ActRoot = string
export type Capabilities = CapabilityOut[]
export type Commit = (string | null)
export type CudaAvailable = (boolean | null)
export type Diagnostics = DiagnosticOut[]
export type ExpectedCommit = (string | null)
export type Python = string
export type Torch = (string | null)
export type TrackedChanges = (boolean | null)
export type Usable = boolean
export type Code1 = string
export type Message1 = string
export type Retryable = boolean
export type Kind1 = ("layer_state" | "run_result" | "spec" | "coverage")
export type Label = string
export type LayerId = (number | null)
export type Neuron = (number | null)
export type RefId = string
export type RunId1 = (string | null)
export type Value = string
export type LayerId1 = (number | null)
export type ModelId = string
export type Neuron1 = (number | null)
export type RunId2 = (string | null)
export type Question = string
export type AnswerId = string
export type Evidence1 = EvidenceRef[]
export type Provider = string
export type ProviderKind = ("fake" | "real")
export type Question1 = string
export type Sections = AnswerSection[]
export type ElapsedS = number
export type Index = number
export type Input = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Iteration = number
export type Kind2 = string
export type Output = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type SeedInput = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type SeedOutput = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Severity1 = (number | ("Infinity" | "-Infinity" | "NaN"))
export type SpecRow = number
export type Strategy = (string | null)
export type TrueClass = (number | null)
export type Depth = number
export type ElapsedS1 = number
export type Input1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Iteration1 = number
export type SeedInput1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type SeedRow = number
export type Strategy1 = (string | null)
export type Violation = boolean
export type Activation = number
export type Boundary = number
export type Gradient = number
export type Pgd = number
export type Random = number
export type ActivationThreshold = number
export type CoverageStrategy = ("GlobalCov" | "BestInputCov")
export type MaxIterations = number
export type PerturbMode = ("adaptive_scalar" | "adaptive_perdim" | "fixed")
export type PerturbScale = number
export type PgdRestarts = number
export type PgdRestartsBinarized = number
export type RngSeed = number
export type SeedSelectionStrategy = ("energy" | "random")
export type StopOnFirst = boolean
export type Corpus = number
export type Counterexamples = number
export type Coverage = number
export type ElapsedS2 = number
export type Iteration2 = number
export type Input2 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Output1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Row = number
export type Name1 = string
export type Selected = number
export type Violations = number
export type Weight = number
export type ActStatus = string
export type CounterexampleCount = number
export type CoverageStrategy1 = string
export type Device = string
export type ElapsedS3 = number
export type Iterations = number
export type NeuronCoverage = number
export type NeverActivatedCount = number
export type NeverActivatedSample = string[]
export type RngSeed1 = number
export type SeedsExplored = number
export type Stopped = boolean
export type TotalMutations = number
export type Availability1 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Counterexamples1 = FuzzCounterexampleOut[]
export type Frames = FuzzFrameOut[]
export type RunId3 = string
export type SavedAt = string
export type Saved = SavedCounterexampleOut[]
export type Seeds = FuzzSeedOut[]
export type Status = ("queued" | "running" | "completed" | "failed")
export type Strategies = FuzzStrategyOut[]
export type Timeline = FuzzPointOut[]
export type Service = string
export type Status1 = "ok"
export type Version = string
export type Center = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Dataset1 = (string | null)
export type Kind3 = string
export type LayerId2 = number
export type Lb = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Shape = number[]
export type Ub = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type InVars = number
export type Kind4 = string
export type LayerId3 = number
export type OutVars = number
export type OutputShape = (number[] | null)
export type Name2 = string
export type Shape1 = (number[] | null)
export type Value1 = (string | null)
export type Params = ParamOut[]
export type Preds = number[]
export type Succs = number[]
export type BeforeLayerIds = number[]
export type Kind5 = string
export type LayerId4 = number
export type Lb1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Shape2 = number[]
export type Stage = "after"
export type Ub1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Availability2 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Layers = LayerStateOut[]
export type Method = ("interval" | null)
export type RunId4 = string
export type Source1 = (LoadVnnlibRequest | LoadTorchRequest)
export type Benchmark = string
export type Kind6 = "vnnlib"
export type Onnx1 = string
export type Vnnlib = string
export type Eps = number
export type Index1 = number
export type Indices = ([number, ...(number)[]] | null)
export type Kind7 = "torch"
export type SourceId1 = string
export type ActCommit = (string | null)
export type InputDim = number
export type InputSpecs = InputSpecOut[]
export type Layers1 = LayerOut[]
export type ModelId1 = string
export type OutputDim = number
export type Kind8 = string
export type LayerId5 = number
export type Matrix = (number[][] | null)
export type Rows = number
export type Text1 = string
export type Thresholds = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type TrueClass1 = (number | null)
export type Sha256 = string
export type ActPath = string
export type Description1 = string
export type Methods = ("interval" | "bab" | "fuzz")[]
export type ModelId2 = string
export type ElapsedS4 = number
export type Nodes = (number | null)
export type Status2 = string
export type Sha2561 = string
export type Source2 = ("catalog" | "vnnlib" | "torch")
export type ClientId = string
/**
 * Browsers with a heartbeat inside the window
 */
export type Online = number
/**
 * Seconds a heartbeat keeps a browser counted
 */
export type WindowS = number
export type Availability3 = ("available" | "not_configured")
export type Kind9 = ("fake" | "real")
export type Name3 = string
export type Note = string
export type Providers = ProviderOut[]
export type At = string
export type Kind10 = ("run.queued" | "run.started" | "run.stop_requested" | "run.completed" | "run.failed" | "bab.summary" | "fuzz.progress")
export type RunId5 = string
export type Seq = number
export type Status3 = ("queued" | "running" | "completed" | "failed")
export type ActCommit1 = (string | null)
export type ClientRequestId = (string | null)
export type CreatedAt = string
export type Domain = (("interval" | "dual" | "hybridz") | null)
export type FinishedAt = (string | null)
export type LastSeq = number
export type MatchesNative = (boolean | null)
export type Method1 = ("interval" | "bab" | "fuzz")
export type ModelId3 = string
export type ModelSha256 = string
export type ActStatus1 = string
export type BabSummary = ({
[k: string]: string | number | boolean | null
} | null)
export type Counterexample = (number[] | null)
export type Device1 = (string | null)
export type ElapsedS5 = number
export type Verdict = ("certified" | "falsified" | "unknown" | "timeout" | "error")
export type RunId6 = string
export type StartedAt = (string | null)
export type Status4 = ("queued" | "running" | "completed" | "failed")
export type TimeBudgetS = number
export type Runs = RunOut[]
export type ClientRequestId1 = (string | null)
export type Domain1 = (("interval" | "dual" | "hybridz") | null)
export type Method2 = ("interval" | "bab" | "fuzz")
export type ModelId4 = string
export type TimeBudgetS1 = number
export type Dataset2 = string
export type Index2 = number
export type Label1 = number
export type Pixels = number[]
export type Shape3 = number[]
export type Size = number
export type Index3 = number
export type Content = string
export type LicenseFingerprint = (string | null)
export type LicenseSource = ("uploaded" | "environment" | "none")
export type LicenseState = ("licensed" | "restricted" | "invalid" | "not_installed")
export type LicenseUpdatedAt = (string | null)
export type Message2 = string
export type Solver = "gurobi"
export type UsedByMethods = ("interval" | "bab" | "fuzz")[]
export type Version1 = (string | null)
export type Classifiers = ClassifierSourceOut[]
export type Benchmark1 = string
export type Onnx2 = string
export type Vnnlib2 = string
export type Instances = VnnlibInstanceOut[]
export type Vnnlib1 = VnnlibBenchmarkOut[]
export type VnnlibRoot = string

export interface ActGuiWire {
AnswerSection?: AnswerSection
CapabilityOut?: CapabilityOut
ClassifierSourceOut?: ClassifierSourceOut
CoverageOut?: CoverageOut
DiagnosticOut?: DiagnosticOut
EngineInfoOut?: EngineInfoOut
ErrorBody?: ErrorBody
ErrorResponse?: ErrorResponse
EvidenceRef?: EvidenceRef
ExplainRequest?: ExplainRequest
ExplainResponse?: ExplainResponse
FuzzCounterexampleOut?: FuzzCounterexampleOut
FuzzFrameOut?: FuzzFrameOut
FuzzMutationWeights?: FuzzMutationWeights
FuzzOptions?: FuzzOptions
FuzzPointOut?: FuzzPointOut
FuzzSeedOut?: FuzzSeedOut
FuzzStrategyOut?: FuzzStrategyOut
FuzzSummaryOut?: FuzzSummaryOut
FuzzingOut?: FuzzingOut
HealthOut?: HealthOut
InputSpecOut?: InputSpecOut
LayerOut?: LayerOut
LayerStateOut?: LayerStateOut
LayerStatesOut?: LayerStatesOut
LoadModelBody?: LoadModelBody
LoadTorchRequest?: LoadTorchRequest
LoadVnnlibRequest?: LoadVnnlibRequest
ModelDescriptionOut?: ModelDescriptionOut
ModelSummary?: ModelSummary
NativeResult?: NativeResult
OutputSpecOut?: OutputSpecOut
ParamOut?: ParamOut
PresenceHeartbeat?: PresenceHeartbeat
PresenceOut?: PresenceOut
ProviderList?: ProviderList
ProviderOut?: ProviderOut
RunEvent?: RunEvent
RunList?: RunList
RunOut?: RunOut
RunRequest?: RunRequest
RunResultOut?: RunResultOut
SampleOut?: SampleOut
SaveCounterexampleRequest?: SaveCounterexampleRequest
SavedCounterexampleOut?: SavedCounterexampleOut
SelectionContext?: SelectionContext
SolverLicenseUpload?: SolverLicenseUpload
SolverStatusOut?: SolverStatusOut
SourcesOut?: SourcesOut
VnnlibBenchmarkOut?: VnnlibBenchmarkOut
VnnlibInstanceOut?: VnnlibInstanceOut
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "AnswerSection".
 */
export interface AnswerSection {
evidence: Evidence
kind: Kind
text: Text
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "CapabilityOut".
 */
export interface CapabilityOut {
availability: Availability
name: Name
source: Source
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ClassifierSourceOut".
 */
export interface ClassifierSourceOut {
dataset: Dataset
description: Description
onnx: Onnx
source_id: SourceId
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "CoverageOut".
 */
export interface CoverageOut {
final_summary: FinalSummary
node_events: NodeEvents
reason: Reason
run_id: RunId
summary: Summary
wave_events: WaveEvents
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "DiagnosticOut".
 */
export interface DiagnosticOut {
code: Code
message: Message
severity: Severity
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineInfoOut".
 */
export interface EngineInfoOut {
act_root: ActRoot
capabilities: Capabilities
commit: Commit
cuda_available: CudaAvailable
diagnostics: Diagnostics
expected_commit: ExpectedCommit
python: Python
torch: Torch
tracked_changes: TrackedChanges
usable: Usable
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ErrorBody".
 */
export interface ErrorBody {
code: Code1
message: Message1
retryable?: Retryable
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ErrorResponse".
 */
export interface ErrorResponse {
error: ErrorBody
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EvidenceRef".
 */
export interface EvidenceRef {
kind: Kind1
label: Label
layer_id: LayerId
neuron: Neuron
ref_id: RefId
run_id: RunId1
value: Value
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ExplainRequest".
 */
export interface ExplainRequest {
context: SelectionContext
question: Question
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SelectionContext".
 */
export interface SelectionContext {
layer_id?: LayerId1
model_id: ModelId
neuron?: Neuron1
run_id?: RunId2
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ExplainResponse".
 */
export interface ExplainResponse {
answer_id: AnswerId
context: SelectionContext
evidence: Evidence1
provider: Provider
provider_kind: ProviderKind
question: Question1
sections: Sections
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzCounterexampleOut".
 */
export interface FuzzCounterexampleOut {
elapsed_s: ElapsedS
index: Index
input: Input
iteration: Iteration
kind: Kind2
output: Output
seed_input: SeedInput
seed_output?: SeedOutput
severity: Severity1
spec_row: SpecRow
strategy: Strategy
true_class: TrueClass
}
/**
 * Lane 0 of the batch ACTFuzzer mutated in one iteration. Display only; not a counterexample unless violation.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzFrameOut".
 */
export interface FuzzFrameOut {
counterexample?: (FuzzCounterexampleOut | null)
depth: Depth
elapsed_s: ElapsedS1
input: Input1
iteration: Iteration1
seed_input: SeedInput1
seed_row: SeedRow
strategy: Strategy1
violation: Violation
}
/**
 * Relative selection weights of ACT's mutation operators (ACT normalizes them; 0 disables one).
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzMutationWeights".
 */
export interface FuzzMutationWeights {
activation?: Activation
boundary?: Boundary
gradient?: Gradient
pgd?: Pgd
random?: Random
}
/**
 * ACTFuzzer settings for method "fuzz". Defaults other than max_iterations equal the fuzzing section of
 * the pinned ACT act/config/pipeline.yaml (drift-checked in fuzzing/test_fuzzing.py); the browser reads them from
 * GET /api/fuzz/defaults. Output, tracing and reporting stay owned by engine_bridge.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzOptions".
 */
export interface FuzzOptions {
activation_threshold?: ActivationThreshold
coverage_strategy?: CoverageStrategy
max_iterations?: MaxIterations
mutation_weights?: FuzzMutationWeights
perturb_mode?: PerturbMode
perturb_scale?: PerturbScale
pgd_restarts?: PgdRestarts
pgd_restarts_binarized?: PgdRestartsBinarized
rng_seed?: RngSeed
seed_selection_strategy?: SeedSelectionStrategy
stop_on_first?: StopOnFirst
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzPointOut".
 */
export interface FuzzPointOut {
corpus: Corpus
counterexamples: Counterexamples
coverage: Coverage
elapsed_s: ElapsedS2
iteration: Iteration2
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzSeedOut".
 */
export interface FuzzSeedOut {
input: Input2
output: Output1
row: Row
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzStrategyOut".
 */
export interface FuzzStrategyOut {
name: Name1
selected: Selected
violations: Violations
weight: Weight
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzSummaryOut".
 */
export interface FuzzSummaryOut {
act_status: ActStatus
counterexample_count: CounterexampleCount
coverage_strategy: CoverageStrategy1
device: Device
elapsed_s: ElapsedS3
iterations: Iterations
neuron_coverage: NeuronCoverage
never_activated_count: NeverActivatedCount
never_activated_sample: NeverActivatedSample
rng_seed: RngSeed1
seeds_explored: SeedsExplored
stopped?: Stopped
total_mutations: TotalMutations
}
/**
 * ACTFuzzer record of a run. While running, timeline comes from committed fuzz.progress events
 * and frames holds only the latest mutated input the worker reported (kept in memory, not recorded).
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzingOut".
 */
export interface FuzzingOut {
availability: Availability1
config: Config
counterexamples: Counterexamples1
frames?: Frames
options: (FuzzOptions | null)
provenance: Provenance
run_id: RunId3
saved?: Saved
seeds?: Seeds
status: Status
strategies: Strategies
summary: (FuzzSummaryOut | null)
timeline: Timeline
}
export interface Config {
[k: string]: string | number | boolean | null
}
export interface Provenance {
[k: string]: string
}
/**
 * An ACT counterexample the user saved on its run record (user annotation; ACT decided the violation).
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SavedCounterexampleOut".
 */
export interface SavedCounterexampleOut {
counterexample: FuzzCounterexampleOut
saved_at: SavedAt
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "HealthOut".
 */
export interface HealthOut {
service: Service
status: Status1
version: Version
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "InputSpecOut".
 */
export interface InputSpecOut {
center: Center
dataset: Dataset1
kind: Kind3
layer_id: LayerId2
lb: Lb
shape: Shape
ub: Ub
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerOut".
 */
export interface LayerOut {
in_vars: InVars
kind: Kind4
layer_id: LayerId3
out_vars: OutVars
output_shape: OutputShape
params: Params
preds: Preds
succs: Succs
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ParamOut".
 */
export interface ParamOut {
name: Name2
shape: Shape1
value: Value1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStateOut".
 */
export interface LayerStateOut {
before_layer_ids: BeforeLayerIds
kind: Kind5
layer_id: LayerId4
lb: Lb1
shape: Shape2
stage: Stage
ub: Ub1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStatesOut".
 */
export interface LayerStatesOut {
availability: Availability2
layers: Layers
method: Method
provenance: Provenance1
run_id: RunId4
}
export interface Provenance1 {
[k: string]: string
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LoadModelBody".
 */
export interface LoadModelBody {
source: Source1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LoadVnnlibRequest".
 */
export interface LoadVnnlibRequest {
benchmark: Benchmark
kind: Kind6
onnx: Onnx1
vnnlib: Vnnlib
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LoadTorchRequest".
 */
export interface LoadTorchRequest {
eps: Eps
index: Index1
indices?: Indices
kind: Kind7
source_id: SourceId1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ModelDescriptionOut".
 */
export interface ModelDescriptionOut {
act_commit: ActCommit
input_dim: InputDim
input_specs: InputSpecs
layers: Layers1
model_id: ModelId1
output_dim: OutputDim
output_spec: (OutputSpecOut | null)
sha256: Sha256
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "OutputSpecOut".
 */
export interface OutputSpecOut {
kind: Kind8
layer_id: LayerId5
matrix: Matrix
rows: Rows
text: Text1
thresholds: Thresholds
true_class: TrueClass1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ModelSummary".
 */
export interface ModelSummary {
act_path: ActPath
description: Description1
methods: Methods
model_id: ModelId2
native: Native
params?: Params1
sha256: Sha2561
source?: Source2
}
export interface Native {
[k: string]: NativeResult
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "NativeResult".
 */
export interface NativeResult {
elapsed_s: ElapsedS4
nodes: Nodes
status: Status2
}
export interface Params1 {
[k: string]: string | number | boolean | null
}
/**
 * One browser's heartbeat; client_id is a random id kept in that browser's localStorage.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PresenceHeartbeat".
 */
export interface PresenceHeartbeat {
client_id: ClientId
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PresenceOut".
 */
export interface PresenceOut {
online: Online
window_s: WindowS
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ProviderList".
 */
export interface ProviderList {
providers: Providers
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ProviderOut".
 */
export interface ProviderOut {
availability: Availability3
kind: Kind9
name: Name3
note: Note
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunEvent".
 */
export interface RunEvent {
at: At
kind: Kind10
payload: Payload
run_id: RunId5
seq: Seq
status: Status3
}
export interface Payload {
[k: string]: string | number | boolean | null
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunList".
 */
export interface RunList {
runs: Runs
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunOut".
 */
export interface RunOut {
act_commit: ActCommit1
client_request_id: ClientRequestId
created_at: CreatedAt
domain: Domain
error: (ErrorBody | null)
finished_at: FinishedAt
last_seq: LastSeq
matches_native: MatchesNative
method: Method1
model_id: ModelId3
model_sha256: ModelSha256
native_reference: (NativeResult | null)
result: (RunResultOut | null)
run_id: RunId6
started_at: StartedAt
status: Status4
time_budget_s: TimeBudgetS
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunResultOut".
 */
export interface RunResultOut {
act_status: ActStatus1
bab_summary: BabSummary
counterexample: Counterexample
device?: Device1
elapsed_s: ElapsedS5
metadata: Metadata
verdict: Verdict
}
export interface Metadata {
[k: string]: string | number | boolean | null
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunRequest".
 */
export interface RunRequest {
client_request_id?: ClientRequestId1
domain?: Domain1
fuzz?: (FuzzOptions | null)
method: Method2
model_id: ModelId4
time_budget_s?: TimeBudgetS1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SampleOut".
 */
export interface SampleOut {
dataset: Dataset2
index: Index2
label: Label1
pixels: Pixels
shape: Shape3
size: Size
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SaveCounterexampleRequest".
 */
export interface SaveCounterexampleRequest {
index: Index3
}
/**
 * Text of a solver license file (e.g. gurobi.lic). Stored server-side; never returned.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SolverLicenseUpload".
 */
export interface SolverLicenseUpload {
content: Content
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SolverStatusOut".
 */
export interface SolverStatusOut {
license_fingerprint: LicenseFingerprint
license_source: LicenseSource
license_state: LicenseState
license_updated_at: LicenseUpdatedAt
message: Message2
solver: Solver
used_by_methods: UsedByMethods
version: Version1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "SourcesOut".
 */
export interface SourcesOut {
classifiers: Classifiers
vnnlib: Vnnlib1
vnnlib_root: VnnlibRoot
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "VnnlibBenchmarkOut".
 */
export interface VnnlibBenchmarkOut {
benchmark: Benchmark1
instances: Instances
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "VnnlibInstanceOut".
 */
export interface VnnlibInstanceOut {
onnx: Onnx2
vnnlib: Vnnlib2
}
