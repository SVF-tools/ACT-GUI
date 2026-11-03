/* Generated from visual_bench/schemas.py by scripts/gen_types.mjs. Do not edit. */

export type Evidence = string[]
export type Kind = ("observation" | "interpretation" | "hypothesis" | "missing")
export type Text = string
export type Availability = ("available" | "pending" | "not_recorded" | "unsupported")
export type Name = string
export type Source = string
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
export type Service = string
export type Status = "ok"
export type Version = string
export type Kind2 = string
export type LayerId2 = number
export type Lb = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Ub = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type InVars = number
export type Kind3 = string
export type LayerId3 = number
export type OutVars = number
export type OutputShape = (number[] | null)
export type Name1 = string
export type Shape = (number[] | null)
export type Value1 = (string | null)
export type Params = ParamOut[]
export type Preds = number[]
export type Succs = number[]
export type BeforeLayerIds = number[]
export type Kind4 = string
export type LayerId4 = number
export type Lb1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Shape1 = number[]
export type Stage = "after"
export type Ub1 = (number | ("Infinity" | "-Infinity" | "NaN"))[]
export type Availability1 = ("available" | "pending" | "not_recorded" | "unsupported")
export type Layers = LayerStateOut[]
export type Method = ("interval" | null)
export type RunId3 = string
export type ActCommit = (string | null)
export type InputDim = number
export type InputSpecs = InputSpecOut[]
export type Layers1 = LayerOut[]
export type ModelId1 = string
export type OutputDim = number
export type Kind5 = string
export type LayerId5 = number
export type Matrix = (number[][] | null)
export type Rows = number
export type Text1 = string
export type Thresholds = ((number | ("Infinity" | "-Infinity" | "NaN"))[] | null)
export type Sha256 = string
export type ActPath = string
export type Description = string
export type Methods = ("interval" | "bab")[]
export type ModelId2 = string
export type ElapsedS = number
export type Nodes = (number | null)
export type Status1 = string
export type Sha2561 = string
export type Availability2 = ("available" | "not_configured")
export type Kind6 = ("fake" | "real")
export type Name2 = string
export type Note = string
export type Providers = ProviderOut[]
export type At = string
export type Kind7 = ("run.queued" | "run.started" | "run.completed" | "run.failed" | "bab.summary")
export type RunId4 = string
export type Seq = number
export type Status2 = ("queued" | "running" | "completed" | "failed")
export type ActCommit1 = (string | null)
export type ClientRequestId = (string | null)
export type CreatedAt = string
export type FinishedAt = (string | null)
export type LastSeq = number
export type MatchesNative = (boolean | null)
export type Method1 = ("interval" | "bab")
export type ModelId3 = string
export type ModelSha256 = string
export type ActStatus = string
export type BabSummary = ({
[k: string]: string | number | boolean | null
} | null)
export type Counterexample = (number[] | null)
export type Device = (string | null)
export type ElapsedS1 = number
export type Verdict = ("certified" | "falsified" | "unknown" | "timeout" | "error")
export type RunId5 = string
export type StartedAt = (string | null)
export type Status3 = ("queued" | "running" | "completed" | "failed")
export type TimeBudgetS = number
export type Runs = RunOut[]
export type ClientRequestId1 = (string | null)
export type Method2 = ("interval" | "bab")
export type ModelId4 = string
export type TimeBudgetS1 = number
export type Content = string
export type LicenseFingerprint = (string | null)
export type LicenseSource = ("uploaded" | "environment" | "none")
export type LicenseState = ("licensed" | "restricted" | "invalid" | "not_installed")
export type LicenseUpdatedAt = (string | null)
export type Message2 = string
export type Solver = "gurobi"
export type UsedByMethods = ("interval" | "bab")[]
export type Version1 = (string | null)

export interface ActGuiWire {
AnswerSection?: AnswerSection
CapabilityOut?: CapabilityOut
CoverageOut?: CoverageOut
DiagnosticOut?: DiagnosticOut
EngineInfoOut?: EngineInfoOut
ErrorBody?: ErrorBody
ErrorResponse?: ErrorResponse
EvidenceRef?: EvidenceRef
ExplainRequest?: ExplainRequest
ExplainResponse?: ExplainResponse
HealthOut?: HealthOut
InputSpecOut?: InputSpecOut
LayerOut?: LayerOut
LayerStateOut?: LayerStateOut
LayerStatesOut?: LayerStatesOut
ModelDescriptionOut?: ModelDescriptionOut
ModelSummary?: ModelSummary
NativeResult?: NativeResult
OutputSpecOut?: OutputSpecOut
ParamOut?: ParamOut
ProviderList?: ProviderList
ProviderOut?: ProviderOut
RunEvent?: RunEvent
RunList?: RunList
RunOut?: RunOut
RunRequest?: RunRequest
RunResultOut?: RunResultOut
SelectionContext?: SelectionContext
SolverLicenseUpload?: SolverLicenseUpload
SolverStatusOut?: SolverStatusOut
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
 * via the `definition` "HealthOut".
 */
export interface HealthOut {
service: Service
status: Status
version: Version
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "InputSpecOut".
 */
export interface InputSpecOut {
kind: Kind2
layer_id: LayerId2
lb: Lb
ub: Ub
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerOut".
 */
export interface LayerOut {
in_vars: InVars
kind: Kind3
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
name: Name1
shape: Shape
value: Value1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStateOut".
 */
export interface LayerStateOut {
before_layer_ids: BeforeLayerIds
kind: Kind4
layer_id: LayerId4
lb: Lb1
shape: Shape1
stage: Stage
ub: Ub1
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "LayerStatesOut".
 */
export interface LayerStatesOut {
availability: Availability1
layers: Layers
method: Method
provenance: Provenance
run_id: RunId3
}
export interface Provenance {
[k: string]: string
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
kind: Kind5
layer_id: LayerId5
matrix: Matrix
rows: Rows
text: Text1
thresholds: Thresholds
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "ModelSummary".
 */
export interface ModelSummary {
act_path: ActPath
description: Description
methods: Methods
model_id: ModelId2
native: Native
sha256: Sha2561
}
export interface Native {
[k: string]: NativeResult
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "NativeResult".
 */
export interface NativeResult {
elapsed_s: ElapsedS
nodes: Nodes
status: Status1
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
availability: Availability2
kind: Kind6
name: Name2
note: Note
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunEvent".
 */
export interface RunEvent {
at: At
kind: Kind7
payload: Payload
run_id: RunId4
seq: Seq
status: Status2
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
error: (ErrorBody | null)
finished_at: FinishedAt
last_seq: LastSeq
matches_native: MatchesNative
method: Method1
model_id: ModelId3
model_sha256: ModelSha256
native_reference: (NativeResult | null)
result: (RunResultOut | null)
run_id: RunId5
started_at: StartedAt
status: Status3
time_budget_s: TimeBudgetS
}
/**
 * This interface was referenced by `ActGuiWire`'s JSON-Schema
 * via the `definition` "RunResultOut".
 */
export interface RunResultOut {
act_status: ActStatus
bab_summary: BabSummary
counterexample: Counterexample
device?: Device
elapsed_s: ElapsedS1
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
method: Method2
model_id: ModelId4
time_budget_s?: TimeBudgetS1
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
