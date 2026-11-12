/* Generated from visual_bench/schemas.py by scripts/gen_types.mjs. Do not edit. */

export type Evidence = string[]
export type Kind = ("observation" | "interpretation" | "hypothesis" | "missing")
export type Text = string
export type Capability = string
export type Detail = string
export type Ok = boolean
export type Symbol = string
export type Axis = number
export type Lb = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Ub = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Intervals = BabIntervalOut[]
export type Kind1 = string
export type LayerId = number
export type Neuron = number
export type Sign = number
export type SpecRows = number[]
export type Phases = BabPhaseOut[]
export type Active = (number | null)
export type Inactive = (number | null)
export type Kind2 = (string | null)
export type LayerId1 = number
export type LbMin = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Neurons = number
export type UbMax = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Unstable = (number | null)
export type BoundKind = (string | null)
export type Bound = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Children1 = number
export type CreatedWave = number
export type Depth = number
export type Descendants = number
export type EvictedWave = (number | null)
export type HiddenChildren = number
export type NodeId = number
export type Outcome = (string | null)
export type ParentId = number
export type SolvedWave = (number | null)
export type State = ("pending" | "branched" | "proved" | "falsified" | "retired" | "evicted" | "unresolved")
export type Children = BabNodeOut[]
export type Layers = BabLayerOut[]
export type Path = BabNodeOut[]
export type RunId = string
export type SolveStatus = (string | null)
export type Choices = string[]
export type Default = (boolean | number | string)
export type Description = string
export type ExclusiveMinimum = boolean
export type Group = string
export type Kind3 = ("int" | "float" | "bool" | "choice")
export type Maximum = (number | null)
export type Minimum = (number | null)
export type Name = string
export type Available = boolean
export type Options = BabOptionOut[]
export type Evicted = number
export type Falsified = number
export type Pending = number
export type Proved = number
export type Retired = number
export type Unresolved = number
export type FrontierSize = number
export type NodeId1 = (number | null)
export type Reason = string
export type Seq = number
export type Status = string
export type TMs = number
export type Wave = number
export type Availability = ("available" | "pending" | "not_recorded" | "unsupported")
export type Complete = boolean
export type IgnoredRecords = number
export type Limit = number
export type Nodes = BabNodeOut[]
export type Path1 = BabNodeOut[]
export type Reason1 = string
export type RecordingError = (string | null)
export type Root = number
export type RunId1 = string
export type Status1 = ("queued" | "running" | "completed" | "failed")
export type Truncated = boolean
export type Branched = number
export type Created = number
export type Evicted1 = number
export type FrontierSize1 = number
export type MinBound = (number | ("Infinity" | "-Infinity" | "NaN") | null)
export type Proved1 = number
export type Retired1 = number
export type Seq1 = number
export type Solved = number
export type TMs1 = number
export type Unresolved1 = number
export type Wave1 = number
export type Waves = BabWaveOut[]
export type Branch = (string | null)
export type Commit = (string | null)
export type Kind4 = ("baseline" | "branch")
export type Remote = (string | null)
export type Availability1 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Name1 = string
export type Source = string
export type Dataset = string
export type Description1 = string
export type Onnx = string
export type SourceId = string
export type Count = number
/**
 * ISO 3166-1 alpha-2 from Cloudflare CF-IPCountry; null when unknown or local
 */
export type Country = (string | null)
export type FinalSummary = ("available" | "pending" | "not_recorded" | "unsupported")
export type NodeEvents = ("available" | "pending" | "not_recorded" | "unsupported")
export type Reason2 = string
export type RunId2 = string
export type Summary = ({
[k: string]: string | number | boolean | null
} | null)
export type WaveEvents = ("available" | "pending" | "not_recorded" | "unsupported")
export type Code = string
export type Message = string
export type Severity = ("info" | "warning" | "error")
export type Alpha = ("fixed" | "optimize" | "optimize_refresh")
export type ForwardLinMaxPerturbed = number
export type Iterations = number
export type LrAlpha = number
export type LrDecay = number
export type MaxTimeS = number
export type PerClassAlpha = boolean
export type StagnationPatience = number
export type StagnationTol = number
export type Branches = string[]
export type Remote1 = string
export type Url = string
export type ActRoot = string
export type ApiChecks = ApiCheckOut[]
export type Capabilities = CapabilityOut[]
export type Commit1 = (string | null)
export type CudaAvailable = (boolean | null)
export type Diagnostics = DiagnosticOut[]
export type ExpectedCommit = (string | null)
export type Python = string
export type Branch1 = (string | null)
export type Commit2 = (string | null)
export type Kind5 = ("baseline" | "branch")
export type Remote2 = (string | null)
export type SwitchedAt = (string | null)
export type Url1 = (string | null)
export type Torch = (string | null)
export type TrackedChanges = (boolean | null)
export type Usable = boolean
export type Custom = boolean
export type Name2 = string
export type Url2 = string
export type CustomAllowed = boolean
export type Remotes = EngineRemoteOut[]
export type Branch2 = (string | null)
export type Remote3 = (string | null)
export type Url3 = (string | null)
export type Code1 = string
export type Message1 = string
export type Retryable = boolean
export type Kind6 = ("layer_state" | "run_result" | "spec" | "coverage")
export type Label = string
export type LayerId2 = (number | null)
export type Neuron1 = (number | null)
export type RefId = string
export type RunId3 = (string | null)
export type Value = string
export type LayerId3 = (number | null)
export type ModelId = string
export type Neuron2 = (number | null)
export type RunId4 = (string | null)
export type Question = string
export type AnswerId = string
export type Evidence1 = EvidenceRef[]
export type Provider = string
export type ProviderKind = ("fake" | "real")
export type Question1 = string
export type Sections = AnswerSection[]
export type Iteration = number
export type Rejected = string
export type Action = ("pause" | "resume" | "stop" | "update")
export type Changes = ({
[k: string]: number | boolean | string | {
[k: string]: number
} | null
} | null)
export type RequestId = string
export type RunId5 = string
export type Status2 = ("queued" | "duplicate")
export type Action1 = ("pause" | "resume" | "stop" | "update")
export type Changes1 = ({
[k: string]: number | boolean | string | {
[k: string]: number
} | null
} | null)
export type RequestId1 = string
export type Changes2 = FuzzConfigChangeOut[]
export type Paused = boolean
export type ElapsedS = number
export type Index = number
export type Input = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Iteration1 = number
export type Kind7 = string
export type Output = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type SeedInput = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type SeedOutput = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Severity1 = (number | ("Infinity" | "-Infinity" | "NaN"))
export type SpecRow = number
export type Strategy = (string | null)
export type TrueClass = (number | null)
export type Depth1 = number
export type ElapsedS1 = number
export type Input1 = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Iteration2 = number
export type SeedInput1 = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type SeedRow = number
export type Strategy1 = (string | null)
export type Violation = boolean
export type Activation = number
export type Boundary = number
export type Gradient = number
export type Pgd = number
export type Random = number
export type Choices1 = string[]
export type Default1 = (number | boolean | string | {
[k: string]: number
} | null)
export type Description2 = string
export type ExclusiveMinimum1 = boolean
export type Kind8 = ("int" | "float" | "bool" | "choice" | "weights")
export type Live1 = boolean
export type Maximum1 = (number | null)
export type Minimum1 = (number | null)
export type Name3 = string
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
export type LiveControl = boolean
export type Options1 = FuzzOptionOut[]
export type Corpus = number
export type Counterexamples = number
export type Coverage = number
export type ElapsedS2 = number
export type Iteration3 = number
export type Input2 = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Output1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Row = number
export type Name4 = string
export type Selected = number
export type Violations = number
export type Weight = number
export type ActStatus = string
export type CounterexampleCount = number
export type CoverageStrategy1 = string
export type Device = string
export type ElapsedS3 = number
export type Iterations1 = number
export type NeuronCoverage = number
export type NeverActivatedCount = number
export type NeverActivatedSample = string[]
export type RngSeed1 = number
export type SeedsExplored = number
export type StopReason = (string | null)
export type Stopped = boolean
export type TotalMutations = number
export type Availability2 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Counterexamples1 = FuzzCounterexampleOut[]
export type Frames = FuzzFrameOut[]
export type RunId6 = string
export type SavedAt = string
export type Saved = SavedCounterexampleOut[]
export type Seeds = FuzzSeedOut[]
export type Status3 = ("queued" | "running" | "completed" | "failed")
export type Strategies = FuzzStrategyOut[]
export type Timeline = FuzzPointOut[]
export type Instance = string
export type Service = string
export type Status4 = "ok"
export type Version = string
export type Tolerance = number
export type Center = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Dataset1 = (string | null)
export type Kind9 = string
export type LayerId4 = number
export type Lb1 = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Shape = number[]
export type Ub1 = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type InVars = number
export type Kind10 = string
export type LayerId5 = number
export type OutVars = number
export type OutputShape = (number[] | null)
export type Name5 = string
export type Shape1 = (number[] | null)
export type Value1 = (string | null)
export type Params = ParamOut[]
export type Preds = number[]
export type Succs = number[]
export type BeforeLayerIds = number[]
export type Kind11 = string
export type LayerId6 = number
export type Lb2 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Shape2 = number[]
export type Stage = ("after" | "pre")
export type Ub2 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Availability3 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Layers1 = LayerStateOut[]
export type Method = (("interval" | "dual" | "hybridz") | null)
export type RunId7 = string
export type Source1 = (LoadVnnlibRequest | LoadTorchRequest)
export type Benchmark = string
export type Kind12 = "vnnlib"
export type Onnx1 = string
export type Vnnlib = string
export type Vnnlibs = ([string, ...(string)[]] | null)
export type Eps = number
export type Index1 = number
export type Indices = ([number, ...(number)[]] | null)
export type Kind13 = "torch"
export type SourceId1 = string
export type ActCommit = (string | null)
export type InputDim = number
export type InputSpecs = InputSpecOut[]
export type Layers2 = LayerOut[]
export type ModelId1 = string
export type OutputDim = number
export type Kind14 = string
export type LayerId7 = number
export type Matrix = (number[][] | null)
export type Rows = number
export type Text1 = string
export type Thresholds = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type TrueClass1 = (number | null)
export type Sha256 = string
export type ActPath = string
export type Description3 = string
export type EngineCheck = (("same_commit" | "loads" | "load_failed" | "unchecked") | null)
export type Methods = ("interval" | "bab" | "fuzz")[]
export type ModelId2 = string
export type ElapsedS4 = number
export type Nodes1 = (number | null)
export type Status5 = string
export type Sha2561 = string
export type Source2 = ("catalog" | "vnnlib" | "torch")
export type ClientId = string
/**
 * Online browsers per country, largest first
 */
export type Countries = CountryCount[]
/**
 * Browsers with a heartbeat inside the window
 */
export type Online = number
/**
 * Seconds a heartbeat keeps a browser counted
 */
export type WindowS = number
export type Availability4 = ("available" | "pending" | "unavailable" | "not_recorded")
export type Complete1 = boolean
export type Domain = (("interval" | "dual" | "hybridz") | null)
export type IgnoredRecords1 = number
export type Domain1 = ("interval" | "dual" | "hybridz")
export type LayerId8 = number
export type Origin = string
export type Parent = (string | null)
export type Pass = string
export type Scope = string
export type Stage1 = string
export type Version1 = number
export type LatestRecordId = number
export type LayerKind = (string | null)
export type OutputShape1 = number[]
export type RecordCount = number
export type Layers3 = PropagationLayerSummaryOut[]
export type Kind15 = ("PhaseEvent" | "LayerBounds" | "Relaxation" | "DualBackward" | "SpecBound")
export type LayerKind1 = (string | null)
export type OutputShape2 = number[]
export type RecordId = number
export type Shape3 = number[]
export type TMs2 = number
export type Dtype = "float32"
export type Sha2562 = string
export type Shape4 = number[]
export type Phases1 = PropagationRecordOut[]
export type Records = PropagationRecordOut[]
export type RunId8 = string
export type ValueLimit = number
export type Availability5 = ("available" | "pending" | "unavailable" | "not_recorded")
export type Domain2 = (("interval" | "dual" | "hybridz") | null)
export type LayerId9 = number
export type Neuron3 = (number | null)
export type OutputShape3 = number[]
export type Kind16 = ("PhaseEvent" | "LayerBounds" | "Relaxation" | "DualBackward" | "SpecBound")
export type LayerKind2 = (string | null)
export type OutputShape4 = number[]
export type RecordId1 = number
export type Shape5 = number[]
export type TMs3 = number
export type Records1 = PropagationLayerRecordOut[]
export type RunId9 = string
export type ValueLimit1 = number
export type Availability6 = ("available" | "not_configured")
export type Kind17 = ("fake" | "real")
export type Name6 = string
export type Note = string
export type Providers = ProviderOut[]
export type ActStatus1 = string
export type Counterexample = (number[] | null)
export type CounterexampleOutput = (number[] | null)
export type CounterexampleOutputError = (string | null)
export type Row1 = number
export type Verdict = ("certified" | "falsified" | "unknown" | "timeout" | "error")
export type Errors = number
export type Exception = (string | null)
export type Location = (string | null)
export type Messages = string[]
export type Warnings = number
export type At = string
export type Kind18 = ("run.queued" | "run.started" | "run.stop_requested" | "run.completed" | "run.failed" | "bab.summary" | "fuzz.progress" | "fuzz.control" | "fuzz.paused" | "fuzz.resumed" | "verify.propagation" | "verify.bab")
export type Payload = ({
[k: string]: string | number | boolean | null
} | PropagationRecordOut | FuzzConfigChangeOut)
export type RunId10 = string
export type Seq2 = number
export type Status6 = ("queued" | "running" | "completed" | "failed")
export type ActCommit1 = (string | null)
export type Bab = ({
[k: string]: boolean | number | string
} | null)
export type ClientRequestId = (string | null)
export type CounterexampleSavedAt = (string | null)
export type CreatedAt = string
export type Domain3 = (("interval" | "dual" | "hybridz") | null)
export type FinishedAt = (string | null)
export type LastSeq = number
export type MatchesNative = (boolean | null)
export type Method1 = ("interval" | "bab" | "fuzz")
export type ModelId3 = string
export type ModelSha256 = string
export type ActStatus2 = string
export type BabSummary = ({
[k: string]: string | number | boolean | null
} | null)
export type Counterexample1 = (number[] | null)
export type CounterexampleOutput1 = (number[] | null)
export type CounterexampleOutputError1 = (string | null)
export type CounterexampleRow = (number | null)
export type Device1 = (string | null)
export type ElapsedS5 = number
export type Rows1 = RowVerdictOut[]
export type Verdict1 = ("certified" | "falsified" | "unknown" | "timeout" | "error")
export type RunId11 = string
export type SavedCounterexampleRows = number[]
export type StartedAt = (string | null)
export type Status7 = ("queued" | "running" | "completed" | "failed")
export type TimeBudgetS = number
export type Runs = RunOut[]
export type Bab1 = ({
[k: string]: boolean | number | string
} | null)
export type ClientRequestId1 = (string | null)
export type Domain4 = (("interval" | "dual" | "hybridz") | null)
export type Method2 = ("interval" | "bab" | "fuzz")
export type ModelId4 = string
export type TimeBudgetS1 = number
export type Dataset2 = string
export type Index2 = number
export type Label1 = number
export type Pixels = number[]
export type Shape6 = number[]
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
export type Version2 = (string | null)
export type Classifiers = ClassifierSourceOut[]
export type Benchmark1 = string
export type Onnx2 = string
export type Vnnlib2 = string
export type Instances = VnnlibInstanceOut[]
export type Vnnlib1 = VnnlibBenchmarkOut[]
export type VnnlibRoot = string

export interface ActGuiWire {
AnswerSection?: AnswerSection
ApiCheckOut?: ApiCheckOut
BabBranchOut?: BabBranchOut
BabIntervalOut?: BabIntervalOut
BabLayerOut?: BabLayerOut
BabNodeDetailOut?: BabNodeDetailOut
BabNodeOut?: BabNodeOut
BabOptionOut?: BabOptionOut
BabOptionsOut?: BabOptionsOut
BabPhaseOut?: BabPhaseOut
BabSharesOut?: BabSharesOut
BabTerminalOut?: BabTerminalOut
BabTreeOut?: BabTreeOut
BabWaveOut?: BabWaveOut
BuiltWithOut?: BuiltWithOut
CapabilityOut?: CapabilityOut
ClassifierSourceOut?: ClassifierSourceOut
CountryCount?: CountryCount
CoverageOut?: CoverageOut
DiagnosticOut?: DiagnosticOut
DualOptions?: DualOptions
EngineBranchesOut?: EngineBranchesOut
EngineInfoOut?: EngineInfoOut
EngineRemoteOut?: EngineRemoteOut
EngineSourceOut?: EngineSourceOut
EngineSourcesOut?: EngineSourcesOut
EngineSwitchRequest?: EngineSwitchRequest
ErrorBody?: ErrorBody
ErrorResponse?: ErrorResponse
EvidenceRef?: EvidenceRef
ExplainRequest?: ExplainRequest
ExplainResponse?: ExplainResponse
FuzzConfigChangeOut?: FuzzConfigChangeOut
FuzzControlOut?: FuzzControlOut
FuzzControlRequest?: FuzzControlRequest
FuzzControlStateOut?: FuzzControlStateOut
FuzzCounterexampleOut?: FuzzCounterexampleOut
FuzzFrameOut?: FuzzFrameOut
FuzzMutationWeights?: FuzzMutationWeights
FuzzOptionOut?: FuzzOptionOut
FuzzOptions?: FuzzOptions
FuzzOptionsSchemaOut?: FuzzOptionsSchemaOut
FuzzPointOut?: FuzzPointOut
FuzzSeedOut?: FuzzSeedOut
FuzzStrategyOut?: FuzzStrategyOut
FuzzSummaryOut?: FuzzSummaryOut
FuzzingOut?: FuzzingOut
HealthOut?: HealthOut
HybridzOptions?: HybridzOptions
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
PropagationIndexOut?: PropagationIndexOut
PropagationKeyOut?: PropagationKeyOut
PropagationLayerOut?: PropagationLayerOut
PropagationLayerRecordOut?: PropagationLayerRecordOut
PropagationLayerSummaryOut?: PropagationLayerSummaryOut
PropagationRecordOut?: PropagationRecordOut
PropagationTensorOut?: PropagationTensorOut
ProviderList?: ProviderList
ProviderOut?: ProviderOut
RowVerdictOut?: RowVerdictOut
RunDiagnosticsOut?: RunDiagnosticsOut
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
VerifyDefaults?: VerifyDefaults
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
 * One ACT symbol a capability's bridge adapter calls, checked on the active checkout.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ApiCheckOut".
 */
export interface ApiCheckOut {
capability: Capability
detail: Detail
ok: Ok
symbol: Symbol
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabBranchOut".
 */
export interface BabBranchOut {
intervals?: Intervals
kind: Kind1
phases?: Phases
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabIntervalOut".
 */
export interface BabIntervalOut {
axis: Axis
lb: Lb
ub: Ub
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabPhaseOut".
 */
export interface BabPhaseOut {
layer_id: LayerId
neuron: Neuron
sign: Sign
spec_rows: SpecRows
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabLayerOut".
 */
export interface BabLayerOut {
active?: Active
inactive?: Inactive
kind: Kind2
layer_id: LayerId1
lb_min: LbMin
neurons: Neurons
ub_max: UbMax
unstable?: Unstable
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabNodeDetailOut".
 */
export interface BabNodeDetailOut {
bound_kind: BoundKind
children: Children
layers: Layers
node: BabNodeOut
path: Path
run_id: RunId
solve_status: SolveStatus
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabNodeOut".
 */
export interface BabNodeOut {
bound: Bound
branch: (BabBranchOut | null)
children: Children1
created_wave: CreatedWave
depth: Depth
descendants: Descendants
evicted_wave: EvictedWave
hidden_children?: HiddenChildren
node_id: NodeId
outcome: Outcome
parent_id: ParentId
solved_wave: SolvedWave
state: State
}
/**
 * One verify_bab_batched setting from ACT's bab_gui.bab_options; kinds, limits and defaults are ACT's.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabOptionOut".
 */
export interface BabOptionOut {
choices: Choices
default: Default
description: Description
exclusive_minimum: ExclusiveMinimum
group: Group
kind: Kind3
maximum: Maximum
minimum: Minimum
name: Name
}
/**
 * GET /api/verification/bab-options: every BaB setting of the active ACT (capability verify.bab.options).
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabOptionsOut".
 */
export interface BabOptionsOut {
available: Available
options: Options
}
/**
 * The focused subtree as fractions per leaf state (they sum to 1), each node's share split equally among its
 * children: a measure of the split tree, not of input volume, and never a verdict.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabSharesOut".
 */
export interface BabSharesOut {
evicted: Evicted
falsified: Falsified
pending: Pending
proved: Proved
retired: Retired
unresolved: Unresolved
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabTerminalOut".
 */
export interface BabTerminalOut {
frontier_size: FrontierSize
node_id: NodeId1
reason: Reason
seq: Seq
status: Status
t_ms: TMs
wave: Wave
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabTreeOut".
 */
export interface BabTreeOut {
availability: Availability
complete: Complete
counts: Counts
ignored_records?: IgnoredRecords
limit: Limit
nodes: Nodes
path: Path1
reason: Reason1
recording_error?: RecordingError
root: Root
run_id: RunId1
shares: (BabSharesOut | null)
status: Status1
terminal: (BabTerminalOut | null)
truncated: Truncated
waves: Waves
}
export interface Counts {
[k: string]: number
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BabWaveOut".
 */
export interface BabWaveOut {
branched: Branched
created: Created
evicted: Evicted1
frontier_size: FrontierSize1
min_bound: MinBound
proved: Proved1
retired: Retired1
seq: Seq1
solved: Solved
t_ms: TMs1
unresolved: Unresolved1
wave: Wave1
}
/**
 * The ACT engine a model was built on: its commit and where that code came from.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "BuiltWithOut".
 */
export interface BuiltWithOut {
branch?: Branch
commit: Commit
kind: Kind4
remote?: Remote
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "CapabilityOut".
 */
export interface CapabilityOut {
availability: Availability1
name: Name1
source: Source
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ClassifierSourceOut".
 */
export interface ClassifierSourceOut {
dataset: Dataset
description: Description1
onnx: Onnx
source_id: SourceId
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "CountryCount".
 */
export interface CountryCount {
count: Count
country: Country
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "CoverageOut".
 */
export interface CoverageOut {
final_summary: FinalSummary
node_events: NodeEvents
reason: Reason2
run_id: RunId2
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
 * DualSolver settings of a dual-domain verify_once run. Defaults equal ACT's DualConfig (drift-checked in
 * test_verification.py); with every default the run calls verify_once exactly as without options.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "DualOptions".
 */
export interface DualOptions {
alpha?: Alpha
forward_lin_max_perturbed?: ForwardLinMaxPerturbed
iterations?: Iterations
lr_alpha?: LrAlpha
lr_decay?: LrDecay
max_time_s?: MaxTimeS
per_class_alpha?: PerClassAlpha
stagnation_patience?: StagnationPatience
stagnation_tol?: StagnationTol
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineBranchesOut".
 */
export interface EngineBranchesOut {
branches: Branches
remote: Remote1
url: Url
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineInfoOut".
 */
export interface EngineInfoOut {
act_root: ActRoot
api_checks: ApiChecks
capabilities: Capabilities
commit: Commit1
cuda_available: CudaAvailable
diagnostics: Diagnostics
expected_commit: ExpectedCommit
python: Python
source: EngineSourceOut
torch: Torch
tracked_changes: TrackedChanges
usable: Usable
}
/**
 * Where the imported ACT code comes from: the pinned baseline checkout or a staged branch head.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineSourceOut".
 */
export interface EngineSourceOut {
branch?: Branch1
commit?: Commit2
kind: Kind5
remote?: Remote2
switched_at?: SwitchedAt
url?: Url1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineRemoteOut".
 */
export interface EngineRemoteOut {
custom: Custom
name: Name2
url: Url2
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineSourcesOut".
 */
export interface EngineSourcesOut {
active: EngineSourceOut
custom_allowed: CustomAllowed
remotes: Remotes
}
/**
 * Neither remote nor url: the pinned baseline. Otherwise the branch head of a listed remote (by name)
 * or of a user-entered https git URL.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "EngineSwitchRequest".
 */
export interface EngineSwitchRequest {
branch?: Branch2
remote?: Remote3
url?: Url3
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
kind: Kind6
label: Label
layer_id: LayerId2
neuron: Neuron1
ref_id: RefId
run_id: RunId3
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
layer_id?: LayerId3
model_id: ModelId
neuron?: Neuron2
run_id?: RunId4
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
 * via the `definition` "FuzzConfigChangeOut".
 */
export interface FuzzConfigChangeOut {
applied: Applied
iteration: Iteration
rejected: Rejected
requested: Requested
}
export interface Applied {
[k: string]: number | boolean | string | {
[k: string]: number
} | null
}
export interface Requested {
[k: string]: number | boolean | string | {
[k: string]: number
} | null
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzControlOut".
 */
export interface FuzzControlOut {
action: Action
changes: Changes
request_id: RequestId
run_id: RunId5
status: Status2
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzControlRequest".
 */
export interface FuzzControlRequest {
action: Action1
changes?: Changes1
request_id: RequestId1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzControlStateOut".
 */
export interface FuzzControlStateOut {
changes: Changes2
live: Live
paused: Paused
}
export interface Live {
[k: string]: number | boolean | string | {
[k: string]: number
} | null
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzCounterexampleOut".
 */
export interface FuzzCounterexampleOut {
elapsed_s: ElapsedS
index: Index
input: Input
iteration: Iteration1
kind: Kind7
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
depth: Depth1
elapsed_s: ElapsedS1
input: Input1
iteration: Iteration2
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
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "FuzzOptionOut".
 */
export interface FuzzOptionOut {
choices: Choices1
default: Default1
description: Description2
exclusive_minimum: ExclusiveMinimum1
kind: Kind8
live: Live1
maximum: Maximum1
minimum: Minimum1
name: Name3
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
 * via the `definition` "FuzzOptionsSchemaOut".
 */
export interface FuzzOptionsSchemaOut {
live_control: LiveControl
options: Options1
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
iteration: Iteration3
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
name: Name4
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
iterations: Iterations1
neuron_coverage: NeuronCoverage
never_activated_count: NeverActivatedCount
never_activated_sample: NeverActivatedSample
rng_seed: RngSeed1
seeds_explored: SeedsExplored
stop_reason?: StopReason
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
availability: Availability2
config: Config
control?: (FuzzControlStateOut | null)
counterexamples: Counterexamples1
frames?: Frames
options: (FuzzOptions | null)
provenance: Provenance
run_id: RunId6
saved?: Saved
seeds?: Seeds
status: Status3
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
instance: Instance
service: Service
status: Status4
version: Version
}
/**
 * HybridZ verdict-solver settings of a hybridz-domain verify_once run; its time limit is the run budget.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "HybridzOptions".
 */
export interface HybridzOptions {
tolerance?: Tolerance
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "InputSpecOut".
 */
export interface InputSpecOut {
center: Center
dataset: Dataset1
kind: Kind9
layer_id: LayerId4
lb: Lb1
shape: Shape
ub: Ub1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerOut".
 */
export interface LayerOut {
in_vars: InVars
kind: Kind10
layer_id: LayerId5
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
name: Name5
shape: Shape1
value: Value1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStateOut".
 */
export interface LayerStateOut {
before_layer_ids: BeforeLayerIds
kind: Kind11
layer_id: LayerId6
lb: Lb2
shape: Shape2
stage: Stage
ub: Ub2
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStatesOut".
 */
export interface LayerStatesOut {
availability: Availability3
layers: Layers1
method: Method
provenance: Provenance1
run_id: RunId7
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
kind: Kind12
onnx: Onnx1
vnnlib: Vnnlib
vnnlibs?: Vnnlibs
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LoadTorchRequest".
 */
export interface LoadTorchRequest {
eps: Eps
index: Index1
indices?: Indices
kind: Kind13
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
layers: Layers2
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
kind: Kind14
layer_id: LayerId7
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
built_with?: (BuiltWithOut | null)
description: Description3
engine_check?: EngineCheck
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
nodes: Nodes1
status: Status5
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
countries: Countries
online: Online
window_s: WindowS
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationIndexOut".
 */
export interface PropagationIndexOut {
availability: Availability4
complete: Complete1
domain: Domain
ignored_records: IgnoredRecords1
layers: Layers3
phases: Phases1
records: Records
run_id: RunId8
value_limit: ValueLimit
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationLayerSummaryOut".
 */
export interface PropagationLayerSummaryOut {
counts: Counts1
key: PropagationKeyOut
latest_record_id: LatestRecordId
layer_kind: LayerKind
output_shape: OutputShape1
record_count: RecordCount
}
export interface Counts1 {
[k: string]: number
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationKeyOut".
 */
export interface PropagationKeyOut {
domain: Domain1
layer_id: LayerId8
origin: Origin
parent: Parent
pass_: Pass
scope: Scope
stage: Stage1
version: Version1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationRecordOut".
 */
export interface PropagationRecordOut {
counts: Counts2
key: (PropagationKeyOut | null)
kind: Kind15
layer_kind: LayerKind1
metadata: Metadata
output_shape: OutputShape2
record_id: RecordId
shape: Shape3
t_ms: TMs2
tensors: Tensors
}
export interface Counts2 {
[k: string]: number
}
export interface Metadata {
[k: string]: string | number | boolean | null
}
export interface Tensors {
[k: string]: PropagationTensorOut
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationTensorOut".
 */
export interface PropagationTensorOut {
dtype: Dtype
sha256: Sha2562
shape: Shape4
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationLayerOut".
 */
export interface PropagationLayerOut {
availability: Availability5
domain: Domain2
layer_id: LayerId9
neuron?: Neuron3
output_shape: OutputShape3
records: Records1
run_id: RunId9
value_limit: ValueLimit1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "PropagationLayerRecordOut".
 */
export interface PropagationLayerRecordOut {
counts: Counts3
key: (PropagationKeyOut | null)
kind: Kind16
layer_kind: LayerKind2
metadata: Metadata1
output_shape: OutputShape4
record_id: RecordId1
shape: Shape5
t_ms: TMs3
tensors: Tensors1
values: Values
}
export interface Counts3 {
[k: string]: number
}
export interface Metadata1 {
[k: string]: string | number | boolean | null
}
export interface Tensors1 {
[k: string]: PropagationTensorOut
}
export interface Values {
[k: string]: (number | ("Infinity" | "-Infinity" | "NaN"))[]
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
availability: Availability6
kind: Kind17
name: Name6
note: Note
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RowVerdictOut".
 */
export interface RowVerdictOut {
act_status: ActStatus1
counterexample?: Counterexample
counterexample_output?: CounterexampleOutput
counterexample_output_error?: CounterexampleOutputError
row: Row1
verdict: Verdict
}
/**
 * What the worker captured while driving ACT; its presence means GET /api/runs/{id}/snapshot has diagnostics.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunDiagnosticsOut".
 */
export interface RunDiagnosticsOut {
errors: Errors
exception: Exception
location: Location
messages?: Messages
warnings: Warnings
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunEvent".
 */
export interface RunEvent {
at: At
kind: Kind18
payload: Payload
run_id: RunId10
seq: Seq2
status: Status6
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
bab?: Bab
client_request_id: ClientRequestId
counterexample_saved_at?: CounterexampleSavedAt
created_at: CreatedAt
diagnostics?: (RunDiagnosticsOut | null)
domain: Domain3
dual?: (DualOptions | null)
error: (ErrorBody | null)
finished_at: FinishedAt
hybridz?: (HybridzOptions | null)
last_seq: LastSeq
matches_native: MatchesNative
method: Method1
model_id: ModelId3
model_sha256: ModelSha256
native_reference: (NativeResult | null)
result: (RunResultOut | null)
run_id: RunId11
saved_counterexample_rows?: SavedCounterexampleRows
started_at: StartedAt
status: Status7
time_budget_s: TimeBudgetS
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunResultOut".
 */
export interface RunResultOut {
act_status: ActStatus2
bab_summary: BabSummary
counterexample: Counterexample1
counterexample_output?: CounterexampleOutput1
counterexample_output_error?: CounterexampleOutputError1
counterexample_row?: CounterexampleRow
device?: Device1
elapsed_s: ElapsedS5
metadata: Metadata2
rows?: Rows1
verdict: Verdict1
}
export interface Metadata2 {
[k: string]: string | number | boolean | null
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunRequest".
 */
export interface RunRequest {
bab?: Bab1
client_request_id?: ClientRequestId1
domain?: Domain4
dual?: (DualOptions | null)
fuzz?: (FuzzOptions | null)
hybridz?: (HybridzOptions | null)
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
shape: Shape6
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
version: Version2
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
/**
 * GET /api/verification/defaults: the settings a verify_once run uses when the request leaves them out.
 * 
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "VerifyDefaults".
 */
export interface VerifyDefaults {
dual: DualOptions
hybridz: HybridzOptions
}
